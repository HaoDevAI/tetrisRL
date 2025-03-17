import random
from src.environments.piece import Piece, SHAPES

SHAPE_KEYS = list(SHAPES.keys())

def random_piece_generator(seed=None):
    """
    Generate a random Tetris piece instance.

    Args:
        seed (optional): Seed for the random number generator.

    Returns:
        Piece: A new Tetris piece instance with a random shape.
    """
    rng = random.Random(seed) if seed is not None else random
    shape = rng.choice(SHAPE_KEYS)
    return Piece(shape)

def generate_7_bag(seed=None):
    """
    Generate a randomized list of all 7 tetromino shapes.

    Args:
        seed (optional): Seed for the random number generator.

    Returns:
        list: A list of all tetromino shape identifiers in randomized order.
    """
    rng = random.Random(seed) if seed is not None else random
    tetrominos = SHAPE_KEYS.copy()
    rng.shuffle(tetrominos)
    return tetrominos
