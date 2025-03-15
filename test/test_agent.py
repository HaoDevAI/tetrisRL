import numpy as np
import pygame
import time
import threading
from src.environments.env import TetrisEnv
from src.agents.tetris_agent import TetrisAgent
from utils.UI import *
# Agent information and file paths
AGENT = "ref"
VERSION = "best"

FILE_DIR = Path(__file__).parent.parent
CONFIG_PATH = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
AGENT_DIR = FILE_DIR / 'logs' / AGENT
WEIGHTS_PATH = AGENT_DIR / f"{VERSION}.npy"
TEST_LOGS_PATH = AGENT_DIR / 'test_results.txt'
SAVE_MODE = False

# Load game config
with open(CONFIG_PATH, 'r') as f:
    config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]

#Agent strategy
AGENT_STRATEGY = config['strategy']

# Group environment configuration
env_params = {
    "piece_generator": config["generator"],
    "random_seed": config["seed"],
    "rows": config["rows"],
    "cols": config["cols"]
}

# Group UI configuration
ui_config = {
    "fps": config["fps"],
    "delay": config["delay"],
    "drop_interval": int(config["drop_interval"]/10),
    "block_size": config["block_size"],
    "panel_width": 8 * config["block_size"],
    "panel_margin": 10,
    "background": config["background"],
    "border": config["border"],
    "border_width": config["border_w"],
    "grid": config["grid"],
    "grid_width": config["grid_w"],
    "panel_bg": config["panel"],
    "text": config["text"],
    "button_bg": config["button_bg"],
    "button_hover": config["button_hover"]
}


NUM_GAMES = 7  # Background games for agent's evaluation

# Global variables for background simulation
max_background_score = 0
min_background_score = float('inf')
max_background_moves = 0
total_background_score = 0
total_background_moves = 0
games_played = 0
simulation_finished = False
score_lock = threading.Lock()

def draw_panel(screen, env, font):
    """
    Draw the side panel including next piece, current score, and background simulation statistics.

    Args:
        screen (pygame.Surface): The game screen surface.
        env (TetrisEnv): The current Tetris game environment.
        font (pygame.font.Font): The font used for rendering text.
    """
    panel_rect = pygame.Rect(WIDTH + PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH, HEIGHT - PANEL_MARGIN * 2)
    pygame.draw.rect(screen, ui_config["panel_bg"], panel_rect)

    # Next Piece preview.
    draw_next_piece(screen, env, panel_rect, font)

    score_text = font.render(f"Score: {env.score}", True, ui_config["text"])
    screen.blit(score_text, (panel_rect.x + 10, panel_rect.y + 150))

    with score_lock:
        bg_max = max_background_score
        bg_min = min_background_score if games_played > 0 else 0
        bg_max_moves = max_background_moves
        progress = games_played
        avg_score = total_background_score / games_played if games_played > 0 else 0
        avg_moves = total_background_moves / games_played if games_played > 0 else 0

    moves_text = font.render(f"Moves: {env.moves_played}", True, ui_config["text"])
    screen.blit(moves_text, (panel_rect.x + 10, panel_rect.y + 200))

    progress_text = font.render(f"Progress: {progress}/{NUM_GAMES}", True, ui_config["text"])
    screen.blit(progress_text, (panel_rect.x + 10, panel_rect.y + 500))

    avg_score_text = font.render(f"Avg score: {avg_score:.2f}", True, ui_config["text"])
    screen.blit(avg_score_text, (panel_rect.x + 10, panel_rect.y + 350))

    avg_moves_text = font.render(f"Avg moves: {avg_moves:.2f}", True, ui_config["text"])
    screen.blit(avg_moves_text, (panel_rect.x + 10, panel_rect.y + 400))

    max_text = font.render(f"Max: {bg_max}", True, ui_config["text"])
    screen.blit(max_text, (panel_rect.x + 10, panel_rect.y + 250))

    min_text = font.render(f"Min: {bg_min}", True, ui_config["text"])
    screen.blit(min_text, (panel_rect.x + 10, panel_rect.y + 300))

    max_moves_text = font.render(f"Max Moves: {bg_max_moves}", True, ui_config["text"])
    screen.blit(max_moves_text, (panel_rect.x + 10, panel_rect.y + 450))

    agent_text = font.render(f"Agent: {AGENT}", True, ui_config["text"])
    screen.blit(agent_text, (panel_rect.x + 10, panel_rect.y + 550))

    version_text = font.render(f"Strategy: {AGENT_STRATEGY}", True, ui_config["text"])
    screen.blit(version_text, (panel_rect.x + 10, panel_rect.y + 600))

