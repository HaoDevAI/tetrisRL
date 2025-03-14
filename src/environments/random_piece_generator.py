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

def seven_bag_random_generator(seed=None):
    """
    Generator that yields Tetris piece instances using the 7-bag randomizer algorithm.

    Args:
        seed (optional): Seed for the random number generator.

    Yields:
        Piece: A Tetris piece instance.
    """
    bag = []
    while True:
        if not bag:
            bag = generate_7_bag(seed)
        shape = bag.pop()
        yield Piece(shape)
