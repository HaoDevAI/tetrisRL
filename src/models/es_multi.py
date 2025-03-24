import numpy as np
import time
import datetime
import multiprocessing as mp
import matplotlib.pyplot as plt
import psutil
from pathlib import Path
import yaml
from functools import partial

from src.agents.agent import TetrisAgent
from src.environments.env import TetrisEnv


def simulate_tetris_game(env, weights, max_moves):
    """
    Run a Tetris game using the agent with a maximum number of moves.

    Args:
        env (TetrisEnv): The Tetris game environment.
        weights (np.array): A weight vector for evaluating game states.
        max_moves (int): Maximum number of moves to perform.

    Returns:
        int: The number of cleared lines (score) achieved in the game.
    """
    env.reset()
    agent = TetrisAgent(env, weights)
    moves = 0

    while moves < max_moves and not env.game_over:
        best_move = agent.get_best_move()
        if best_move is not None:
            for _ in range(best_move["rotations"]):
                env.rotate_piece(clockwise=True)
            env.current_piece.x = best_move["x"]
            env.hard_drop()
        else:
            env.drop_piece()
        moves += 1

    return env.score


def compute_fitness(random_weights, num_games, max_moves, env_params):
    """
    Compute the fitness for the given weight vector by simulating a number of games.

    Args:
        random_weights (np.array): The weight vector to evaluate.
        num_games (int): Number of games to simulate.
        max_moves (int): Maximum number of moves per game.
        env_params (dict): Dictionary containing environment parameters (rows, cols, piece_generator, random_seed).

    Returns:
        int: The total number of cleared lines (cumulative score) over all games.
    """
    total_lines = 0
    env = TetrisEnv(
        env_params["rows"],
        env_params["cols"],
        env_params["piece_generator"],
        env_params["random_seed"],
    )
    for _ in range(num_games):
        total_lines += simulate_tetris_game(env, random_weights, max_moves)
    return total_lines


