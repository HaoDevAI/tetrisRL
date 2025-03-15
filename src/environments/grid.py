class Grid:
    """
    Class representing the Tetris game grid.
    """
    def __init__(self, rows=20, cols=10):
        """
        Initialize the grid with the specified number of rows and columns.

        Args:
            rows (int): Number of rows in the grid.
            cols (int): Number of columns in the grid.
        """
        self.rows = rows
        self.cols = cols
        self.board = [[0 for _ in range(cols)] for _ in range(rows)]

    def clone(self):
        """
        Create and return a shallow copy of the grid.

        Returns:
            Grid: A new Grid instance with the same board configuration.
        """
        new_grid = Grid(self.rows, self.cols)
        new_grid.board = [row[:] for row in self.board]
        return new_grid

    def is_valid_position(self, piece):
        """
        Check if the given piece can be placed on the grid without collisions and within boundaries.

        Args:
            piece (Piece): The Tetris piece to check.

        Returns:
            bool: True if the piece can be placed, False otherwise.
        """
        rows, cols, board = self.rows, self.cols, self.board
        return all(
            0 <= x < cols and 0 <= y < rows and not board[y][x]
            for x, y in piece.get_cells()
        )

    def place_piece(self, piece):
        """
        Place the given piece on the grid by marking its cells with the piece's color.

        Args:
            piece (Piece): The Tetris piece to place on the grid.
        """
        for x, y in piece.get_cells():
            if 0 <= y < self.rows and 0 <= x < self.cols:
                self.board[y][x] = piece.color

    def clear_lines(self):
        """
        Clear fully occupied lines from the grid and return the number of lines cleared.

        Returns:
            int: The number of cleared lines.
        """
        cols = self.cols
        new_board = [row for row in self.board if 0 in row]
        lines_cleared = self.rows - len(new_board)
        if lines_cleared:
            empty_rows = [[0] * cols for _ in range(lines_cleared)]
            self.board = empty_rows + new_board
        else:
            self.board = new_board
        return lines_cleared

    def print_board(self):
        """
        Print the current state of the grid to the console.
        """
        for row in self.board:
            print(" ".join(str(cell) for cell in row))
