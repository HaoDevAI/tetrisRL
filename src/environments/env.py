from src.environments.grid import Grid
from src.environments.random_piece_generator import *

class TetrisEnv:
    def __init__(self, rows=20, cols=10,generator="random",seed= None):
        self.rows = rows
        self.cols = cols
        self.generator = generator
        self.seed = seed
        self.grid = Grid(rows, cols)
        if self.generator == "random":
            self.current_piece = random_piece_generator(seed=self.seed)
            self.next_piece = random_piece_generator()
        elif self.generator == "classic":
            self.seven_bag_gen = seven_bag_random_generator(seed=self.seed)
            self.current_piece = next(self.seven_bag_gen)
            self.next_piece = next(self.seven_bag_gen)
        self.score = 0
        self.moves_played = 0
        self.game_over = False

    def reset(self):
        """
        Reset trạng thái game.
        """
        self.grid = Grid(self.rows, self.cols)
        self.score = 0
        self.moves_played = 0
        self.game_over = False

        # Sau khi reset, không truyền seed để giữ trạng thái random đã tiến triển.
        if self.generator == "random":
            self.current_piece = random_piece_generator()
            self.next_piece = random_piece_generator()
        elif self.generator == "classic":
            self.seven_bag_gen = seven_bag_random_generator()
            self.current_piece = next(self.seven_bag_gen)
            self.next_piece = next(self.seven_bag_gen)

    def clone(self):
        """
        Trả về một bản sao của TetrisEnv bằng cách sử dụng hàm clone của các thành phần.
        Lưu ý: Chúng ta giả định rằng Grid và Piece đã có hàm clone riêng.
        """
        new_env = TetrisEnv.__new__(TetrisEnv)
        new_env.generator = self.generator
        new_env.seed = self.seed
        new_env.grid = self.grid.clone()
        new_env.current_piece = self.current_piece.clone()
        new_env.next_piece = self.next_piece.clone()
        new_env.score = self.score
        new_env.game_over = self.game_over
        if self.generator == "classic":
            new_env.seven_bag_gen = self.seven_bag_gen
        return new_env

    def new_piece(self):
        """Set the current piece to the next one, and generate a new next piece.
           Check if the new piece's starting position is valid; if not, end the game.
        """
        self.current_piece = self.next_piece

        # Căn giữa: vị trí x = ((số cột lưới - độ rộng piece) / 2) điều chỉnh lại theo min_offset
        self.current_piece.x = (self.grid.cols - self.current_piece.piece_width) // 2
        self.current_piece.y = 0
        if self.generator == "random":
            self.next_piece = random_piece_generator()
        elif self.generator == "classic":
            self.next_piece = next(self.seven_bag_gen)

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

    def get_ghost_piece(self):
        """
        Tạo một bản sao của khối hiện tại và di chuyển nó xuống cho đến khi không hợp lệ,
        sau đó lùi lại 1 bước để xác định vị trí mà khối sẽ rơi nếu hard drop.
        """
        ghost = self.current_piece.clone()
        while self.grid.is_valid_position(ghost):
            ghost.y += 1
        ghost.y -= 1  # Lùi lại 1 bước vì bước cuối cùng không hợp lệ
        return ghost

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
        original_piece = self.current_piece.clone()

        # Thử 0 đến 3 lần xoay
        for rotations in range(4):
            # Tạo bản sao của mảnh với số lần xoay tương ứng
            piece_copy = original_piece.clone()
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
                test_piece = piece_copy.clone()
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
        simulated_game = self.clone()

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