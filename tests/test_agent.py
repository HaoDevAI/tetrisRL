import numpy as np
import pygame
import time
import threading
from pathlib import Path
import yaml
from concurrent.futures import ProcessPoolExecutor, as_completed

from src.environments.env import TetrisEnv
from src.agents.agent import TetrisAgent
from src.utils.display import draw_grid, draw_piece, draw_next_piece, check_play_again
from src.utils.config import ui_config, SCREEN_WIDTH, SCREEN_HEIGHT, env_params, WIDTH, HEIGHT, PANEL_MARGIN, PANEL_WIDTH

# Agent information and file paths
AGENT_NAME = "base"
FILE_DIR = Path(__file__).parent.parent
CONFIG_PATH = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
AGENT_DIR = FILE_DIR / 'logs' / AGENT_NAME
VERSION = "best"
WEIGHTS_PATH = AGENT_DIR / f"{VERSION}.npy"
TEST_LOGS_PATH = AGENT_DIR / 'test_results.txt'
SAVE_MODE = False

# Load game config
with open(CONFIG_PATH, 'r') as f:
    config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]
STRATEGY = config['strategy']
NUM_SIMULATION_GAMES = 20  # Number of background simulation games

# Global simulation statistics
max_score = 0
min_score = float('inf')
max_moves = 0
total_score = 0
total_moves = 0
games_completed = 0
simulation_finished = False
score_lock = threading.Lock()


def draw_agent_panel(screen, env, font):
    """
    Draw the side panel including the next piece preview, current score,
    moves played, and background simulation statistics.
    """
    panel_rect = pygame.Rect(WIDTH + PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH + 50, HEIGHT - 2 * PANEL_MARGIN)
    pygame.draw.rect(screen, ui_config["panel_bg_color"], panel_rect)

    # Draw the next piece preview at the top of the panel.
    draw_next_piece(screen, env, panel_rect, font)

    y_offset = panel_rect.y + 120  # Adjust offset after next piece preview
    current_score_text = font.render(f"Score: {env.score}", True, ui_config["text_color"])
    screen.blit(current_score_text, (panel_rect.x + 10, y_offset))
    y_offset += 40

    moves_text = font.render(f"Moves: {env.moves_played}", True, ui_config["text_color"])
    screen.blit(moves_text, (panel_rect.x + 10, y_offset))
    y_offset += 40

    with score_lock:
        progress_text = font.render(f"Progress: {games_completed}/{NUM_SIMULATION_GAMES}", True,
                                    ui_config["text_color"])
        avg_score = total_score / games_completed if games_completed > 0 else 0
        avg_moves = total_moves / games_completed if games_completed > 0 else 0
        max_score_text = font.render(f"Max Score: {max_score}", True, ui_config["text_color"])
        min_score_text = font.render(f"Min Score: {min_score if games_completed > 0 else 0}", True,
                                     ui_config["text_color"])
        max_moves_text = font.render(f"Max Moves: {max_moves}", True, ui_config["text_color"])
        avg_score_text = font.render(f"Avg Score: {avg_score:.2f}", True, ui_config["text_color"])
        avg_moves_text = font.render(f"Avg Moves: {avg_moves:.2f}", True, ui_config["text_color"])

    screen.blit(progress_text, (panel_rect.x + 10, y_offset))
    y_offset += 40
    screen.blit(avg_score_text, (panel_rect.x + 10, y_offset))
    y_offset += 40
    screen.blit(avg_moves_text, (panel_rect.x + 10, y_offset))
    y_offset += 40
    screen.blit(max_score_text, (panel_rect.x + 10, y_offset))
    y_offset += 40
    screen.blit(min_score_text, (panel_rect.x + 10, y_offset))
    y_offset += 40
    screen.blit(max_moves_text, (panel_rect.x + 10, y_offset))
    y_offset += 40

    agent_text = font.render(f"Agent: {AGENT_NAME}", True, ui_config["text_color"])
    screen.blit(agent_text, (panel_rect.x + 10, y_offset))
    y_offset += 40
    strategy_text = font.render(f"Agent mode: {STRATEGY}", True, ui_config["text_color"])
    screen.blit(strategy_text, (panel_rect.x + 10, y_offset))
    y_offset += 40
    game_text = font.render(f"Game mode: {env_params["piece_generator"]}", True, ui_config["text_color"])
    screen.blit(game_text, (panel_rect.x + 10, y_offset))


