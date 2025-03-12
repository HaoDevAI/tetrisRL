import random
from src.environments.piece import Piece, SHAPES

SHAPE_KEYS = list(SHAPES.keys())

def random_piece_generator():
    """
    Select a random Tetris piece and return a new Piece instance.
    """
    shape = random.choice(SHAPE_KEYS)
    return Piece(shape)

def generate_7_bag():
    """Sinh ngẫu nhiên một danh sách chứa cả 7 loại tetromino."""
    tetrominos = SHAPE_KEYS.copy()  # Sao chép danh sách SHAPE_KEYS để không thay đổi gốc
    random.shuffle(tetrominos)
    return tetrominos

def seven_bag_random_generator():
    """Trình sinh khối theo thuật toán 7-bag."""
    bag = []
    while True:
        if not bag:  # Nếu túi trống, tạo một túi mới
            bag = generate_7_bag()
        shape = bag.pop()
        yield Piece(shape) # Lấy từng khối một từ túi

# Example usage:
if __name__ == "__main__":
    piece = random_piece_generator()
    print("Generated piece shape:", piece.shape)
    print("Piece cells:", piece.get_cells())
