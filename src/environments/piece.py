# Mapping Tetris piece identifiers to their rotation matrices.
SHAPES = {
    'I': [
        [
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ],
        [
            [0, 0, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 0]
        ]
    ],
    'O': [
        [
            [1, 1],
            [1, 1]
        ]
    ],
    'T': [
        [
            [0, 1, 0],
            [1, 1, 1],
            [0, 0, 0]
        ],
        [
            [0, 1, 0],
            [0, 1, 1],
            [0, 1, 0]
        ],
        [
            [0, 0, 0],
            [1, 1, 1],
            [0, 1, 0]
        ],
        [
            [0, 1, 0],
            [1, 1, 0],
            [0, 1, 0]
        ]
    ],
    'S': [
        [
            [0, 1, 1],
            [1, 1, 0],
            [0, 0, 0]
        ],
        [
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0]
        ]
    ],
    'Z': [
        [
            [1, 1, 0],
            [0, 1, 1],
            [0, 0, 0]
        ],
        [
            [0, 0, 1],
            [0, 1, 1],
            [0, 1, 0]
        ]
    ],
    'J': [
        [
            [1, 0, 0],
            [1, 1, 1],
            [0, 0, 0]
        ],
        [
            [0, 1, 1],
            [0, 1, 0],
            [0, 1, 0]
        ],
        [
            [0, 0, 0],
            [1, 1, 1],
            [0, 0, 1]
        ],
        [
            [0, 1, 0],
            [0, 1, 0],
            [1, 1, 0]
        ]
    ],
    'L': [
        [
            [0, 0, 1],
            [1, 1, 1],
            [0, 0, 0]
        ],
        [
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 1]
        ],
        [
            [0, 0, 0],
            [1, 1, 1],
            [1, 0, 0]
        ],
        [
            [1, 1, 0],
            [0, 1, 0],
            [0, 1, 0]
        ]
    ]
}

# Mapping Tetris piece identifiers to their corresponding RGB colors.
SHAPES_COLORS = {
    "I": (102, 204, 204),
    "O": (255, 255, 153),
    "T": (204, 153, 255),
    "S": (153, 255, 153),
    "Z": (255, 153, 153),
    "J": (102, 153, 255),
    "L": (255, 178, 102)
}


class Piece:
    """
    Class representing a Tetris piece with its shape, color, and rotational states.
    """
    def __init__(self, shape):
        """
        Initialize a Piece object with a specified shape.

        Args:
            shape (str): The identifier of the Tetris shape.

        Raises:
            ValueError: If the specified shape is not defined in SHAPES.
        """
        if shape not in SHAPES:
            raise ValueError(f"Shape {shape} is not defined.")
        self.shape = shape
        self.color = SHAPES_COLORS[shape]
        self.rotations = SHAPES[shape]
        self.rotation_index = 0
        self.matrix = [row[:] for row in self.rotations[self.rotation_index]]
        self.x = 3
        self.y = 0

    @property
    def piece_width(self):
        """
        Calculate the width of the piece based on its current matrix representation.

        Returns:
            int: The width of the piece.
        """
        rel_cells = [j for i, row in enumerate(self.matrix)
                     for j, val in enumerate(row) if val]
        if not rel_cells:
            return 0
        min_offset = min(rel_cells)
        max_offset = max(rel_cells)
        return max_offset - min_offset + 1

    def rotate(self):
        """
        Rotate the piece clockwise.
        """
        self.rotation_index = (self.rotation_index + 1) % len(self.rotations)
        self.matrix = [row[:] for row in self.rotations[self.rotation_index]]

    def rotate_counterclockwise(self):
        """
        Rotate the piece counterclockwise.
        """
        self.rotation_index = (self.rotation_index - 1) % len(self.rotations)
        self.matrix = [row[:] for row in self.rotations[self.rotation_index]]

    def get_cells(self):
        """
        Get the absolute grid positions of the blocks that constitute the piece.

        Returns:
            list of tuple: A list containing (x, y) positions of each block.
        """
        cells = []
        for i, row in enumerate(self.matrix):
            for j, val in enumerate(row):
                if val:
                    cells.append((self.x + j, self.y + i))
        return cells

    def move(self, dx, dy):
        """
        Move the piece by a given offset.

        Args:
            dx (int): Change in x-coordinate (columns).
            dy (int): Change in y-coordinate (rows).
        """
        self.x += dx
        self.y += dy

    def clone(self):
        """
        Create and return a copy of the current piece.

        Returns:
            Piece: A new Piece instance with the same state.
        """
        cloned = Piece(self.shape)
        cloned.rotation_index = self.rotation_index
        cloned.matrix = [row[:] for row in self.matrix]
        cloned.x = self.x
        cloned.y = self.y
        return cloned