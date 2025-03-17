def get_weights(weights):
    """
    Convert a weight vector into a dictionary.

    Args:
        weights (np.array): Weight vector.

    Returns:
        dict: Dictionary mapping feature names to weights.
    """
    return {
        "AGGREGATE_HEIGHT_WEIGHT": weights[0],
        "COMPLETE_LINES_WEIGHT": weights[1],
        "HOLES_WEIGHT": weights[2],
        "BUMPINESS_WEIGHT": weights[3],
    }


def compute_column_heights(board, rows, cols):
    """
    Compute the heights of each column.

    Args:
        board (list[list[int]]): Game board.
        rows (int): Number of rows.
        cols (int): Number of columns.

    Returns:
        list[int]: List of column heights.
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
    Compute the aggregate height.

    Args:
        heights (list[int]): List of column heights.

    Returns:
        int: The aggregate height.
    """
    return sum(heights)


def compute_clear_lines(board):
    """
    Compute the number of complete lines in the board.

    Args:
        board (list[list[int]]): Game board.

    Returns:
        int: Number of complete lines.
    """
    return sum(1 for row in board if all(cell != 0 for cell in row))


def compute_holes(board, rows, cols):
    """
    Compute the number of holes in the board.

    Args:
        board (list[list[int]]): Game board.
        rows (int): Number of rows.
        cols (int): Number of columns.

    Returns:
        int: Number of holes.
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
    Compute the bumpiness of the board.

    Args:
        heights (list[int]): List of column heights.

    Returns:
        int: Bumpiness value.
    """
    return sum(abs(heights[i] - heights[i + 1]) for i in range(len(heights) - 1))


def evaluate_state(state, weights):
    """
    Evaluate the game state using weighted features.

    Args:
        state: Game state containing grid.
        weights (np.array): Weight vector.

    Returns:
        float: The evaluation score.
    """
    board = state.grid.board
    rows, cols = state.grid.rows, state.grid.cols
    heights = compute_column_heights(board, rows, cols)
    aggregate_height = compute_aggregate_height(heights)
    complete_lines = state.grid.lines_cleared
    holes = compute_holes(board, rows, cols)
    bumpiness = compute_bumpiness(heights)
    weights_dict = get_weights(weights)
    score = (weights_dict["AGGREGATE_HEIGHT_WEIGHT"] * aggregate_height +
             weights_dict["COMPLETE_LINES_WEIGHT"] * complete_lines +
             weights_dict["HOLES_WEIGHT"] * holes +
             weights_dict["BUMPINESS_WEIGHT"] * bumpiness)
    return score
