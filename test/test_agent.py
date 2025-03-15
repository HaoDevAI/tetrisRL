import numpy as np
import pygame
import sys
import time
import threading
from src.environments.env import TetrisEnv
from src.agents.linear_agent import TetrisAgent
from pathlib import Path
import yaml

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

# Derived UI variables
BLOCK_SIZE = ui_config["block_size"]
ROWS = env_params["rows"]
COLUMNS = env_params["cols"]
WIDTH = COLUMNS * BLOCK_SIZE
HEIGHT = ROWS * BLOCK_SIZE
PANEL_WIDTH = ui_config["panel_width"]
PANEL_MARGIN = ui_config["panel_margin"]
SCREEN_WIDTH = WIDTH + PANEL_WIDTH + PANEL_MARGIN * 2
SCREEN_HEIGHT = HEIGHT
NUM_GAMES = 0  # Background games for agent's evaluation

# Global variables for background simulation
max_background_score = 0
min_background_score = float('inf')
max_background_moves = 0
total_background_score = 0
total_background_moves = 0
games_played = 0
simulation_finished = False
score_lock = threading.Lock()


def draw_block_3d(screen, color, x, y):
    """
    Draw a 3D-styled block at the given grid coordinates.

    Args:
        screen (pygame.Surface): The game screen surface.
        color (tuple): RGB color tuple for the block.
        x (int): X-coordinate (column index).
        y (int): Y-coordinate (row index).
    """
    rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, ui_config["border"], rect, ui_config["border_width"])


def draw_grid(screen, board):
    """
    Draw the Tetris grid and any placed blocks on the board.

    Args:
        screen (pygame.Surface): The game screen surface.
        board (list[list]): 2D list representing the game board.
    """
    for y in range(ROWS):
        for x in range(COLUMNS):
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(screen, ui_config["grid"], rect, ui_config["grid_width"])
            if board[y][x]:
                draw_block_3d(screen, board[y][x], x, y)


def draw_piece(screen, cells, color):
    """
    Draw a Tetris piece given its cell coordinates and color.

    Args:
        screen (pygame.Surface): The game screen surface.
        cells (list[tuple]): List of (x, y) tuples for the piece's cells.
        color (tuple): RGB color tuple for the piece.
    """
    for (x, y) in cells:
        draw_block_3d(screen, color, x, y)


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

    next_text = font.render("Next Piece:", True, ui_config["text"])
    screen.blit(next_text, (panel_rect.x + 10, panel_rect.y + 10))

    next_piece = env.next_piece
    temp_piece = next_piece.clone()
    temp_piece.x = 0
    temp_piece.y = 0
    piece_height = len(temp_piece.matrix)
    piece_width = len(temp_piece.matrix[0])
    offset_x = panel_rect.x + (PANEL_WIDTH - piece_width * BLOCK_SIZE) // 2
    offset_y = panel_rect.y + 40
    for i, row in enumerate(temp_piece.matrix):
        for j, val in enumerate(row):
            if val:
                rect = pygame.Rect(offset_x + j * BLOCK_SIZE, offset_y + i * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(screen, temp_piece.color, rect)

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

    version_text = font.render(f"Version: {VERSION}", True, ui_config["text"])
    screen.blit(version_text, (panel_rect.x + 10, panel_rect.y + 600))


def check_play_again(screen, font, final_score):
    """
    Display a game over overlay with the final score and Yes/No buttons.
    Returns True if the player chooses to play again, False otherwise.

    Args:
        screen (pygame.Surface): The game screen surface.
        font (pygame.font.Font): The font used for rendering text.
        final_score (int): The final score of the game.

    Returns:
        bool: True if player clicks Yes, False if No.
    """
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(ui_config["background"])
    screen.blit(overlay, (0, 0))

    game_over_text = font.render("Game Over!", True, ui_config["text"])
    score_text = font.render(f"Score: {final_score}", True, ui_config["text"])
    play_again_text = font.render("Play again?", True, ui_config["text"])

    center_x = SCREEN_WIDTH // 2
    game_over_rect = game_over_text.get_rect(center=(center_x, SCREEN_HEIGHT // 2 - 100))
    score_rect = score_text.get_rect(center=(center_x, SCREEN_HEIGHT // 2 - 50))
    play_again_rect = play_again_text.get_rect(center=(center_x, SCREEN_HEIGHT // 2))

    screen.blit(game_over_text, game_over_rect)
    screen.blit(score_text, score_rect)
    screen.blit(play_again_text, play_again_rect)

    button_width = 100
    button_height = 50
    spacing = 20

    yes_button_rect = pygame.Rect(
        center_x - button_width - spacing // 2,
        SCREEN_HEIGHT // 2 + 50,
        button_width,
        button_height
    )
    no_button_rect = pygame.Rect(
        center_x + spacing // 2,
        SCREEN_HEIGHT // 2 + 50,
        button_width,
        button_height
    )

    yes_text = font.render("Yes", True, ui_config["text"])
    no_text = font.render("No", True, ui_config["text"])

    waiting = True
    while waiting:
        screen.blit(overlay, (0, 0))
        screen.blit(game_over_text, game_over_rect)
        screen.blit(score_text, score_rect)
        screen.blit(play_again_text, play_again_rect)

        mouse_pos = pygame.mouse.get_pos()
        yes_color = ui_config["button_hover"] if yes_button_rect.collidepoint(mouse_pos) else ui_config["button_bg"]
        no_color = ui_config["button_hover"] if no_button_rect.collidepoint(mouse_pos) else ui_config["button_bg"]

        pygame.draw.rect(screen, yes_color, yes_button_rect)
        pygame.draw.rect(screen, no_color, no_button_rect)

        yes_text_rect = yes_text.get_rect(center=yes_button_rect.center)
        no_text_rect = no_text.get_rect(center=no_button_rect.center)
        screen.blit(yes_text, yes_text_rect)
        screen.blit(no_text, no_text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if yes_button_rect.collidepoint(event.pos):
                    return True
                elif no_button_rect.collidepoint(event.pos):
                    return False


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
            f"Version: {VERSION}\n"
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