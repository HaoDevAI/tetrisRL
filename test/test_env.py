"""
Module: test_env.py

This module provides a user interface for running and testing the Tetris game.
It loads configuration settings from a YAML file, groups environment and UI parameters
into dictionaries (env_params and ui_config), and sets up the Pygame display for gameplay.
The module includes functions to draw game elements (blocks, pieces, grid, panel, ghost piece)
and handles user input to control the Tetris game.
"""

import sys
import pygame
from src.environments.env import TetrisEnv
from src.agents.policy import *
from pathlib import Path
import yaml

# File path
FILE_DIR = Path(__file__).parent.parent
CONFIG = FILE_DIR / 'src' / 'config' / 'game_config.yaml'

# Load game config
with open(CONFIG, 'r') as f:
    config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]

# Environment configuration (similar to es_multi.py)
env_params = {
    "piece_generator": config["generator"],
    "random_seed": config["seed"],
    "rows": config["rows"],
    "cols": config["cols"]
}

# UI configuration
ui_config = {
    "fps": config["fps"],
    "drop_interval": config["drop_interval"],
    "block_size": config["block_size"],
    "panel_width": 6 * config["block_size"],
    "panel_margin": 12,
    "background_color": config["background"],
    "border_color": config["border"],
    "border_width": config["border_w"],
    "grid_color": config["grid"],
    "grid_width": config["grid_w"],
    "panel_bg_color": config["panel"],
    "text_color": config["text"],
    "button_bg_color": config["button_bg"],
    "button_hover_color": config["button_hover"]
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
    pygame.draw.rect(screen, ui_config["border_color"], rect, ui_config["border_width"])


def draw_piece(screen, cells, color):
    """
    Draw a Tetris piece using the provided cell coordinates and color.

    Args:
        screen (pygame.Surface): The game screen surface.
        cells (list of tuple): List of (x, y) tuples representing cell positions.
        color (tuple): RGB color tuple for the piece.
    """
    for (x, y) in cells:
        draw_block_3d(screen, color, x, y)


def draw_grid(screen, board):
    """
    Draw the game grid along with any placed blocks.

    Args:
        screen (pygame.Surface): The game screen surface.
        board (list of list): 2D list representing the game board.
    """
    for y in range(ROWS):
        for x in range(COLUMNS):
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(screen, ui_config["grid_color"], rect, 1)
            if board[y][x]:
                draw_block_3d(screen, board[y][x], x, y)


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

    next_text = font.render("Next Piece:", True, ui_config["text_color"])
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

    score_text = font.render(f"Lines: {env.score}", True, ui_config["text_color"])
    screen.blit(score_text, (panel_rect.x + 10, panel_rect.y + 150))

    y_offset = panel_rect.y + 150

    board = env.grid.board
    rows, cols = env.grid.rows, env.grid.cols
    heights = compute_column_heights(board, rows, cols)
    agg_height = compute_aggregate_height(heights)
    holes = compute_holes(board, rows, cols)
    bumpiness = compute_bumpiness(heights)

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


def draw_ghost_piece(screen, ghost_piece):
    """
    Draw a ghost (shadow) piece with transparency indicating where the current piece will land.

    Args:
        screen (pygame.Surface): The game screen surface.
        ghost_piece (Piece): The ghost piece instance.
    """
    ghost_color = (ghost_piece.color[0], ghost_piece.color[1], ghost_piece.color[2], 100)
    for (x, y) in ghost_piece.get_cells():
        ghost_cell = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        ghost_cell.fill(ghost_color)
        screen.blit(ghost_cell, (x * BLOCK_SIZE, y * BLOCK_SIZE))


def check_play_again(screen, font, final_score):
    """
    Display a game over screen with final score and Yes/No buttons for replay.

    Args:
        screen (pygame.Surface): The game screen surface.
        font (pygame.font.Font): Font for rendering text.
        final_score (int): The final score achieved in the game.

    Returns:
        bool: True if the player chooses to play again, False otherwise.
    """
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(ui_config["background_color"])
    screen.blit(overlay, (0, 0))

    game_over_text = font.render("Game Over!", True, ui_config["text_color"])
    score_text = font.render(f"Score: {final_score}", True, ui_config["text_color"])
    play_again_text = font.render("Play again?", True, ui_config["text_color"])

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

    yes_text = font.render("Yes", True, ui_config["text_color"])
    no_text = font.render("No", True, ui_config["text_color"])

    waiting = True
    while waiting:
        screen.blit(overlay, (0, 0))
        screen.blit(game_over_text, game_over_rect)
        screen.blit(score_text, score_rect)
        screen.blit(play_again_text, play_again_rect)

        mouse_pos = pygame.mouse.get_pos()
        yes_color = ui_config["button_hover_color"] if yes_button_rect.collidepoint(mouse_pos) else ui_config[
            "button_bg_color"]
        no_color = ui_config["button_hover_color"] if no_button_rect.collidepoint(mouse_pos) else ui_config[
            "button_bg_color"]

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
