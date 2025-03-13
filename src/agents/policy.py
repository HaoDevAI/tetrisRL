"""
ref weights
AGGREGATE_HEIGHT_WEIGHT = -0.510066
COMPLETE_LINES_WEIGHT = 0.760666
HOLES_WEIGHT = -0.35663
BUMPINESS_WEIGHT = -0.184483

"""

def get_weights(weights):
    """
    Nhận đầu vào là vector 4 chiều (np.array)
    và trả về một dictionary chứa các trọng số cho từng đặc trưng
    """
    return {
        "AGGREGATE_HEIGHT_WEIGHT":  weights[0],
        "COMPLETE_LINES_WEIGHT":    weights[1],
        "HOLES_WEIGHT":             weights[2],
        "BUMPINESS_WEIGHT":         weights[3],
    }

def compute_column_heights(board,rows,cols):
    """
    Tính chiều cao của từng cột.
    Chiều cao của cột được định nghĩa là số ô từ vị trí đầu tiên gặp khối (1) đến đáy board.
    Nếu cột trống hoàn toàn thì chiều cao bằng 0.
    """
    heights = [0] * cols
    for col in range(cols):
        # Tìm hàng đầu tiên có giá trị 1 trong cột, tính từ đầu (trên) xuống dưới.
        for row in range(rows):
            if board[row][col]:
                heights[col] = rows - row
                break  # chỉ cần giá trị đầu tiên
    return heights


def compute_aggregate_height(heights):
    """
    Tổng hợp chiều cao của tất cả các cột.
    """
    return sum(heights)


def compute_complete_lines(board):
    """
    Đếm số dòng đầy đủ.
    Một dòng được xem là đầy đủ nếu tất cả các ô đều có giá trị khác 0.
    """
    complete_lines = 0
    for row in board:
        if 0 not in row:
            complete_lines += 1
    return complete_lines


def compute_holes(board, rows, cols):
    """
    Đếm số lỗ trống trên board.
    Một lỗ trống là ô trống (0) có ít nhất một ô đã được lấp (1) phía trên nó trong cùng cột.
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
    Tính độ gồ ghề bằng tổng độ chênh lệch giữa các cột liền kề.
    """
    return sum(abs(heights[i] - heights[i + 1]) for i in range(len(heights) - 1))


def evaluate_state(state,weights):
    """
    Hàm tính điểm cho mỗi state action.
    Giả sử state có thuộc tính board là ma trận (2D list) với 0 và 1.
    Công thức tính điểm dựa trên:
        score = a * (aggregate height) + b * (complete lines)
              + c * (holes) + d * (bumpiness)
    Các hệ số a, b, c, d được định nghĩa ở đầu file.
    """
    board = state.grid.board  # giả sử state có thuộc tính board
    # Tính các đặc trưng
    rows, cols = state.grid.rows, state.grid.cols
    heights = compute_column_heights(board,rows,cols)
    aggregate_height = compute_aggregate_height(heights)
    complete_lines = compute_complete_lines(board)
    holes = compute_holes(board,rows,cols)
    bumpiness = compute_bumpiness(heights)
    weights = get_weights(weights)
    # Tính điểm tổng theo công thức
    score = (weights["AGGREGATE_HEIGHT_WEIGHT"] * aggregate_height +
             weights["COMPLETE_LINES_WEIGHT"] * complete_lines +
             weights["HOLES_WEIGHT"] * holes +
             weights["BUMPINESS_WEIGHT"] * bumpiness)

    return score



