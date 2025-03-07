import torch

class GridGPU:
    def __init__(self, batch_size, rows=20, cols=10, device='cuda'):
        """
        Khởi tạo board cho toàn bộ batch.
        - board: tensor shape (batch_size, rows, cols), giá trị 0 biểu thị ô trống,
          1 biểu thị ô đã được lấp.
        """
        self.batch_size = batch_size
        self.rows = rows
        self.cols = cols
        self.device = device
        self.board = torch.zeros((batch_size, rows, cols), dtype=torch.int32, device=device)

    def is_valid_position_batch(self, piece_batch):
        """
        Kiểm tra cho mỗi game trong batch xem các cell của piece có hợp lệ hay không.
        - piece_batch: đối tượng có phương thức get_cells_batch() trả về list gồm tensor với shape (num_cells, 2)
        Trả về tensor boolean với shape (batch_size,).
        """
        valid = torch.ones(self.batch_size, dtype=torch.bool, device=self.device)
        cells_list = piece_batch.get_cells_batch()  # List gồm batch_size tensor
        for i, cells in enumerate(cells_list):
            if cells.numel() == 0:
                valid[i] = False
                continue
            xs = cells[:, 0]
            ys = cells[:, 1]
            # Kiểm tra giới hạn: 0 <= x < cols, 0 <= y < rows
            in_bounds = (xs >= 0) & (xs < self.cols) & (ys >= 0) & (ys < self.rows)
            if not in_bounds.all():
                valid[i] = False
                continue
            # Kiểm tra va chạm: giá trị tại board[i, ys, xs] phải bằng 0
            board_vals = self.board[i, ys.long(), xs.long()]
            if (board_vals != 0).any():
                valid[i] = False
        return valid

    def place_piece_batch(self, piece_batch, mask=None):
        """
        Đặt piece lên board cho các game được chọn bởi mask.
        - piece_batch: đối tượng có phương thức get_cells_batch(), trả về list của tensor các tọa độ.
        - mask: tensor boolean shape (batch_size,). Nếu không cung cấp, cập nhật cho toàn batch.
        """
        if mask is None:
            mask = torch.ones(self.batch_size, dtype=torch.bool, device=self.device)
        cells_list = piece_batch.get_cells_batch()
        for i in range(self.batch_size):
            if mask[i]:
                cells = cells_list[i]
                xs = cells[:, 0].long()
                ys = cells[:, 1].long()
                self.board[i, ys, xs] = 1

    def clear_lines_batch(self, mask=None):
        """
        Xóa các hàng đầy cho các game được chỉ định bởi mask.
        Trả về tensor số dòng đã xóa cho từng game (shape: (batch_size,)).
        """
        lines_cleared = torch.zeros(self.batch_size, dtype=torch.int32, device=self.device)
        if mask is None:
            mask = torch.ones(self.batch_size, dtype=torch.bool, device=self.device)
        for i in range(self.batch_size):
            if mask[i]:
                board = self.board[i]
                full_rows = (board != 0).all(dim=1)  # full_rows: tensor boolean shape (rows,)
                num_full = int(full_rows.sum().item())
                lines_cleared[i] = num_full
                # Giữ lại những hàng không đầy
                new_rows = board[~full_rows]
                # Tạo các hàng trống để thêm vào trên cùng
                empty_rows = torch.zeros((num_full, self.cols), dtype=board.dtype, device=self.device)
                new_board = torch.cat((empty_rows, new_rows), dim=0)
                # Nếu cần pad thêm để đạt đủ số hàng
                if new_board.shape[0] < self.rows:
                    pad_rows = self.rows - new_board.shape[0]
                    pad = torch.zeros((pad_rows, self.cols), dtype=board.dtype, device=self.device)
                    new_board = torch.cat((pad, new_board), dim=0)
                self.board[i] = new_board
        return lines_cleared

    def clone_batch(self):
        """
        Trả về clone của toàn bộ đối tượng GridGPU.
        """
        cloned = GridGPU(self.batch_size, self.rows, self.cols, device=self.device)
        cloned.board = self.board.clone()
        return cloned

    def clone_item(self, index):
        """
        Trả về clone của board cho game thứ index (batch_size = 1).
        """
        cloned = GridGPU(1, self.rows, self.cols, device=self.device)
        cloned.board = self.board[index].unsqueeze(0).clone()
        return cloned

    def print_board(self, idx=0):
        """
        In board của game thứ idx (chuyển về CPU để in).
        """
        board_cpu = self.board[idx].cpu().numpy()
        for row in board_cpu:
            print(" ".join(str(int(cell)) for cell in row))

    def is_valid_position_item(self, piece, index):
        # Giả sử piece là instance của PieceGPUBatch với batch_size = 1
        valid = self.is_valid_position_batch(piece)
        return valid[0]


# Example usage:
if __name__ == "__main__":
    batch_size = 1
    grid = GridGPU(batch_size, rows=20, cols=10, device='cuda')
    # Giả sử bạn có đối tượng piece từ PieceGPUBatch (chạy thử với batch_size = 1)
    from piece import PieceGPUBatch
    piece_batch = PieceGPUBatch(batch_size, 'T', device='cuda')
    if grid.is_valid_position_batch(piece_batch).all():
        grid.place_piece_batch(piece_batch)
    grid.print_board(idx=0)
    cleared = grid.clear_lines_batch(torch.tensor([True], device='cuda'))
    print("Lines cleared:", cleared.cpu().numpy())
