def get_weights(weights):
    """
    Convert a 4-dimensional weight vector into a dictionary mapping each feature's weight.

    Args:
        weights (np.array): A 4-dimensional vector of weights.

    Returns:
        dict: A dictionary with keys "AGGREGATE_HEIGHT_WEIGHT", "COMPLETE_LINES_WEIGHT",
              "HOLES_WEIGHT", and "BUMPINESS_WEIGHT" and their corresponding values.
    """
    return {
        "AGGREGATE_HEIGHT_WEIGHT":  weights[0],
        "COMPLETE_LINES_WEIGHT":    weights[1],
        "HOLES_WEIGHT":             weights[2],
        "BUMPINESS_WEIGHT":         weights[3],
    }

def compute_column_heights(board, rows, cols):
    """
    Compute the height of each column in the board.
    The height is defined as the number of cells from the first filled cell (1) encountered
    to the bottom of the board. If a column is entirely empty, its height is 0.

    Args:
        board (list[list[int]]): The game board.
        rows (int): Number of rows in the board.
        cols (int): Number of columns in the board.

    Returns:
        list[int]: A list containing the height of each column.
    """
    heights = [0] * cols
    for col in range(cols):
        for row in range(rows):
            if board[row][col]:
                heights[col] = rows - row
                break
    return heights

def compute_aggregate_height(heights):
    """
    Compute the aggregate height by summing the heights of all columns.

    Args:
        heights (list[int]): List of column heights.

    Returns:
        int: The aggregate height.
    """
    return sum(heights)

def compute_holes(board, rows, cols):
    """
    Count the number of holes in the board.
    A hole is defined as an empty cell (0) that has at least one filled cell (1) above it in the same column.

    Args:
        board (list[list[int]]): The game board.
        rows (int): Number of rows in the board.
        cols (int): Number of columns in the board.

    Returns:
        int: The number of holes.
    """
    holes = 0
    for col in range(cols):
        block_found = False
        for row in range(rows):
            if board[row][col]:
                block_found = True
            elif block_found:
                holes += 1
    return holes

def compute_bumpiness(heights):
    """
    Compute the bumpiness of the board, defined as the sum of absolute differences between adjacent column heights.

    Args:
        heights (list[int]): List of column heights.

    Returns:
        int: The bumpiness value.
    """
    return sum(abs(heights[i] - heights[i + 1]) for i in range(len(heights) - 1))

def evaluate_state(state, weights):
    """
    Evaluate the board state using weighted features.
    The score is calculated as:
        score = (aggregate height * weight1) + (complete lines * weight2) +
                (holes * weight3) + (bumpiness * weight4)

    Assumes that the state has an attribute 'grid' with 'board', 'rows', and 'cols'.

    Args:
        state: The current state containing the game grid.
        weights (np.array): A 4-dimensional vector of weights.

    Returns:
        float: The evaluated score of the state.
    """
    board = state.grid.board
    rows, cols = state.grid.rows, state.grid.cols
    heights = compute_column_heights(board, rows, cols)
    aggregate_height = compute_aggregate_height(heights)
    complete_lines = state.grid.clear_lines()
    holes = compute_holes(board, rows, cols)
    bumpiness = compute_bumpiness(heights)
    weights = get_weights(weights)
    score = (weights["AGGREGATE_HEIGHT_WEIGHT"] * aggregate_height +
             weights["COMPLETE_LINES_WEIGHT"] * complete_lines +
             weights["HOLES_WEIGHT"] * holes +
             weights["BUMPINESS_WEIGHT"] * bumpiness)
    return score
