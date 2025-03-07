import torch
from grid_gpu import GridGPU
from random_piece_generator_gpu import random_piece_generator_gpu_batch
from piece_gpu import PieceGPUBatch

class TetrisEnvGPU_Batch:
    def __init__(self, batch_size, rows=20, cols=10, device=None):
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        self.batch_size = batch_size
        self.rows = rows
        self.cols = cols
        # Khởi tạo board dưới dạng batch
        self.grid = GridGPU(batch_size, rows, cols, device=device)
        # Sinh batch current_piece và next_piece
        self.current_piece = random_piece_generator_gpu_batch(batch_size, device=device)
        self.next_piece = random_piece_generator_gpu_batch(batch_size, device=device)
        # Điểm số cho từng game: tensor shape (batch_size,)
        self.score = torch.zeros(batch_size, device=device, dtype=torch.int32)
        # Trạng thái game_over: tensor boolean shape (batch_size,)
        self.game_over = torch.zeros(batch_size, dtype=torch.bool, device=device)

    def new_piece(self):
        """
        Với các game active (chưa game_over), chuyển next_piece thành current_piece,
        đặt lại vị trí và sinh ra next_piece mới.
        Nếu vị trí mới không hợp lệ, đánh dấu game_over cho game đó.
        """
        active_mask = ~self.game_over  # tensor boolean shape (batch_size,)
        if active_mask.sum() == 0:
            return
        # Cập nhật current_piece của các game active bằng next_piece hiện tại (sử dụng clone từng phần)
        self.current_piece.update_indices(active_mask, self.next_piece.get_batch(active_mask))
        # Đặt lại vị trí khởi đầu cho các game active
        self.current_piece.x[active_mask] = 3
        self.current_piece.y[active_mask] = 0
        # Sinh next_piece mới cho các game active
        new_next = random_piece_generator_gpu_batch(int(active_mask.sum().item()), device=self.device)
        self.next_piece.update_indices(active_mask, new_next)
        # Kiểm tra tính hợp lệ của current_piece cho các game active
        valid = self.grid.is_valid_position_batch(self.current_piece)
        self.game_over[active_mask] |= ~valid[active_mask]

    def move_piece(self, dx, dy):
        """
        Di chuyển current_piece theo (dx, dy) cho toàn bộ batch (chỉ cập nhật cho game active).
        Nếu di chuyển không hợp lệ với game nào đó, revert lại di chuyển cho game đó.
        Trả về tensor boolean với shape (batch_size,) cho biết game nào di chuyển thành công.
        """
        active_mask = ~self.game_over
        self.current_piece.move_batch(dx, dy, mask=active_mask)
        valid = self.grid.is_valid_position_batch(self.current_piece)
        # Các game không hợp lệ: revert di chuyển
        revert_mask = active_mask & (~valid)
        if revert_mask.any():
            self.current_piece.move_batch(-dx, -dy, mask=revert_mask)
        return valid

    def rotate_piece(self, clockwise=True):
        """
        Xoay current_piece cho toàn bộ batch (chỉ game active).
        Nếu xoay gây ra vị trí không hợp lệ, revert lại.
        Trả về tensor boolean cho biết game nào xoay thành công.
        """
        active_mask = ~self.game_over
        if clockwise:
            self.current_piece.rotate_batch(mask=active_mask)
        else:
            self.current_piece.rotate_counterclockwise_batch(mask=active_mask)
        valid = self.grid.is_valid_position_batch(self.current_piece)
        revert_mask = active_mask & (~valid)
        if revert_mask.any():
            if clockwise:
                self.current_piece.rotate_counterclockwise_batch(mask=revert_mask)
            else:
                self.current_piece.rotate_batch(mask=revert_mask)
        return valid

    def drop_piece(self):
        """
        Với các game active, nếu current_piece không thể di chuyển xuống thêm 1 ô,
        đặt piece lên board, xóa các hàng đầy và cập nhật điểm, sau đó gọi new_piece.
        """
        active_mask = ~self.game_over
        valid = self.move_piece(0, 1)
        not_moved = active_mask & (~valid)
        if not_moved.any():
            self.grid.place_piece_batch(self.current_piece, mask=not_moved)
            lines_cleared = self.grid.clear_lines_batch(mask=not_moved)  # tensor (batch_size,)
            self.score[not_moved] += lines_cleared[not_moved]
            self.new_piece()

    def hard_drop(self):
        """
        Di chuyển current_piece xuống dưới cho đến khi không thể di chuyển (cho game active).
        Sau đó gọi drop_piece để cập nhật board và điểm.
        """
        active_mask = ~self.game_over
        valid = self.move_piece(0, 1)
        while valid[active_mask].any():
            valid = self.move_piece(0, 1)
        self.drop_piece()

    def update(self):
        """
        Hàm update chính: Với các game active, gọi drop_piece.
        """
        if (~self.game_over).any():
            self.drop_piece()

    def get_state(self):
        """
        Trả về trạng thái hiện tại của batch game dưới dạng dict:
          - "grid": board (tensor, shape (batch_size, rows, cols))
          - "current_piece_cells": danh sách các tensor chứa tọa độ của current_piece cho mỗi game
          - "score": tensor điểm số (batch_size,)
          - "game_over": tensor boolean (batch_size,)
        """
        return {
            "grid": self.grid.board,
            "current_piece_cells": self.current_piece.get_cells_batch(),
            "score": self.score,
            "game_over": self.game_over
        }

    # ---------------------
    # Các hàm hỗ trợ cho Agent
    # ---------------------

    def get_possible_moves(self):
        """
        Trả về danh sách các nước đi khả dĩ cho current_piece cho từng game trong batch.
        Trả về một list với độ dài = batch_size, mỗi phần tử là:
            - None nếu game đã kết thúc,
            - Hoặc list các dict, mỗi dict có khóa "rotations" và "x".
        Cách làm: Với từng game, clone current_piece, thử từ 0 đến 3 lần xoay,
        tính offset dựa trên matrix (chuyển về numpy để tính đơn giản) và kiểm tra tính hợp lệ.
        """
        moves_batch = []
        for i in range(self.batch_size):
            if self.game_over[i]:
                moves_batch.append(None)
                continue
            moves = []
            original_piece = self.current_piece.get_item(i).clone()
            for rotations in range(4):
                piece_copy = original_piece.clone()
                for _ in range(rotations):
                    piece_copy.rotate()
                # Tính offset dựa trên matrix: chuyển matrix về numpy để dễ tính toán
                matrix_np = piece_copy.matrix.cpu().numpy()
                rel_cells = [(j, i_row) for i_row, row in enumerate(matrix_np) for j, val in enumerate(row) if val]
                if not rel_cells:
                    continue
                min_offset = min(j for j, _ in rel_cells)
                max_offset = max(j for j, _ in rel_cells)
                min_x = -min_offset
                max_x = self.cols - max_offset - 1
                for x in range(min_x, max_x + 1):
                    test_piece = piece_copy.clone()
                    test_piece.x = torch.tensor(x, device=self.device)
                    # Sử dụng phương thức is_valid_position_item để kiểm tra game thứ i
                    if self.grid.is_valid_position_item(test_piece, i):
                        moves.append({"rotations": rotations, "x": x})
            moves_batch.append(moves)
        return moves_batch

    def simulate_move(self, move, game_index):
        """
        Giả lập thực hiện nước đi cho game thứ game_index.
        move: dict có khóa "rotations" và "x" cho game đó.
        Trả về clone của môi trường sau khi thực hiện nước đi và hard drop,
        hoặc None nếu nước đi không hợp lệ.
        """
        simulated_game = self.clone_item(game_index)
        for _ in range(move["rotations"]):
            simulated_game.current_piece.rotate()
        simulated_game.current_piece.x = torch.tensor(move["x"], device=self.device)
        if not simulated_game.grid.is_valid_position_item(simulated_game.current_piece, 0):
            return None
        simulated_game.hard_drop()
        return simulated_game

    def clone(self):
        """
        Clone toàn bộ môi trường batch.
        Yêu cầu các thành phần con (grid, current_piece, next_piece) có phương thức clone_batch.
        """
        cloned_env = TetrisEnvGPU_Batch(self.batch_size, self.rows, self.cols, device=self.device)
        cloned_env.grid = self.grid.clone_batch()
        cloned_env.current_piece = self.current_piece.clone_batch()
        cloned_env.next_piece = self.next_piece.clone_batch()
        cloned_env.score = self.score.clone()
        cloned_env.game_over = self.game_over.clone()
        return cloned_env

    def clone_item(self, index):
        """
        Clone môi trường của game thứ index (batch_size = 1).
        Yêu cầu các thành phần con có phương thức clone_item hoặc get_item.
        """
        cloned_env = TetrisEnvGPU_Batch(1, self.rows, self.cols, device=self.device)
        cloned_env.grid = self.grid.clone_item(index)
        cloned_env.current_piece = self.current_piece.get_item(index).clone()
        cloned_env.next_piece = self.next_piece.get_item(index).clone()
        cloned_env.score = self.score[index].clone().unsqueeze(0)
        cloned_env.game_over = self.game_over[index].clone().unsqueeze(0)
        return cloned_env


# Example usage:
if __name__ == "__main__":
    import time
    batch_size = 16
    env = TetrisEnvGPU_Batch(batch_size=batch_size)
    print("Starting batch game on device:", env.device)
    steps = 0
    while ((~env.game_over).any()) and (steps < 50):
        env.update()
        # In trạng thái board của game đầu tiên trong batch (chuyển về CPU để in)
        print("Board of game 0:")
        env.grid.print_board(idx=0)
        print("Scores:", env.score.cpu().numpy())
        print("------")
        time.sleep(0.5)
        steps += 1
    print("Batch simulation completed!")
