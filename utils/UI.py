from pathlib import Path
import yaml
import pygame
import sys

# Load game config
FILE_DIR = Path(__file__).parent.parent
CONFIG = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
with open(CONFIG, 'r') as f:
    config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]

env_params = {
    "piece_generator": config["generator"],
    "random_seed": config["seed"],
    "rows": config["rows"],
    "cols": config["cols"]
}
# UI configuration
ui_config = {
    "fps": config["fps"],
    "agent_delay": config["delay"],
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

def adjust_color(color, factor):
    """ Adjust color brightness """
    return tuple(max(0, min(255, int(c * factor))) for c in color)

def draw_block_3d(screen, color, x, y):
    """
    Draw a 3D-styled block at the given grid coordinates.

    Args:
        screen (pygame.Surface): The game screen surface.
        color (tuple): RGB color tuple for the block.
        x (int): X-coordinate (column index).
        y (int): Y-coordinate (row index).
    """
    px, py = x * BLOCK_SIZE, y * BLOCK_SIZE
    edge = 6

    light_color = adjust_color(color, 1.3)
    dark_color = adjust_color(color, 0.6)

    pygame.draw.polygon(screen, light_color, [
        (px, py), (px + BLOCK_SIZE, py), (px + BLOCK_SIZE - edge, py + edge), (px + edge, py + edge)
    ])

    pygame.draw.polygon(screen, light_color, [
        (px, py), (px, py + BLOCK_SIZE), (px + edge, py + BLOCK_SIZE - edge), (px + edge, py + edge)
    ])

    pygame.draw.polygon(screen, dark_color, [
        (px + BLOCK_SIZE, py), (px + BLOCK_SIZE, py + BLOCK_SIZE),
        (px + BLOCK_SIZE - edge, py + BLOCK_SIZE - edge), (px + BLOCK_SIZE - edge, py + edge)
    ])

    pygame.draw.polygon(screen, dark_color, [
        (px, py + BLOCK_SIZE), (px + BLOCK_SIZE, py + BLOCK_SIZE),
        (px + BLOCK_SIZE - edge, py + BLOCK_SIZE - edge), (px + edge, py + BLOCK_SIZE - edge)
    ])

    pygame.draw.polygon(screen, color, [
        (px + edge, py + edge), (px + BLOCK_SIZE - edge, py + edge),
        (px + BLOCK_SIZE - edge, py + BLOCK_SIZE - edge), (px + edge, py + BLOCK_SIZE - edge)
    ])

    pygame.draw.line(screen, (0, 0, 0), (px, py), (px + BLOCK_SIZE, py), 2)  # Viền trên
    pygame.draw.line(screen, (0, 0, 0), (px, py), (px, py + BLOCK_SIZE), 2)  # Viền trái
    pygame.draw.line(screen, (0, 0, 0), (px, py + BLOCK_SIZE), (px + BLOCK_SIZE, py + BLOCK_SIZE), 2)  # Viền dưới
    pygame.draw.line(screen, (0, 0, 0), (px + BLOCK_SIZE, py), (px + BLOCK_SIZE, py + BLOCK_SIZE), 2)  # Viền phải

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

def draw_next_piece(screen,env,panel_rect,font):
    next_text = font.render("Next Piece:", True, ui_config["text_color"])
    screen.blit(next_text, (panel_rect.x + 10, panel_rect.y + 10))
    next_piece = env.next_piece
    temp_piece = next_piece.clone()
    temp_piece.x = 0
    temp_piece.y = 0
    piece_height = len(temp_piece.matrix)
    piece_width = len(temp_piece.matrix[0])
    offset_x = panel_rect.x + (PANEL_WIDTH - piece_width * BLOCK_SIZE) // 2
    offset_y = panel_rect.y + 50
    for i, row in enumerate(temp_piece.matrix):
        for j, val in enumerate(row):
            if val:
                draw_block_3d(screen, temp_piece.color, offset_x // BLOCK_SIZE + j, offset_y // BLOCK_SIZE + i)


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