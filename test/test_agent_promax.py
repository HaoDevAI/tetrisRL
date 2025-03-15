import numpy as np
import time
import os
from src.environments.env import TetrisEnv
from src.agents.tetris_agent import TetrisAgent
from pathlib import Path
import yaml

# Thông tin agent và đường dẫn file
AGENT = "ref"
VERSION = "best"
FILE_DIR = Path(__file__).parent.parent
CONFIG_PATH = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
AGENT_DIR = FILE_DIR / 'logs' / AGENT
WEIGHTS_PATH = AGENT_DIR / f"{VERSION}.npy"

# Load cấu hình game
with open(CONFIG_PATH, 'r') as f:
    config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]

# Cấu hình môi trường
env_params = {
    "piece_generator": config["generator"],
    "random_seed": None,
    "rows": config["rows"],
    "cols": config["cols"]
}


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def main():
    load_weights = np.load(WEIGHTS_PATH)
    env = TetrisEnv(env_params["rows"], env_params["cols"],
                    generator=env_params["piece_generator"],
                    seed=env_params["random_seed"])
    agent = TetrisAgent(env, load_weights)

    last_print_time = time.time()

    # Vòng lặp chạy game liên tục cho đến khi game kết thúc (env.game_over == True)
    while not env.game_over:
        best_move = agent.get_best_move_promax()
        if best_move is not None:
            for _ in range(best_move["rotations"]):
                env.rotate_piece(clockwise=True)
            env.current_piece.x = best_move["x"]
            env.hard_drop()
            env.moves_played += 1
        else:
            env.drop_piece()
            env.moves_played += 1

        # In kết quả chỉ mỗi 1 giây mà không làm chậm vòng lặp của agent
        current_time = time.time()
        if current_time - last_print_time >= 1:
            clear_screen()
            print(f"Score: {env.score}, Moves: {env.moves_played}")
            last_print_time = current_time

    clear_screen()
    print("Game Over!")
    print(f"Final Score: {env.score}, Total Moves: {env.moves_played}")


if __name__ == "__main__":
    main()