def evolution_strategy(
        pretrained_weights,
        max_generations,
        population_size,
        sigma,
        alpha,
        num_games,
        max_moves,
        env_params,
):
    """
    Perform training using an Evolution Strategy.

    Args:
        pretrained_weights (str or Path): Path to the pretrained weight file (numpy file).
        max_generations (int): Maximum number of generations.
        population_size (int): Number of candidate weight vectors per generation.
        sigma (float): Standard deviation for noise.
        alpha (float): Learning rate.
        num_games (int): Number of games to simulate for fitness evaluation.
        max_moves (int): Maximum number of moves per game.
        env_params (dict): Environment parameters including rows, cols, piece_generator, and random_seed.

    Returns:
        tuple: (best_params, best_fitness_value, best_avg_params, best_avg_fit, best_rewards, avg_rewards)
    """
    baseline = np.load(pretrained_weights)
    best_rewards = []
    avg_rewards = []
    best_baseline = baseline.copy()
    best_fitness_value = compute_fitness(baseline, num_games, max_moves, env_params)
    best_avg_fit = -float("inf")
    best_avg_baseline = baseline.copy()

    compute_fitness_partial = partial(
        compute_fitness, num_games=num_games, max_moves=max_moves, env_params=env_params
    )
    with mp.Pool() as pool:
        for generation in range(max_generations):
            start_time = time.time()
            noise = np.random.randn(population_size, baseline.shape[0])
            candidates = baseline + sigma * noise
            candidates = candidates / np.linalg.norm(candidates, axis=1, keepdims=True)

            rewards = np.array(pool.map(compute_fitness_partial, candidates))

            mean_reward = np.mean(rewards)
            standardized_rewards = (rewards - mean_reward) / (np.std(rewards) + 1e-8)
            update = (alpha / (sigma * population_size)) * np.dot(noise.T, standardized_rewards)

            baseline += update
            baseline /= np.linalg.norm(baseline)

            current_fitness = compute_fitness(baseline, num_games, max_moves, env_params)
            if current_fitness > best_fitness_value:
                best_fitness_value = current_fitness
                best_baseline = baseline.copy()

            if mean_reward > best_avg_fit:
                best_avg_fit = mean_reward
                best_avg_baseline = baseline.copy()

            best_reward = np.max(rewards)
            generation_time = time.time() - start_time
            print(
                f"Generation {generation}: | Best Fitness = {best_reward:.2f} | Avg Fitness = {mean_reward:.2f} | Time: {generation_time:.2f}"
            )
            print(f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%")

            best_rewards.append(best_reward)
            avg_rewards.append(mean_reward)

    return best_baseline, best_fitness_value, best_avg_baseline, best_avg_fit, best_rewards, avg_rewards


if __name__ == "__main__":
    FILE_DIR = Path(__file__).parent.parent.parent
    LOG_DIR = FILE_DIR / "logs"
    start_training_time = datetime.datetime.now()
    CHECKPOINT_DIR = LOG_DIR / start_training_time.strftime("%Y_%m_%d_%H_%M")
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    TRAIN_LOGS_PATH = CHECKPOINT_DIR / "training_log.txt"
    PLOT_PATH = CHECKPOINT_DIR / "fitness_plot.png"
    BEST_SCORE = CHECKPOINT_DIR / "best.npy"
    BEST_AVG = CHECKPOINT_DIR / "best_avg.npy"
    TRAIN_CONFIG = FILE_DIR / "src" / "config" / "train_config.yaml"
    GAME_CONFIG = FILE_DIR / "src" / "config" / "game_config.yaml"

    with open(TRAIN_CONFIG, "r", encoding="utf-8") as f:
        train_config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]
    with open(GAME_CONFIG, "r", encoding="utf-8") as f:
        game_config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]

    env_params = {
        "rows": game_config["rows"],
        "cols": game_config["cols"],
        "piece_generator": game_config["generator"],
        "random_seed": game_config["seed"],
    }

    pretrained_weights = LOG_DIR / train_config["check_point"] / f"{train_config['model']}.npy"
    population_size = train_config["population"]
    num_games = train_config["games"]
    max_moves = train_config["moves"]
    max_generations = train_config["generations"]
    sigma = train_config["sigma"]
    alpha = train_config["lr"]

    print(f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%")
    print("Training in parallel...")

    training_info = f"""
        --- TRAINING PARAMETERS ---
        Time Start: {start_training_time.strftime("%Y-%m-%d %H:%M:%S")}
        WEIGHTS: {pretrained_weights}
        POPULATION_SIZE: {population_size}
        NUM_GAMES: {num_games}
        MAX_MOVES: {max_moves}
        MAX_GENERATIONS: {max_generations}
        SIGMA: {sigma}
        ALPHA: {alpha}
        GAME_MODE: {env_params["piece_generator"]}
        SEED: {env_params["random_seed"]}
    """
    with open(TRAIN_LOGS_PATH, "w", encoding="utf-8") as f:
        f.write(training_info)

    best_params, best_fit, best_avg_params, best_avg_fit, best_rewards, avg_rewards = evolution_strategy(
        pretrained_weights,
        max_generations,
        population_size,
        sigma,
        alpha,
        num_games,
        max_moves,
        env_params,
    )

    print("\nBest high score parameters:")
    print(f"AGGREGATE_HEIGHT_WEIGHT = {best_params[0]:.6f}")
    print(f"COMPLETE_LINES_WEIGHT = {best_params[1]:.6f}")
    print(f"HOLES_WEIGHT = {best_params[2]:.6f}")
    print(f"BUMPINESS_WEIGHT = {best_params[3]:.6f}")
    print(f"Fitness: {best_fit}")
    print("---------------------------------")
    print("\nBest average score parameters:")
    print(f"AGGREGATE_HEIGHT_WEIGHT = {best_avg_params[0]:.6f}")
    print(f"COMPLETE_LINES_WEIGHT = {best_avg_params[1]:.6f}")
    print(f"HOLES_WEIGHT = {best_avg_params[2]:.6f}")
    print(f"BUMPINESS_WEIGHT = {best_avg_params[3]:.6f}")
    print(f"Fitness: {best_avg_fit}")

    end_training_time = datetime.datetime.now()
    duration = end_training_time - start_training_time
    formatted_duration = str(duration).split(".")[0]
    training_results = f"""
        --- TRAINING RESULTS ---
        Time End: {end_training_time.strftime("%Y-%m-%d %H:%M:%S")}
        Training Duration: {formatted_duration}

        Best Score: {best_fit}
        Best High Score Parameters:
        AGGREGATE_HEIGHT_WEIGHT = {best_params[0]:.6f}
        COMPLETE_LINES_WEIGHT = {best_params[1]:.6f}
        HOLES_WEIGHT = {best_params[2]:.6f}
        BUMPINESS_WEIGHT = {best_params[3]:.6f}

        Best Average Score: {best_avg_fit:.6f}
        Best Average Score Parameters:
        AGGREGATE_HEIGHT_WEIGHT = {best_avg_params[0]:.6f}
        COMPLETE_LINES_WEIGHT = {best_avg_params[1]:.6f}
        HOLES_WEIGHT = {best_avg_params[2]:.6f}
        BUMPINESS_WEIGHT = {best_avg_params[3]:.6f}
    """
    with open(TRAIN_LOGS_PATH, "a", encoding="utf-8") as f:
        f.write(training_results)

    print(f"Training logs saved in {TRAIN_LOGS_PATH}")

    np.save(BEST_SCORE, best_params)
    print("Best weights saved at {}".format(BEST_SCORE))
    np.save(BEST_AVG, best_avg_params)
    print("Best weights saved at {}".format(BEST_AVG))

    plt.figure(figsize=(10, 5))
    plt.plot(range(max_generations), best_rewards, label="Best Fitness", marker="o", markersize=3)
    plt.plot(range(max_generations), avg_rewards, label="Average Fitness", linestyle="--")
    plt.xlabel("Generation")
    plt.ylabel("Fitness")
    plt.title("Evolution Strategy Training Progress")
    plt.legend()
    plt.grid(True)
    plt.savefig(PLOT_PATH)
    plt.close()
    print(f"Fitness plot saved at {PLOT_PATH}")
