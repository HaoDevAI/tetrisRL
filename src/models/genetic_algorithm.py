import numpy as np
import random
from src.agents.linear_agent import TetrisAgent
from src.environments.env import GameManager
import datetime
import os
LOG_DIR = "E:\HaoDevAI\REL301m\HaoNA_Assignment\data\weights"

# Số lượng cá thể trong quần thể
POPULATION_SIZE = 50
# Số game chơi để đánh giá một cá thể
NUM_GAMES = 10
# Số nước đi tối đa trong mỗi game
MAX_MOVES = 50
# Tỷ lệ offsprings được tạo ra
OFFSPRING_RATE = 0.3
# Tỷ lệ đột biến cho mỗi offspring
MUTATION_RATE = 0.05
# Số cá thể được chọn ngẫu nhiên trong tournament (10% của POPULATION_SIZE)
TOURNAMENT_SIZE = POPULATION_SIZE // 10
# Số thế hệ tối đa
MAX_GENERATIONS = 2


# Hàm giả định để mô phỏng trò chơi Tetris
# Thực tế, hàm này sẽ chạy trò chơi Tetris với tham số heuristic và trả về tổng số dòng cleared
def simulate_tetris_game(random_weights):
    """
        Chạy 1 game Tetris sử dụng agent với số nước đi tối đa max_moves.
        Trả về số dòng cleared (score) của game.
        """
    gm = GameManager()
    agent = TetrisAgent(gm,random_weights)
    moves = 0

    while moves < MAX_MOVES and not gm.game_over:
        best_move = agent.get_best_move()
        if best_move is not None:
            # Thực hiện các xoay cần thiết
            for _ in range(best_move["rotations"]):
                gm.rotate_piece(clockwise=True)
            # Đặt mảnh vào vị trí x được chọn
            gm.current_piece.x = best_move["x"]
            # Thực hiện hard drop để đưa mảnh xuống vị trí cuối cùng
            gm.hard_drop()
        else:
            # Nếu không có nước đi khả dĩ, tiến hành drop tự động
            gm.drop_piece()
        moves += 1

    return gm.score


def compute_fitness(random_weights):
    total_lines = 0
    for _ in range(NUM_GAMES):
        total_lines += simulate_tetris_game(random_weights)
    return total_lines


# Hàm khởi tạo cá thể: tạo vector tham số 4 chiều trên mặt cầu đơn vị (unit 3-sphere)
def random_individual():
    vec = np.random.randn(4)  # Sinh vector 4 chiều ngẫu nhiên từ phân phối chuẩn
    return vec / np.linalg.norm(vec)


# Tournament selection: chọn 2 cá thể tốt nhất từ một tập con có kích thước TOURNAMENT_SIZE
def tournament_selection(population, fitnesses):
    # Chọn ngẫu nhiên TOURNAMENT_SIZE cá thể
    indices = random.sample(range(len(population)), TOURNAMENT_SIZE)
    # Sắp xếp theo fitness giảm dần (fitness cao hơn tốt hơn)
    sorted_indices = sorted(indices, key=lambda i: fitnesses[i], reverse=True)
    # Trả về 2 cá thể có fitness cao nhất trong tập con
    return (population[sorted_indices[0]], fitnesses[sorted_indices[0]],
            population[sorted_indices[1]], fitnesses[sorted_indices[1]])


# Weighted average crossover: tạo vector con từ 2 vector cha mẹ
def crossover(parent1, parent2, fitness1, fitness2):
    # Tạo vector trung bình có trọng số theo fitness
    child = parent1 * fitness1 + parent2 * fitness2
    # Chuẩn hóa vector con về đơn vị
    norm = np.linalg.norm(child)
    if norm == 0:
        return random_individual()
    return child / norm


# Mutation: với xác suất MUTATION_RATE, thay đổi một thành phần của vector ngẫu nhiên
def mutate(individual):
    if random.random() < MUTATION_RATE:
        # Chọn một chỉ số ngẫu nhiên trong vector
        idx = random.randint(0, 3)
        # Thay đổi thành phần đó bằng một giá trị ngẫu nhiên trong khoảng [-0.2, 0.2]
        mutation_value = random.uniform(-0.2, 0.2)
        individual[idx] += mutation_value
        # Chuẩn hóa lại vector
        individual = individual / np.linalg.norm(individual)
    return individual


def genetic_algorithm():
    # Khởi tạo quần thể ban đầu
    population = [random_individual() for _ in range(POPULATION_SIZE)]
    generation = 0

    while generation < MAX_GENERATIONS:
        # Tính fitness cho toàn bộ quần thể
        fitnesses = [compute_fitness(ind) for ind in population]
        best_fitness = max(fitnesses)
        best_ind = population[fitnesses.index(best_fitness)]
        print(f"Generation {generation}: Best Fitness = {best_fitness:.2f}")

        # Nếu đạt được fitness mong muốn (bạn có thể đặt điều kiện dừng cụ thể)
        # if best_fitness > SOME_THRESHOLD:
        #     break

        # Tạo offsprings
        num_offsprings = int(OFFSPRING_RATE * POPULATION_SIZE)
        offsprings = []
        for _ in range(num_offsprings):
            # Chọn tournament 2 cha mẹ
            parent1, f1, parent2, f2 = tournament_selection(population, fitnesses)
            # Tạo vector con từ weighted average crossover
            child = crossover(parent1, parent2, f1, f2)
            # Đột biến (có thể xảy ra)
            child = mutate(child)
            offsprings.append(child)

        # Sắp xếp lại quần thể theo fitness tăng dần (fitness thấp hơn là kém)
        sorted_population = [ind for _, ind in sorted(zip(fitnesses, population), key=lambda x: x[0])]
        # Thay thế 30% cá thể yếu nhất bằng các offsprings mới
        new_population = sorted_population[num_offsprings:] + offsprings
        population = new_population
        generation += 1

    return best_ind, best_fitness


if __name__ == "__main__":
    best_params, best_fit = genetic_algorithm()
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