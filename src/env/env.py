from src.env.grid import Grid
from src.env.random_piece_generator import random_piece_generator, generate_7_bag
from src.env.piece import Piece
from src.utils.config import gravity_rate

class TetrisEnv:
    """Tetris game environment class."""

    def __init__(self, rows=20, cols=10, generator="classic", seed=None, level=0):
        """
        Initialize the Tetris environment.

        Args:
            rows (int): Number of grid rows.
            cols (int): Number of grid columns.
            generator (str): "random" or "classic" generator.
            seed: Seed for random generation.
        """
        self.rows = rows
        self.cols = cols
        self.generator = generator
        self.seed = seed
        self.level = level
        self.grid = Grid(rows, cols)
        self.score = 0
        self.moves_played = 0
        self.timing = 0
        self.game_over = False
        self._init_pieces()


    def _init_pieces(self):
        """Initialize current and next pieces."""
        if self.generator == "random":
            self.current_piece = random_piece_generator(seed=self.seed)
            self.next_piece = random_piece_generator()
        elif self.generator == "classic":
            self.current_bag = generate_7_bag(seed=self.seed)
            self.current_piece = Piece(self.current_bag.pop())
            if not self.current_bag:
                self.current_bag = generate_7_bag()
            self.next_piece = Piece(self.current_bag.pop())

    def reset(self):
        """Reset the game state."""
        self.grid.reset()
        self.score = 0
        self.moves_played = 0
        self.game_over = False
        self._init_pieces()

    def clone(self):
        """
        Clone the Tetris environment.

        Returns:
            TetrisEnv: A cloned instance.
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
            new_env.current_bag = self.current_bag.copy() if hasattr(self, 'current_bag') else []
        return new_env

    def new_piece(self):
        """Update the environment with a new piece."""
        self.current_piece = self.next_piece
        self.current_piece.x = (self.grid.cols - self.current_piece.piece_width) // 2
        if self.generator == "random":
            self.next_piece = random_piece_generator()
        elif self.generator == "classic":
            if not self.current_bag:
                self.current_bag = generate_7_bag()
            self.next_piece = Piece(self.current_bag.pop())
        if not self.grid.is_valid_position(self.current_piece):
            self.game_over = True

    def move_piece(self, dx, dy):
        """
        Move the current piece.

        Args:
            dx (int): Horizontal displacement.
            dy (int): Vertical displacement.

        Returns:
            bool: True if move is successful, False otherwise.
        """
        self.current_piece.move(dx, dy)
        if not self.grid.is_valid_position(self.current_piece):
            self.current_piece.move(-dx, -dy)
            return False
        return True

    def rotate_piece(self, clockwise=True):
        """
        Rotate the current piece.

        Args:
            clockwise (bool): True for clockwise rotation.

        Returns:
            bool: True if rotation is successful, False otherwise.
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

    def swap_piece(self):
        """
        Swap current piece with the next piece while maintaining position.

        Returns:
            bool: True if swap is successful, False otherwise.
        """
        # Store the current piece and its position
        temp_piece = self.current_piece.clone()
        current_x = self.current_piece.x
        current_y = self.current_piece.y

        # Set current piece to next piece but keep the position
        self.current_piece = self.next_piece.clone()
        self.current_piece.x = current_x
        self.current_piece.y = current_y

        # Check if the new position is valid
        if not self.grid.is_valid_position(self.current_piece):
            # If invalid, restore the original piece and return False
            self.current_piece = temp_piece
            return False

        # Set the next piece to the stored piece
        self.next_piece = temp_piece
        self.next_piece.x = (self.grid.cols - self.current_piece.piece_width) // 2
        self.next_piece.y = 0
        return True

    def drop_piece(self):
        """Drop the piece by one unit; if unable, place it on the grid."""
        if not self.move_piece(0, 1):
            self.grid.place_piece(self.current_piece)
            self.score += self.grid.lines_cleared
            if not self.game_over:
                self.new_piece()

    def hard_drop(self):
        """Perform a hard drop."""
        while self.move_piece(0, 1):
            pass
        self.drop_piece()

    def get_ghost_piece(self):
        """
        Get the ghost (shadow) piece.

        Returns:
            Piece: The ghost piece.
        """
        ghost = self.current_piece.clone()
        while self.grid.is_valid_position(ghost):
            ghost.y += 1
        ghost.y -= 1
        return ghost

    def update(self,dt):
        """Update the game state."""
        self.timing += dt
        threshold = self.get_gravity()
        if self.timing >= threshold*dt:
            self.timing = 0
            self.drop_piece()

    def get_state(self):
        """
        Get the current game state.

        Returns:
            dict: Dictionary containing grid, current piece cells, score, and game over status.
        """
        return {
            "grid": self.grid.board,
            "current_piece_cells": self.current_piece.get_cells(),
            "score": self.score,
            "game_over": self.game_over
        }

    def get_possible_moves(self):
        """
        Compute possible moves for the current piece.

        Returns:
            list: List of move dictionaries.
        """
        moves = []
        original_piece = self.current_piece.clone()
        for rotations in range(4):
            piece_copy = original_piece.clone()
            for _ in range(rotations):
                piece_copy.rotate()
            rel_cells = [(j, i) for i, row in enumerate(piece_copy.matrix) for j, val in enumerate(row) if val]
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
        Simulate applying a move.

        Args:
            move (dict): Move description.

        Returns:
            TetrisEnv: Cloned environment after applying the move, or None if invalid.
        """
        simulated_game = self.clone()
        for _ in range(move["rotations"]):
            simulated_game.current_piece.rotate()
        simulated_game.current_piece.x = move["x"]
        if not simulated_game.grid.is_valid_position(simulated_game.current_piece):
            return None
        simulated_game.hard_drop()
        return simulated_game

    def get_gravity(self):
        """
        Adjust dropping speed of the pieces.
        """
        if self.score // 10 > self.level and self.level < 29:
            self.level += 1
        return gravity_rate[self.level]

