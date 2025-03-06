import copy

SHAPES = {
        'I': [
            [
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0],   #shape ----
                [0, 0, 0, 0]
            ],
            [
                [0, 0, 1, 0],
                [0, 0, 1, 0],   #rotated 90 degrees
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

class Piece:
    def __init__(self, shape):
        if shape not in SHAPES:
            raise ValueError(f"Shape {shape} is not defined.")
        self.shape = shape
        self.rotations = SHAPES[shape]
        self.rotation_index = 0
        self.matrix = copy.deepcopy(self.rotations[self.rotation_index])
        # Position on grid (x for column, y for row)
        self.x = 3  # Starting X position (may vary)
        self.y = 0  # Starting Y position

    def rotate(self):
        """Rotate the piece clockwise."""
        self.rotation_index = (self.rotation_index + 1) % len(self.rotations)
        self.matrix = copy.deepcopy(self.rotations[self.rotation_index])

    def rotate_counterclockwise(self):
        """Rotate the piece counterclockwise."""
        self.rotation_index = (self.rotation_index - 1) % len(self.rotations)
        self.matrix = [row[:] for row in self.rotations[self.rotation_index]]

    def get_cells(self):
        """
        Returns the absolute positions of the blocks that make up the piece
        relative to the grid.
        """
        cells = []
        for i, row in enumerate(self.matrix):
            for j, val in enumerate(row):
                if val:
                    cells.append((self.x + j, self.y + i))
        return cells

    def move(self, dx, dy):
        """Move the piece by dx, dy."""
        self.x += dx
        self.y += dy

    def clone(self):
        """Return a copy of the piece (for simulation purposes)."""
        cloned = Piece(self.shape)
        cloned.rotation_index = self.rotation_index
        cloned.matrix = copy.deepcopy(self.matrix)
        cloned.x = self.x
        cloned.y = self.y
        return cloned


# Test
if __name__ == "__main__":
    piece = Piece('T')
    print("Initial cells:", piece.get_cells())
    piece.rotate()
    print("After rotation:", piece.get_cells())