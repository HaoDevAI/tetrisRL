import numpy as np
import random
from src.agents.linear_agent import TetrisAgent
from src.environments.env import TetrisEnv
import datetime
import os
import multiprocessing as mp

# Đường dẫn
PRETRAINED_WEIGHTS = 'E:\\HaoDevAI\\REL301m\\HaoNA_Assignment\\data\\weights\\best_weights.npy'
LOG_DIR = "E:\\HaoDevAI\\REL301m\\HaoNA_Assignment\\data\\weights"

# Các tham số ES
POPULATION_SIZE = 50  # Số lượng cá thể (số mẫu nhiễu)
NUM_GAMES = 10  # Số game để đánh giá một cá thể
MAX_MOVES = 50  # Số nước đi tối đa trong mỗi game
MAX_GENERATIONS = 2  # Số thế hệ huấn luyện ES (có thể tăng lên để đạt hiệu quả tốt hơn)
SIGMA = 0.1  # Độ lệch chuẩn của nhiễu Gaussian
ALPHA = 0.01  # Learning rate (tốc độ học)


# Hàm mô phỏng trò chơi Tetris với bộ trọng số heuristic cho agent
def simulate_tetris_game(weights):
    """
    Chạy 1 game Tetris sử dụng agent với số nước đi tối đa MAX_MOVES.
    Trả về số dòng cleared (score) của game.
    """
    # Khởi tạo môi trường và agent (lưu ý: TetrisEnv và TetrisAgent cần được cài đặt phù hợp)
    env = TetrisEnv()
    agent = TetrisAgent(env, weights)
    moves = 0

    while moves < MAX_MOVES and not env.game_over:
        best_move = agent.get_best_move()
        if best_move is not None:
            # Thực hiện các xoay cần thiết
            for _ in range(best_move["rotations"]):
                env.rotate_piece(clockwise=True)
            # Đặt mảnh vào vị trí x được chọn
            env.current_piece.x = best_move["x"]
            # Thực hiện hard drop để đưa mảnh xuống vị trí cuối cùng
            env.hard_drop()
        else:
            # Nếu không có nước đi khả dĩ, tiến hành drop tự động
            env.drop_piece()
        moves += 1

    return env.score


def compute_fitness(random_weights):
    """Parallel-friendly fitness computation function"""
    total_lines = 0
    for _ in range(NUM_GAMES):
        total_lines += simulate_tetris_game(random_weights)
    return total_lines


def evolution_strategy():
    baseline = np.load(PRETRAINED_WEIGHTS)

    for generation in range(MAX_GENERATIONS):
        noise = [np.random.randn(4) for _ in range(POPULATION_SIZE)]
        candidates = []

        # Generate candidate solutions
        for n in noise:
            candidate = baseline + SIGMA * n
            candidate /= np.linalg.norm(candidate)
            candidates.append(candidate)

        # Parallel fitness evaluation
        with mp.Pool() as pool:
            rewards = pool.map(compute_fitness, candidates)
        rewards = np.array(rewards)

        # Update parameters
        mean_reward = np.mean(rewards)
        update = np.zeros_like(baseline)
        for i in range(POPULATION_SIZE):
            update += noise[i] * (rewards[i] - mean_reward)
        baseline += (ALPHA / (SIGMA * POPULATION_SIZE)) * update
        baseline /= np.linalg.norm(baseline)

        best_reward = np.max(rewards)
        print(f"Generation {generation}: Best Fitness = {best_reward:.2f}")

    best_fitness = compute_fitness(baseline)
    return baseline, best_fitness


if __name__ == "__main__":
    best_params, best_fit = evolution_strategy()
    print("\nTối ưu được tham số heuristic:")
    print(f"AGGREGATE_HEIGHT_WEIGHT = {best_params[0]:.6f}")
    print(f"COMPLETE_LINES_WEIGHT = {best_params[1]:.6f}")
    print(f"HOLES_WEIGHT = {best_params[2]:.6f}")
    print(f"BUMPINESS_WEIGHT = {best_params[3]:.6f}")
    print(f"Fitness: {best_fit}")

    save_name = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_best_weights.npy")
    save_path = os.path.join(LOG_DIR, save_name)
    np.save(save_path, best_params)
    print("Best weights saved at {}".format(save_path))
