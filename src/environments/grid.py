class Grid:
    def __init__(self, rows=20, cols=10):
        # Initialize a 2D grid with zeros (empty cells)
        self.rows = rows
        self.cols = cols
        self.board = [[0 for _ in range(cols)] for _ in range(rows)]

    def clone(self):
        new_grid = Grid(self.rows, self.cols)
        # Tạo copy nông cho board (list of lists)
        new_grid.board = [row[:] for row in self.board]
        return new_grid

    def is_valid_position(self, piece):
        rows, cols, board = self.rows, self.cols, self.board
        return all(
            0 <= x < cols and 0 <= y < rows and not board[y][x]
            for x, y in piece.get_cells()
        )

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
        cols = self.cols
        # Giữ lại các dòng không đầy (có chứa 0)
        new_board = [row for row in self.board if 0 in row]
        lines_cleared = self.rows - len(new_board)
        if lines_cleared:
            # Tạo các dòng trống mới
            empty_rows = [[0] * cols for _ in range(lines_cleared)]
            # Nối các dòng trống vào đầu bảng
            self.board = empty_rows + new_board
        else:
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
