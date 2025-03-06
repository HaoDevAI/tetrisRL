class Grid:
    def __init__(self, rows=20, cols=10):
        # Initialize a 2D grid with zeros (empty cells)
        self.rows = rows
        self.cols = cols
        self.board = [[0 for _ in range(cols)] for _ in range(rows)]

    def is_valid_position(self, piece):
        """
        Check if the piece is in a valid position.
        Returns True if all cells of the piece are within bounds and not colliding.
        """
        for x, y in piece.get_cells():
            if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
                return False
            if self.board[y][x]:
                return False
        return True

    def place_piece(self, piece):
        """
        Place the piece on the board by marking the cells with 1 (or a specific identifier).
        """
        for x, y in piece.get_cells():
            if 0 <= y < self.rows and 0 <= x < self.cols:
                self.board[y][x] = 1

    def clear_lines(self):
        """
        Clear complete lines and return the number of lines cleared.
        """
        new_board = [row for row in self.board if any(cell == 0 for cell in row)]
        lines_cleared = self.rows - len(new_board)
        # Add new empty rows at the top
        for _ in range(lines_cleared):
            new_board.insert(0, [0 for _ in range(self.cols)])
        self.board = new_board
        return lines_cleared

    def print_board(self):
        """
        Print the board for debugging.
        """
        for row in self.board:
            print(" ".join(str(cell) for cell in row))

# Example usage:
if __name__ == "__main__":
    from piece import Piece  # Ensure piece.py is in the same folder

    grid = Grid()
    piece = Piece('T')
    if grid.is_valid_position(piece):
        grid.place_piece(piece)
    grid.print_board()
    cleared = grid.clear_lines()
    print("Lines cleared:", cleared)
