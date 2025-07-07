import random
from src.env.piece import Piece, SHAPES

SHAPE_KEYS = list(SHAPES.keys())


def random_piece_generator(seed=None):
    """
    Generate a random Tetris piece.

    Args:
        seed (optional): Seed for the random generator.

    Returns:
        Piece: A Tetris piece instance.
    """
    rng = random.Random(seed) if seed is not None else random
    shape = rng.choice(SHAPE_KEYS)
    return Piece(shape)


def generate_7_bag(seed=None):
    """
    Generate a 7-bag of Tetris piece identifiers.

    Args:
        seed (optional): Seed for the random generator.

    Returns:
        list: A list of piece identifiers in random order.
    """
    rng = random.Random(seed) if seed is not None else random
    tetrominos = SHAPE_KEYS.copy()
    rng.shuffle(tetrominos)
    return tetrominos
