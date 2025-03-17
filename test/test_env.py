"""
Module: test_env.py

This module provides a user interface for running and testing the Tetris game.
It loads configuration settings from a YAML file, groups environment and UI parameters
into dictionaries (env_params and ui_config), and sets up the Pygame display for gameplay.
The module includes functions to draw game elements (blocks, pieces, grid, panel, ghost piece)
and handles user input to control the Tetris game.
"""
import numpy as np
import pygame
from src.environments.env import TetrisEnv
from src.agents.reward import *
from utils.UI import *

# === Agent setup ===
AGENT = "ref"
VERSION = "best"
AGENT_DIR = FILE_DIR / 'logs' / AGENT
WEIGHTS_PATH = AGENT_DIR / f"{VERSION}.npy"
agent_weights = np.load(WEIGHTS_PATH)

def draw_panel(screen, env, font):
    """
    Draw the side panel displaying the next piece and the current score.

    Args:
        screen (pygame.Surface): The game screen surface.
        env (TetrisEnv): The current Tetris game environment.
        font (pygame.font.Font): Font for rendering text.
    """
    panel_rect = pygame.Rect(WIDTH + PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH, HEIGHT - PANEL_MARGIN * 2)
    pygame.draw.rect(screen, ui_config["panel_bg_color"], panel_rect)

    # Next Piece preview.
    draw_next_piece(screen, env, panel_rect, font)

    score_text = font.render(f"Lines: {env.score}", True, ui_config["text_color"])
    screen.blit(score_text, (panel_rect.x + 10, panel_rect.y + 150))

    y_offset = panel_rect.y + 150

    board = env.grid.board
    rows, cols = env.grid.rows, env.grid.cols
    heights = compute_column_heights(board, rows, cols)
    agg_height = compute_aggregate_height(heights)
    holes = compute_holes(board, rows, cols)
    bumpiness = compute_bumpiness(heights)
    reward = evaluate_state(env,agent_weights)

    y_offset += 40
    agg_text = font.render(f"Aggregate: {agg_height}", True, ui_config["text_color"])
    screen.blit(agg_text, (panel_rect.x + 10, y_offset))

    # Display holes count
    y_offset += 40
    holes_text = font.render(f"Holes: {holes}", True, ui_config["text_color"])
    screen.blit(holes_text, (panel_rect.x + 10, y_offset))

    # Display bumpiness
    y_offset += 40
    bump_text = font.render(f"Bumpiness: {bumpiness}", True, ui_config["text_color"])
    screen.blit(bump_text, (panel_rect.x + 10, y_offset))

    y_offset += 40
    reward_text = font.render(f"Reward: {reward}", True, ui_config["text_color"])
    screen.blit(reward_text, (panel_rect.x + 10, y_offset))

def main():
    """
    Main function to initialize Pygame, set up the Tetris game, and run the game loop.

    It handles user inputs for controlling the game, updates game state, draws game elements,
    and manages game over conditions.
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris AI with Pygame")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    running = True
    while running:
        env = TetrisEnv(
            env_params["rows"],
            env_params["cols"],
            env_params["piece_generator"],
            env_params["random_seed"]
        )
        drop_interval = ui_config["drop_interval"]
        DROP_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(DROP_EVENT, drop_interval)

        game_active = True
        while game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_active = False
                    running = False
                elif event.type == DROP_EVENT:
                    env.drop_piece()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        env.move_piece(-1, 0)
                    elif event.key == pygame.K_d:
                        env.move_piece(1, 0)
                    elif event.key == pygame.K_s:
                        env.move_piece(0, 1)
                    elif event.key == pygame.K_w:
                        env.hard_drop()
                    elif event.key == pygame.K_q:
                        env.rotate_piece(clockwise=False)
                    elif event.key == pygame.K_e:
                        env.rotate_piece(clockwise=True)

            screen.fill(ui_config["background_color"])
            draw_grid(screen, env.grid.board)
            ghost_piece = env.get_ghost_piece()
            draw_ghost_piece(screen, ghost_piece)
            draw_piece(screen, env.current_piece.get_cells(), env.current_piece.color)
            draw_panel(screen, env, font)
            pygame.display.flip()

            if env.game_over:
                game_active = False

            clock.tick(ui_config["fps"])

        play_again = check_play_again(screen, font, env.score)
        if not play_again:
            running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
