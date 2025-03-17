from src.environments.grid import Grid
from src.environments.random_piece_generator import *

class TetrisEnv:
    """
    Class representing the Tetris game environment.
    """
    def __init__(self, rows=20, cols=10, generator="random", seed=None):
        """
        Initialize the Tetris environment.

        Args:
            rows (int): Number of rows in the grid.
            cols (int): Number of columns in the grid.
            generator (str): Type of piece generator to use ("random" or "classic").
            seed (optional): Seed for random number generation.
        """
        self.rows = rows
        self.cols = cols
        self.generator = generator
        self.seed = seed
        self.grid = Grid(rows, cols)
        if self.generator == "random":
            self.current_piece = random_piece_generator(seed=self.seed)
            self.next_piece = random_piece_generator()
        elif self.generator == "classic":
            # Tạo túi đầu tiên
            self.current_bag = generate_7_bag(seed=self.seed)
            # Lấy 2 viên đầu tiên từ túi
            self.current_piece = Piece(self.current_bag.pop())
            if not self.current_bag:  # Nếu túi rỗng, tạo lại
                self.current_bag = generate_7_bag()
            self.next_piece = Piece(self.current_bag.pop())
        self.score = 0
        self.moves_played = 0
        self.game_over = False

    def reset(self):
        """
        Reset the game state to its initial configuration.
        """
        self.grid = Grid(self.rows, self.cols)
        self.score = 0
        self.moves_played = 0
        self.game_over = False

        if self.generator == "random":
            self.current_piece = random_piece_generator()
            self.next_piece = random_piece_generator()
        elif self.generator == "classic":
            # Khởi tạo lại túi 7-bag mới cho ván đấu mới.
            self.current_bag = generate_7_bag(seed=self.seed)
            self.current_piece = Piece(self.current_bag.pop())
            if not self.current_bag:  # Dự phòng, nếu túi rỗng thì tạo lại
                self.current_bag = generate_7_bag()
            self.next_piece = Piece(self.current_bag.pop())

    def clone(self):
        """
        Return a clone of the Tetris environment by cloning its components.
        Note: Assumes Grid and Piece have their own clone methods.

        Returns:
            TetrisEnv: A new instance of the environment with the same state.
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
            # Sao chép trạng thái của túi hiện tại để clone không làm thay đổi túi của game gốc
            new_env.current_bag = self.current_bag.copy() if hasattr(self, 'current_bag') else []
        return new_env

    def new_piece(self):
        self.current_piece = self.next_piece
        self.current_piece.x = (self.grid.cols - self.current_piece.piece_width) // 2
        # Sử dụng bag đã lưu để lấy viên tiếp theo
        if self.generator == "random":
            self.next_piece = random_piece_generator()
        elif self.generator == "classic":
            if not self.current_bag:  # Nếu túi rỗng, tạo một túi mới (không cần seed nữa)
                self.current_bag = generate_7_bag()
            self.next_piece = Piece(self.current_bag.pop())
        if not self.grid.is_valid_position(self.current_piece):
            self.game_over = True

    def move_piece(self, dx, dy):
        """
        Attempt to move the current piece by (dx, dy).
        Revert the move if the new position is invalid.

        Args:
            dx (int): Horizontal displacement.
            dy (int): Vertical displacement.

        Returns:
            bool: True if the move was successful, False otherwise.
        """
        self.current_piece.move(dx, dy)
        if not self.grid.is_valid_position(self.current_piece):
            self.current_piece.move(-dx, -dy)
            return False
        return True

    def rotate_piece(self, clockwise=True):
        """
        Rotate the current piece. Revert the rotation if the new orientation is invalid.

        Args:
            clockwise (bool): If True, rotate clockwise; otherwise, rotate counterclockwise.

        Returns:
            bool: True if the rotation was successful, False otherwise.
        """
        if clockwise:
            self.current_piece.rotate()
        else:
            self.current_piece.rotate_counterclockwise()

        if not self.grid.is_valid_position(self.current_piece):
            if clockwise:
                self.current_piece.rotate_counterclockwise()
            else:
                self.current_piece.rotate()
            return False
        return True

    def drop_piece(self):
        """
        Attempt to move the piece down by one. If it cannot move down,
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
        Create a ghost piece by cloning the current piece and moving it downward
        until an invalid position is reached, then move it one step up to determine
        its landing position if hard dropped.

        Returns:
            Piece: The ghost piece.
        """
        ghost = self.current_piece.clone()
        while self.grid.is_valid_position(ghost):
            ghost.y += 1
        ghost.y -= 1
        return ghost

    def update(self):
        """
        Update the game state for one tick by moving the current piece down automatically.
        """
        if not self.game_over:
            self.drop_piece()

    def get_state(self):
        """
        Return the current game state for UI purposes.

        Returns:
            dict: A dictionary containing the grid, current piece cells, score, and game over status.
        """
        return {
            "grid": self.grid.board,
            "current_piece_cells": self.current_piece.get_cells(),
            "score": self.score,
            "game_over": self.game_over
        }

    def get_possible_moves(self):
        """
        Return a list of possible moves for the current piece.
        Each move is represented as a dictionary with keys:
            - "rotations": Number of rotations (0, 1, 2, 3)
            - "x": The horizontal position where the piece will be placed before hard drop.
        This function simulates moves on a clone of the current piece to check validity.

        Returns:
            list: A list of move dictionaries.
        """
        moves = []
        original_piece = self.current_piece.clone()

        for rotations in range(4):
            piece_copy = original_piece.clone()
            for _ in range(rotations):
                piece_copy.rotate()

            rel_cells = [(j, i) for i, row in enumerate(piece_copy.matrix)
                         for j, val in enumerate(row) if val]
            min_offset = min(j for j, _ in rel_cells)
            max_offset = max(j for j, _ in rel_cells)

            min_x = -min_offset
            max_x = self.grid.cols - max_offset - 1

            for x in range(min_x, max_x + 1):
                test_piece = piece_copy.clone()
                test_piece.x = x
                if self.grid.is_valid_position(test_piece):
                    moves.append({"rotations": rotations, "x": x})
        return moves

    def simulate_move(self, move):
        """
        Simulate applying a specified move.

        Args:
            move (dict): A move description with keys "rotations" and "x".

        Returns:
            TetrisEnv: A clone of the current environment after applying the move and hard drop,
                       or None if the move is invalid.
        """
        simulated_game = self.clone()

        for _ in range(move["rotations"]):
            simulated_game.current_piece.rotate()

        simulated_game.current_piece.x = move["x"]

        if not simulated_game.grid.is_valid_position(simulated_game.current_piece):
            return None

        simulated_game.hard_drop()

        return simulated_game