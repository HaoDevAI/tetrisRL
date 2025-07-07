class Grid:
    """Class representing the Tetris grid."""

    def __init__(self, rows=20, cols=10):
        """
        Initialize the grid.

        Args:
            rows (int): Number of rows.
            cols (int): Number of columns.
        """
        self.rows = rows
        self.cols = cols
        self.lines_cleared = 0
        self.board = [[0 for _ in range(cols)] for _ in range(rows)]

    def clone(self):
        """
        Clone the grid.

        Returns:
            Grid: A cloned grid instance.
        """
        new_grid = Grid(self.rows, self.cols)
        new_grid.board = [row[:] for row in self.board]
        new_grid.lines_cleared = self.lines_cleared
        return new_grid

    def is_valid_position(self, piece):
        """
        Check if the piece is in a valid position.

        Args:
            piece (Piece): Tetris piece.

        Returns:
            bool: True if valid, False otherwise.
        """
        return all(
            0 <= x < self.cols and 0 <= y < self.rows and not self.board[y][x]
            for x, y in piece.get_cells()
        )

    def place_piece(self, piece):
        """
        Place the piece on the grid.

        Args:
            piece (Piece): Tetris piece.
        """
        for x, y in piece.get_cells():
            if 0 <= y < self.rows and 0 <= x < self.cols:
                self.board[y][x] = piece.color
        self.lines_cleared = self.clear_lines()

    def clear_lines(self):
        """
        Clear complete lines in the grid.

        Returns:
            int: Number of lines cleared.
        """
        new_board = [row for row in self.board if 0 in row]
        lines_cleared = self.rows - len(new_board)
        if lines_cleared:
            empty_rows = [[0] * self.cols for _ in range(lines_cleared)]
            self.board = empty_rows + new_board
        else:
            self.board = new_board
        return lines_cleared

    def reset(self):
        """Reset the grid to the initial state."""
        self.lines_cleared = 0
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

    def print_board(self):
        """Print the grid state."""
        for row in self.board:
            print(" ".join(str(cell) for cell in row))