def run_background_games():
    """
    Run background simulations of NUM_GAMES Tetris games using the agent.
    Updates global statistics for background simulation.
    """
    global max_background_score, min_background_score, max_background_moves
    global total_background_score, total_background_moves, games_played, simulation_finished
    load_weights = np.load(WEIGHTS_PATH)
    env = TetrisEnv(env_params["rows"], env_params["cols"],
                    generator=env_params["piece_generator"], seed=env_params["random_seed"])

    for game_index in range(NUM_GAMES):
        env.reset()
        agent = TetrisAgent(env, load_weights)
        game_active = True

        while game_active:
            best_move = None
            if AGENT_STRATEGY == "normal":
                best_move = agent.get_best_move()
            elif AGENT_STRATEGY == "promax":
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
            if env.game_over:
                game_active = False
                with score_lock:
                    games_played = game_index + 1
                    total_background_score += env.score
                    total_background_moves += env.moves_played
                    if env.score > max_background_score:
                        max_background_score = env.score
                    if env.score < min_background_score:
                        min_background_score = env.score
                    if env.moves_played > max_background_moves:
                        max_background_moves = env.moves_played
    simulation_finished = True


def main():
    """
    Main function to run the Tetris agent UI and background simulation.
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris AI Agent")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    sim_thread = threading.Thread(target=run_background_games, daemon=True)
    sim_thread.start()

    env = TetrisEnv(env_params["rows"], env_params["cols"],
                    generator=env_params["piece_generator"], seed=env_params["random_seed"])
    load_weights = np.load(WEIGHTS_PATH)
    pygame.time.set_timer(pygame.USEREVENT + 1, ui_config["drop_interval"])
    running = True

    while running:
        env.reset()
        agent = TetrisAgent(env, load_weights)
        game_active = True
        last_move_time = time.time()

        while game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_active = False
                    running = False
                elif event.type == pygame.USEREVENT + 1:
                    if (time.time() - last_move_time) > ui_config["delay"]:
                        best_move = None
                        if AGENT_STRATEGY == "normal":
                            best_move = agent.get_best_move()
                        elif AGENT_STRATEGY == "promax":
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
                        last_move_time = time.time()

            screen.fill(ui_config["background"])
            draw_grid(screen, env.grid.board)
            draw_piece(screen, env.current_piece.get_cells(), env.current_piece.color)
            draw_panel(screen, env, font)
            pygame.display.flip()

            if env.game_over:
                play_again = check_play_again(screen, font, env.score)
                if play_again:
                    game_active = False  # Restart game
                else:
                    running = False
                    game_active = False

            clock.tick(ui_config["fps"])

    pygame.quit()

    with score_lock:
        avg_score = total_background_score / games_played if games_played > 0 else 0
        avg_moves = total_background_moves / games_played if games_played > 0 else 0
        min_score = min_background_score if games_played > 0 else 0
        logs = (
            "Simulation finished:\n"
            f"Agent: {AGENT}\n"
            f"Strategy: {AGENT_STRATEGY}\n"
            f"Mode: {env_params['piece_generator']}\n"
            f"Progress: {games_played}/{NUM_GAMES}\n"
            f"Max Score: {max_background_score}\n"
            f"Min Score: {min_score}\n"
            f"Average Score: {avg_score:.2f}\n"
            f"Average moves: {avg_moves:.2f}\n"
            f"Max Moves: {max_background_moves}\n"
        )

        print(logs)
        if SAVE_MODE:
            with open(TEST_LOGS_PATH, "a") as log_file:
                log_file.write(logs + "\n")


if __name__ == "__main__":
    main()