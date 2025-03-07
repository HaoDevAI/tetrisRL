import copy
from src.environments.grid import Grid
from src.environments.random_piece_generator import random_piece_generator

class TetrisEnv:
    def __init__(self, rows=20, cols=10):
        self.grid = Grid(rows, cols)
        self.current_piece = random_piece_generator()
        self.next_piece = random_piece_generator()
        self.score = 0
        self.game_over = False

    def new_piece(self):
        """Set the current piece to the next one, and generate a new next piece.
           Check if the new piece's starting position is valid; if not, end the game.
        """
        self.current_piece = self.next_piece
        self.current_piece.x = 3  # Reset starting position
        self.current_piece.y = 0
        self.next_piece = random_piece_generator()

        if not self.grid.is_valid_position(self.current_piece):
            self.game_over = True

    def move_piece(self, dx, dy):
        """Attempt to move the current piece by dx, dy.
           Revert if the new position is invalid.
        """
        self.current_piece.move(dx, dy)
        if not self.grid.is_valid_position(self.current_piece):
            self.current_piece.move(-dx, -dy)
            return False
        return True

    def rotate_piece(self, clockwise=True):
        """Rotate the current piece.
           Revert the rotation if the new orientation is invalid.
        """
        if clockwise:
            self.current_piece.rotate()
        else:
            self.current_piece.rotate_counterclockwise()

        if not self.grid.is_valid_position(self.current_piece):
            # Revert the rotation
            if clockwise:
                self.current_piece.rotate_counterclockwise()
            else:
                self.current_piece.rotate()
            return False
        return True

    def drop_piece(self):
        """
        Try to move the piece down by one. If it cannot move down,
        place the piece on the grid, clear full lines, update the score,
        and spawn a new piece.
        """
        if not self.move_piece(0, 1):
            self.grid.place_piece(self.current_piece)
            lines_cleared = self.grid.clear_lines()
            self.score += lines_cleared
            self.new_piece()

    def hard_drop(self):
        """
        Immediately drop the current piece to its lowest valid position.
        """
        while self.move_piece(0, 1):
            pass
        self.drop_piece()

    def update(self):
        """
        Main update method that should be called on each tick.
        This method is responsible for moving the piece down automatically.
        """
        if not self.game_over:
            self.drop_piece()

    def get_state(self):
        """Return a dictionary containing current game state for UI purposes."""
        return {
            "grid": self.grid.board,
            "current_piece_cells": self.current_piece.get_cells(),
            "score": self.score,
            "game_over": self.game_over
        }

    # ---------------------
    # Các hàm hỗ trợ cho Agent
    # ---------------------

    def get_possible_moves(self):
        """
        Trả về danh sách các nước đi khả dĩ cho mảnh hiện tại.
        Mỗi nước đi được mô tả bằng một dict với:
            - "rotations": số lần xoay (0, 1, 2, 3)
            - "x": vị trí x (cột) mà mảnh sẽ được đặt trước khi hard drop.
        Hàm này sẽ thực hiện mô phỏng trên bản sao để kiểm tra tính hợp lệ.
        """
        moves = []
        # Lưu lại trạng thái ban đầu của mảnh hiện tại
        original_piece = copy.deepcopy(self.current_piece)

        # Thử 0 đến 3 lần xoay
        for rotations in range(4):
            # Tạo bản sao của mảnh với số lần xoay tương ứng
            piece_copy = copy.deepcopy(original_piece)
            for _ in range(rotations):
                piece_copy.rotate()

            # Tính các offset tương đối dựa trên ma trận của piece
            rel_cells = [(j, i) for i, row in enumerate(piece_copy.matrix)
                         for j, val in enumerate(row) if val]
            min_offset = min(j for j, _ in rel_cells)
            max_offset = max(j for j, _ in rel_cells)

            # Xác định giới hạn x hợp lệ:
            # Để không vượt quá bên trái: x >= -min_offset
            # Và không vượt quá bên phải: x <= grid.cols - max_offset - 1
            min_x = -min_offset
            max_x = self.grid.cols - max_offset - 1

            # Debug in ra offset nếu cần:
            # print(f"Rotation {rotations}: min_offset={min_offset}, max_offset={max_offset}, min_x={min_x}, max_x={max_x}")

            for x in range(min_x, max_x + 1):
                test_piece = copy.deepcopy(piece_copy)
                test_piece.x = x
                if self.grid.is_valid_position(test_piece):
                    moves.append({"rotations": rotations, "x": x})
        return moves

    def simulate_move(self, move):
        """
        Giả lập việc thực hiện nước đi được chỉ định.
        move: dict có 2 khóa "rotations" và "x".
        Trả về một bản sao của TetrisEnv sau khi áp dụng nước đi và hard drop.
        """
        simulated_game = copy.deepcopy(self)

        # Áp dụng số lần xoay cho mảnh hiện tại.
        for _ in range(move["rotations"]):
            simulated_game.current_piece.rotate()

        # Di chuyển mảnh về vị trí x đã chỉ định.
        simulated_game.current_piece.x = move["x"]

        # Nếu vị trí hiện tại chưa hợp lệ (do xoay hay dịch chuyển), không mô phỏng được nước đi này.
        if not simulated_game.grid.is_valid_position(simulated_game.current_piece):
            return None

        # Thực hiện hard drop để cho mảnh đi xuống vị trí cuối cùng.
        simulated_game.hard_drop()

        return simulated_game
# Example usage:
if __name__ == "__main__":
    gm = TetrisEnv()
    print("Starting game...")
    while not gm.game_over:
        gm.update()
        # For demonstration, print the grid state and score.
        # In a full game, you would integrate with a Pygame loop.
        for row in gm.grid.board:
            print(" ".join(str(cell) for cell in row))
        print("Score:", gm.score)
        print("------")
        # Slow down loop for demo purposes
        import time
        time.sleep(0.5)
    print("Game Over!")