def simulate_single_game(game_index):
    """
    Simulate a single Tetris game and return its final score and moves.

    Args:
        game_index (int): The simulation game index (unused, for differentiation).

    Returns:
        tuple: (score, moves_played)
    """
    # Import local versions of the modules to avoid issues with multiprocessing
    from src.environments.env import TetrisEnv
    from src.agents.agent import TetrisAgent

    weights = np.load(str(WEIGHTS_PATH))
    env_sim = TetrisEnv(env_params["rows"], env_params["cols"],
                        env_params["piece_generator"], env_params["random_seed"])
    agent_sim = TetrisAgent(env_sim, weights, mode=STRATEGY)
    while not env_sim.game_over:
        best_move = agent_sim.get_best_move()
        if best_move is not None:
            for _ in range(best_move["rotations"]):
                env_sim.rotate_piece(clockwise=True)
            env_sim.current_piece.x = best_move["x"]
            env_sim.hard_drop()
            env_sim.moves_played += 1
        else:
            env_sim.drop_piece()
            env_sim.moves_played += 1
    return (env_sim.score, env_sim.moves_played)


def run_simulation_games():
    """
    Run NUM_SIMULATION_GAMES Tetris simulations concurrently using multiple processes.
    Update global statistics as each simulation completes.
    """
    global max_score, min_score, max_moves, total_score, total_moves, games_completed, simulation_finished

    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(simulate_single_game, i) for i in range(NUM_SIMULATION_GAMES)]
        for future in as_completed(futures):
            result = future.result()  # (score, moves_played)
            with score_lock:
                games_completed += 1
                score, moves = result
                total_score += score
                total_moves += moves
                if score > max_score:
                    max_score = score
                if score < min_score:
                    min_score = score
                if moves > max_moves:
                    max_moves = moves
    simulation_finished = True


def main():
    """
    Main function to run the Tetris agent UI and background simulation.
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH + 50, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris AI Agent")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    # Start background simulation using multiprocessing (runs in a separate thread)
    simulation_thread = threading.Thread(target=run_simulation_games, daemon=True)
    simulation_thread.start()

    weights = np.load(str(WEIGHTS_PATH))
    env = TetrisEnv(env_params["rows"], env_params["cols"],
                    env_params["piece_generator"], env_params["random_seed"])
    agent = TetrisAgent(env, weights, mode=STRATEGY)

    # Set timer for agent moves; timer interval taken from configuration
    TIMER_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(TIMER_EVENT, int(ui_config["drop_interval"] / 10))

    running = True
    while running:
        env.reset()
        agent = TetrisAgent(env, weights, mode=STRATEGY)
        game_active = True
        last_move_time = time.time()

        while game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_active = False
                    running = False
                elif event.type == TIMER_EVENT:
                    if time.time() - last_move_time > ui_config["agent_delay"]:
                        best_move = agent.get_best_move()
                        if best_move is not None:
                            for _ in range(best_move["rotations"]):
                                env.rotate_piece(clockwise=True)
                            env.current_piece.x = best_move["x"]
                            env.hard_drop()
                            env.moves_played += 1
                        else:
                            env.drop_piece()
                            env.moves_played += 1
                        last_move_time = time.time()
            screen.fill(ui_config["background_color"])
            draw_grid(screen, env.grid.board)
            draw_piece(screen, env.current_piece.get_cells(), env.current_piece.color)
            draw_agent_panel(screen, env, font)
            pygame.display.flip()

            if env.game_over:
                if check_play_again(screen, font, env.score):
                    game_active = False  # Restart game
                else:
                    running = False
                    game_active = False

            clock.tick(ui_config["fps"])

    pygame.quit()

    with score_lock:
        avg_score = total_score / games_completed if games_completed > 0 else 0
        avg_moves = total_moves / games_completed if games_completed > 0 else 0
        min_sc = min_score if games_completed > 0 else 0
        log_results = (
            "Simulation finished:\n"
            f"Agent: {AGENT_NAME}\n"
            f"Agent mode: {STRATEGY}\n"
            f"Game Mode: {env_params['piece_generator']}\n"
            f"Random seed: {env_params['random_seed']}\n"
            f"Games Completed: {games_completed}/{NUM_SIMULATION_GAMES}\n"
            f"Max Score: {max_score}\n"
            f"Min Score: {min_sc}\n"
            f"Average Score: {avg_score:.2f}\n"
            f"Average Moves: {avg_moves:.2f}\n"
            f"Max Moves: {max_moves}\n"
            f"_____________________________"
        )
        print(log_results)
        if SAVE_MODE:
            with open(TEST_LOGS_PATH, "a") as log_file:
                log_file.write(log_results + "\n")


if __name__ == "__main__":
    main()
