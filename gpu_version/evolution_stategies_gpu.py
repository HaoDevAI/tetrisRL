import numpy as np
import random
import datetime
import os
import torch
from agent_gpu import TetrisAgentGPU      # Sử dụng agent GPU batch
from env_gpu import TetrisEnvGPU_Batch    # Sử dụng môi trường GPU batch

# Đường dẫn
PRETRAINED_WEIGHTS = 'E:\\HaoDevAI\\REL301m\\HaoNA_Assignment\\data\\weights\\best_weights.npy'
LOG_DIR = "E:\\HaoDevAI\\REL301m\\HaoNA_Assignment\\data\\weights"

# Các tham số ES
POPULATION_SIZE = 50    # Số lượng cá thể (số mẫu nhiễu)
NUM_GAMES = 10          # Số game trong mỗi batch simulation (batch_size)
MAX_MOVES = 50          # Số nước đi tối đa trong mỗi game
MAX_GENERATIONS = 2     # Số thế hệ huấn luyện ES (có thể tăng lên để đạt hiệu quả tốt hơn)
SIGMA = 0.1             # Độ lệch chuẩn của nhiễu Gaussian
ALPHA = 0.01            # Learning rate (tốc độ học)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

def simulate_tetris_game_batch(weights, batch_size=NUM_GAMES):
    """
    Chạy một batch gồm NUM_GAMES game Tetris trên GPU với trọng số heuristic cho agent.
    Trả về trung bình điểm số (số dòng cleared) của batch.
    """
    # Khởi tạo môi trường batch và agent GPU
    env = TetrisEnvGPU_Batch(batch_size=batch_size, device=device)
    agent = TetrisAgentGPU(env, weights)
    moves = 0

    while moves < MAX_MOVES and (~env.game_over).any():
        # Lấy nước đi tốt nhất cho từng game trong batch
        best_moves = agent.get_best_move()  # Trả về list (độ dài = batch_size) với mỗi phần tử là dict hoặc None
        # Với mỗi game, nếu có nước đi, thực hiện xoay và hard drop; nếu không, gọi drop_piece
        for i, move in enumerate(best_moves):
            if env.game_over[i]:
                continue
            if move is not None:
                # Thực hiện các xoay cần thiết
                for _ in range(move["rotations"]):
                    # Ta xoay cho game thứ i (sử dụng phương thức get_item)
                    piece = env.current_piece.get_item(i)
                    piece.rotate()
                    # Cập nhật lại giá trị của current_piece tại index i
                    env.current_piece.x[i] = piece.x[0]  # Vì get_item trả về batch_size=1
                    env.current_piece.y[i] = piece.y[0]
                    env.current_piece.matrix[i] = piece.matrix[0]
                # Đặt mảnh theo vị trí x đã chọn
                env.current_piece.x[i] = torch.tensor(move["x"], device=device)
                # Hard drop cho game thứ i
                simulated_game = env.simulate_move(move, i)
                if simulated_game is not None:
                    # Cập nhật điểm cho game thứ i
                    env.score[i] = simulated_game.score
                    # Cập nhật board của game thứ i từ simulated_game
                    env.grid.board[i] = simulated_game.grid.board[0]
                    # Cập nhật current_piece của game thứ i
                    env.current_piece.x[i] = simulated_game.current_piece.x[0]
                    env.current_piece.y[i] = simulated_game.current_piece.y[0]
                else:
                    # Nếu simulate_move trả về None, gọi drop_piece để cập nhật tự động
                    # (drop_piece sẽ gọi hard_drop bên trong nếu không di chuyển được)
                    env.drop_piece()
            else:
                # Nếu không có nước đi khả dĩ, gọi drop_piece cho game đó
                env.drop_piece()
        moves += 1

    # Trả về trung bình điểm của batch
    return torch.mean(env.score).item()

def compute_fitness(random_weights):
    """
    Tính fitness cho một vector trọng số bằng cách chạy 1 batch simulation trên GPU
    với số game = NUM_GAMES và trả về trung bình điểm.
    """
    return simulate_tetris_game_batch(random_weights, batch_size=NUM_GAMES)

def random_individual():
    """
    Tạo cá thể ban đầu: vector 4 chiều trên mặt cầu đơn vị.
    """
    vec = np.random.randn(4)
    return vec / np.linalg.norm(vec)

def evolution_strategy():
    # Khởi tạo vector trọng số baseline từ file đã huấn luyện trước (hoặc random_individual)
    baseline = np.load(PRETRAINED_WEIGHTS)
    # baseline = random_individual()

    for generation in range(MAX_GENERATIONS):
        noise = [np.random.randn(4) for _ in range(POPULATION_SIZE)]
        rewards = []

        for i in range(POPULATION_SIZE):
            candidate = baseline + SIGMA * noise[i]
            candidate = candidate / np.linalg.norm(candidate)
            reward = compute_fitness(candidate)
            rewards.append(reward)

        rewards = np.array(rewards)
        mean_reward = np.mean(rewards)

        update = np.zeros_like(baseline)
        for i in range(POPULATION_SIZE):
            update += noise[i] * (rewards[i] - mean_reward)
        baseline = baseline + (ALPHA / (SIGMA * POPULATION_SIZE)) * update
        baseline = baseline / np.linalg.norm(baseline)

        best_reward = np.max(rewards)
        print(f"Generation {generation}: Best Fitness = {best_reward:.2f}")

    best_fitness = compute_fitness(baseline)
    return baseline, best_fitness

if __name__ == "__main__":
    best_params, best_fit = evolution_strategy()
    print("\nOptimized heuristic parameters:")
    print(f"AGGREGATE_HEIGHT_WEIGHT = {best_params[0]:.6f}")
    print(f"COMPLETE_LINES_WEIGHT = {best_params[1]:.6f}")
    print(f"HOLES_WEIGHT = {best_params[2]:.6f}")
    print(f"BUMPINESS_WEIGHT = {best_params[3]:.6f}")
    print(f"Fitness: {best_fit}")

    save_name = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_best_weights.npy")
    save_path = os.path.join(LOG_DIR, save_name)
    np.save(save_path, best_params)
    print("Best weights saved at {}".format(save_path))
