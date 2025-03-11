import numpy as np
import time
from src.agents.linear_agent import TetrisAgent
from src.environments.env import TetrisEnv
import datetime
import multiprocessing as mp
import matplotlib.pyplot as plt
import psutil
from pathlib import Path
# Đường dẫn

FILE_DIR = Path(__file__).parent.parent.parent
WEIGHT_DIR = FILE_DIR / 'data' / 'weights'
PLOT_DIR = FILE_DIR / 'data' / 'plots'
LOG_DIR = FILE_DIR / 'data' / 'logs'


# Các tham số ES
PRETRAINED_WEIGHTS = WEIGHT_DIR / 'start_weights.npy'
POPULATION_SIZE = 100  # Số lượng cá thể
NUM_GAMES = 5  # Số game để đánh giá một cá thể
MAX_MOVES = 500  # Số nước đi tối đa trong mỗi game
MAX_GENERATIONS = 10  # Số thế hệ huấn luyện ES
SIGMA = 0.1  # Độ lệch chuẩn của nhiễu Gaussian
ALPHA = 0.01  # Learning rate


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
    # Giả sử PRETRAINED_WEIGHTS, MAX_GENERATIONS, POPULATION_SIZE, SIGMA, ALPHA, compute_fitness đã được định nghĩa
    baseline = np.load(PRETRAINED_WEIGHTS)
    best_rewards = []
    avg_rewards = []

    for generation in range(MAX_GENERATIONS):
        start_time = time.time()
        # Sinh noise vector hoá, với noise có shape (POPULATION_SIZE, 4)
        noise = np.random.randn(POPULATION_SIZE, 4)

        # Tạo candidate bằng cách cộng baseline với nhiễu đã nhân SIGMA
        candidates = baseline + SIGMA * noise

        # Chuẩn hoá từng candidate: đưa candidate về trên mặt cầu đơn vị (normalize theo hàng)
        candidates = candidates / np.linalg.norm(candidates, axis=1, keepdims=True)

        # Đánh giá fitness song song cho tất cả candidate
        with mp.Pool() as pool:
            rewards = np.array(list(pool.imap(compute_fitness, candidates)))

        # Tính toán update:
        mean_reward = np.mean(rewards)
        standardized_rewards = (rewards - mean_reward) / (np.std(rewards) + 1e-8)
        update = (ALPHA / (SIGMA * POPULATION_SIZE)) * np.dot(noise.T, standardized_rewards)

        # Cập nhật baseline và chuẩn hoá lại baseline
        baseline += update
        baseline /= np.linalg.norm(baseline)

        # Logging kết quả tốt nhất của generation
        best_reward = np.max(rewards)
        generation_time = time.time() - start_time
        print(f"Generation {generation}: | Best Fitness = {best_reward:.2f} |Avg Fitness = {mean_reward:.2f} | Time : {generation_time:.2f}")
        print(f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%")
        # Lưu lại thông tin của mỗi generation
        best_rewards.append(best_reward)
        avg_rewards.append(mean_reward)

    best_fitness = compute_fitness(baseline)
    return baseline, best_fitness, best_rewards, avg_rewards


if __name__ == "__main__":
    print(f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%")
    print("Training in parallel...")
    # Lưu lịch sử train
    log_name = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_train_log.txt")
    log_path = LOG_DIR / log_name
    start_time = datetime.datetime.now()
    training_info = f"""
        --- THÔNG SỐ TRAINING ---
        Time Start: {start_time.strftime("%Y-%m-%d %H:%M:%S")}
        WEIGHTS: {PRETRAINED_WEIGHTS}
        POPULATION_SIZE: {POPULATION_SIZE}
        NUM_GAMES: {NUM_GAMES}
        MAX_MOVES: {MAX_MOVES}
        MAX_GENERATIONS: {MAX_GENERATIONS}
        SIGMA: {SIGMA}
        ALPHA: {ALPHA}

        """
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(training_info)

    #training...
    best_params, best_fit, best_rewards, avg_rewards = evolution_strategy()
    print("\nTối ưu được tham số heuristic:")
    print(f"AGGREGATE_HEIGHT_WEIGHT = {best_params[0]:.6f}")
    print(f"COMPLETE_LINES_WEIGHT = {best_params[1]:.6f}")
    print(f"HOLES_WEIGHT = {best_params[2]:.6f}")
    print(f"BUMPINESS_WEIGHT = {best_params[3]:.6f}")
    print(f"Fitness: {best_fit}")
    #saving...
    end_time = datetime.datetime.now()
    training_results = f"""
        --- KẾT QUẢ TRAINING ---
        Time End: {end_time.strftime("%Y-%m-%d %H:%M:%S")}
        Training Duration: {end_time - start_time}
        Best Fitness: {best_fit}
        Best Rewards per Generation: {best_rewards}
        Average Rewards per Generation: {avg_rewards}

        Final Heuristic Parameters:
        AGGREGATE_HEIGHT_WEIGHT = {best_params[0]:.6f}
        COMPLETE_LINES_WEIGHT = {best_params[1]:.6f}
        HOLES_WEIGHT = {best_params[2]:.6f}
        BUMPINESS_WEIGHT = {best_params[3]:.6f}
        """
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(training_results)

    print(f"Training logs saved in {log_path}")
    #Lưu weights
    save_name = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_best_weights.npy")
    save_path = WEIGHT_DIR / save_name
    np.save(save_path, best_params)
    print("Best weights saved at {}".format(save_path))

    # Lưu biểu đồ plot fitness theo generation
    plt.figure(figsize=(10, 5))
    plt.plot(range(MAX_GENERATIONS), best_rewards, label='Best Fitness', marker='o', markersize=3)
    plt.plot(range(MAX_GENERATIONS), avg_rewards, label='Average Fitness', linestyle='--')
    plt.xlabel('Generation')
    plt.ylabel('Fitness')
    plt.title('Evolution Strategy Training Progress')
    plt.legend()
    plt.grid(True)
    plot_name = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_fitness_plot.png")
    fitness_plot_path = PLOT_DIR / plot_name
    plt.savefig(fitness_plot_path)
    plt.close()
    print(f"Fitness plot saved at {fitness_plot_path}")




