import torch

# Định nghĩa biến SHAPES (có thể import từ file shapes.py nếu cần)
SHAPES = {
    'I': [
        [
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ],
        [
            [0, 0, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 0]
        ]
    ],
    'O': [
        [
            [1, 1],
            [1, 1]
        ]
    ],
    'T': [
        [
            [0, 1, 0],
            [1, 1, 1],
            [0, 0, 0]
        ],
        [
            [0, 1, 0],
            [0, 1, 1],
            [0, 1, 0]
        ],
        [
            [0, 0, 0],
            [1, 1, 1],
            [0, 1, 0]
        ],
        [
            [0, 1, 0],
            [1, 1, 0],
            [0, 1, 0]
        ]
    ],
    'S': [
        [
            [0, 1, 1],
            [1, 1, 0],
            [0, 0, 0]
        ],
        [
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0]
        ]
    ],
    'Z': [
        [
            [1, 1, 0],
            [0, 1, 1],
            [0, 0, 0]
        ],
        [
            [0, 0, 1],
            [0, 1, 1],
            [0, 1, 0]
        ]
    ],
    'J': [
        [
            [1, 0, 0],
            [1, 1, 1],
            [0, 0, 0]
        ],
        [
            [0, 1, 1],
            [0, 1, 0],
            [0, 1, 0]
        ],
        [
            [0, 0, 0],
            [1, 1, 1],
            [0, 0, 1]
        ],
        [
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 0]
        ]
    ],
    'L': [
        [
            [0, 0, 1],
            [1, 1, 1],
            [0, 0, 0]
        ],
        [
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 1]
        ],
        [
            [0, 0, 0],
            [1, 1, 1],
            [1, 0, 0]
        ],
        [
            [1, 1, 0],
            [0, 1, 0],
            [0, 1, 0]
        ]
    ]
}

class PieceGPUBatch:
    def __init__(self, batch_size, shape, device='cuda'):
        if shape not in SHAPES:
            raise ValueError(f"Shape {shape} is not defined.")
        self.device = device
        self.batch_size = batch_size
        self.shape = shape
        # Chuyển các ma trận của từng rotation sang tensor
        self.rotations = [torch.tensor(r, dtype=torch.float32, device=device)
                          for r in SHAPES[shape]]
        # Mỗi phần tử trong batch bắt đầu ở rotation index 0
        self.rotation_index = torch.zeros(batch_size, dtype=torch.long, device=device)
        # Lấy rotation đầu tiên và nhân bản cho toàn batch: shape (batch_size, rows, cols)
        self.matrix = self.rotations[0].unsqueeze(0).repeat(batch_size, 1, 1)
        # Vị trí bắt đầu: x = 3, y = 0 cho toàn batch (tensor shape: (batch_size,))
        self.x = torch.full((batch_size,), 3, dtype=torch.long, device=device)
        self.y = torch.zeros(batch_size, dtype=torch.long, device=device)

    def rotate_batch(self, mask=None):
        """
        Xoay các piece trong batch theo chiều kim đồng hồ.
        Nếu mask được cung cấp (tensor boolean shape (batch_size,)), chỉ cập nhật các phần tử được chọn.
        """
        if mask is None:
            mask = torch.ones(self.batch_size, dtype=torch.bool, device=self.device)
        # Cập nhật rotation_index cho các phần tử trong mask
        self.rotation_index[mask] = (self.rotation_index[mask] + 1) % len(self.rotations)
        # Cập nhật matrix cho toàn batch (với vòng lặp cho từng phần tử)
        new_matrices = []
        for i in range(self.batch_size):
            new_matrices.append(self.rotations[self.rotation_index[i].item()])
        self.matrix = torch.stack(new_matrices, dim=0)

    def rotate_counterclockwise_batch(self, mask=None):
        """
        Xoay các piece trong batch ngược chiều kim đồng hồ.
        """
        if mask is None:
            mask = torch.ones(self.batch_size, dtype=torch.bool, device=self.device)
        self.rotation_index[mask] = (self.rotation_index[mask] - 1) % len(self.rotations)
        new_matrices = []
        for i in range(self.batch_size):
            new_matrices.append(self.rotations[self.rotation_index[i].item()])
        self.matrix = torch.stack(new_matrices, dim=0)

    def move_batch(self, dx, dy, mask=None):
        """
        Di chuyển các piece trong batch theo (dx, dy) cho các phần tử được chọn bởi mask.
        """
        if mask is None:
            mask = torch.ones(self.batch_size, dtype=torch.bool, device=self.device)
        self.x[mask] = self.x[mask] + dx
        self.y[mask] = self.y[mask] + dy

    def get_cells_batch(self):
        """
        Trả về danh sách các tensor, mỗi tensor chứa tọa độ của các cell (x, y) của từng piece trong batch.
        Mỗi tensor có shape (num_cells, 2).
        """
        batch_cells = []
        for i in range(self.batch_size):
            # Lấy các chỉ số (nonzero) của self.matrix[i]
            indices = torch.nonzero(self.matrix[i], as_tuple=False)
            xs = indices[:, 1] + self.x[i]
            ys = indices[:, 0] + self.y[i]
            cells = torch.stack([xs, ys], dim=1)
            batch_cells.append(cells)
        return batch_cells

    def clone_batch(self):
        """
        Trả về clone của đối tượng PieceGPUBatch (cho toàn batch).
        """
        cloned = PieceGPUBatch(self.batch_size, self.shape, self.device)
        cloned.rotation_index = self.rotation_index.clone()
        cloned.matrix = self.matrix.clone()
        cloned.x = self.x.clone()
        cloned.y = self.y.clone()
        return cloned

    def get_item(self, index):
        """
        Trả về một instance của PieceGPUBatch với batch_size = 1 tương ứng với phần tử thứ index trong batch.
        """
        new_piece = PieceGPUBatch(1, self.shape, self.device)
        new_piece.rotation_index = self.rotation_index[index].unsqueeze(0).clone()
        new_piece.matrix = self.matrix[index].unsqueeze(0).clone()
        new_piece.x = self.x[index].unsqueeze(0).clone()
        new_piece.y = self.y[index].unsqueeze(0).clone()
        return new_piece


# Test
if __name__ == "__main__":
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    batch_size = 4
    piece_batch = PieceGPUBatch(batch_size, 'T', device=device)
    # In tọa độ các cell cho toàn batch
    cells = piece_batch.get_cells_batch()
    for i, cell in enumerate(cells):
        print(f"Game {i} initial cells: {cell.cpu().numpy()}")
    # Thực hiện xoay cho toàn batch
    piece_batch.rotate_batch()
    cells = piece_batch.get_cells_batch()
    for i, cell in enumerate(cells):
        print(f"Game {i} after rotation: {cell.cpu().numpy()}")
    # Di chuyển batch
    piece_batch.move_batch(1, 2)
    cells = piece_batch.get_cells_batch()
    for i, cell in enumerate(cells):
        print(f"Game {i} after moving (1,2): {cell.cpu().numpy()}")
