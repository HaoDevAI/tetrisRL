import random
from src.environments.piece import Piece, SHAPES

def random_piece_generator():
    """
    Select a random Tetris piece and return a new Piece instance.
    """
    shape = random.choice(list(SHAPES.keys()))
    return Piece(shape)

# Example usage:
if __name__ == "__main__":
    piece = random_piece_generator()
    print("Generated piece shape:", piece.shape)
    print("Piece cells:", piece.get_cells())
