import pygame
from src.utils.config import BLOCK_SIZE, ROWS, COLUMNS, SCREEN_WIDTH, SCREEN_HEIGHT, PANEL_WIDTH, PANEL_MARGIN, ui_config,AGENT_STRATEGY


def adjust_color(color, factor):
    """
    Adjust the brightness of a color.

    Args:
        color (tuple): RGB color.
        factor (float): Brightness factor.

    Returns:
        tuple: Adjusted RGB color.
    """
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def draw_block_3d(screen, color, x, y):
    """
    Draw a 3D-styled block at the specified grid coordinates.

    Args:
        screen (pygame.Surface): The game screen.
        color (tuple): RGB color of the block.
        x (int): X-coordinate.
        y (int): Y-coordinate.
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
    pygame.draw.line(screen, (0, 0, 0), (px, py), (px + BLOCK_SIZE, py), 2)
    pygame.draw.line(screen, (0, 0, 0), (px, py), (px, py + BLOCK_SIZE), 2)
    pygame.draw.line(screen, (0, 0, 0), (px, py + BLOCK_SIZE), (px + BLOCK_SIZE, py + BLOCK_SIZE), 2)
    pygame.draw.line(screen, (0, 0, 0), (px + BLOCK_SIZE, py), (px + BLOCK_SIZE, py + BLOCK_SIZE), 2)


def draw_grid(screen, board):
    """
    Draw the game grid and any placed blocks.

    Args:
        screen (pygame.Surface): The game screen.
        board (list of list): Game board.
    """
    for y in range(ROWS):
        for x in range(COLUMNS):
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(screen, ui_config["grid_color"], rect, 1)
            if board[y][x]:
                draw_block_3d(screen, board[y][x], x, y)


def draw_piece(screen, cells, color):
    """
    Draw a Tetris piece.

    Args:
        screen (pygame.Surface): The game screen.
        cells (list): List of (x, y) tuples.
        color (tuple): RGB color of the piece.
    """
    for (x, y) in cells:
        draw_block_3d(screen, color, x, y)


def draw_ghost_piece(screen, ghost_piece):
    """
    Draw the ghost (shadow) piece.

    Args:
        screen (pygame.Surface): The game screen.
        ghost_piece: The ghost piece instance.
    """
    ghost_color = (ghost_piece.color[0], ghost_piece.color[1], ghost_piece.color[2], 100)
    for (x, y) in ghost_piece.get_cells():
        ghost_cell = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        ghost_cell.fill(ghost_color)
        screen.blit(ghost_cell, (x * BLOCK_SIZE, y * BLOCK_SIZE))


def draw_next_piece(screen, env, panel_rect, font):
    """
    Draw the next piece preview.

    Args:
        screen (pygame.Surface): The game screen.
        env: Tetris environment.
        panel_rect (pygame.Rect): Panel rectangle.
        font (pygame.font.Font): Font for text.
    """
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


def draw_panel(screen, env, font,AGENT, agent_mode):
    """
    Draw the side panel.

    Args:
        screen (pygame.Surface): The game screen.
        env: Tetris environment.
        font (pygame.font.Font): Font for text.
        agent_mode (bool): True if agent mode is active.

    Returns:
        pygame.Rect: The rectangle of the mode toggle button.
    """
    panel_rect = pygame.Rect(SCREEN_WIDTH - PANEL_WIDTH - PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH,
                             SCREEN_HEIGHT - 2 * PANEL_MARGIN)
    pygame.draw.rect(screen, ui_config["panel_bg_color"], panel_rect)
    draw_next_piece(screen, env, panel_rect, font)
    score_text = font.render(f"Score: {env.score}", True, ui_config["text_color"])
    screen.blit(score_text, (panel_rect.x + 10, panel_rect.y + 150))
    button_width = PANEL_WIDTH - 20
    button_height = 40
    button_x = panel_rect.x + 10
    button_y = panel_rect.y + 200
    mode_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    if agent_mode:
        button_color = (255, 153, 153)
        button_text = "Stop"
    else:
        button_color = (153, 255, 153)
        button_text = "Run AI"
    mouse_pos = pygame.mouse.get_pos()
    if mode_button_rect.collidepoint(mouse_pos):
        button_color = tuple(max(0, c - 50) for c in button_color)
    pygame.draw.rect(screen, button_color, mode_button_rect)
    button_text_render = font.render(button_text, True, ui_config["text_color"])
    text_rect = button_text_render.get_rect(center=mode_button_rect.center)
    screen.blit(button_text_render, text_rect)
    agent_text = font.render(f"Agent: {AGENT}", True, ui_config["text_color"])
    screen.blit(agent_text, (panel_rect.x + 10, panel_rect.y + 250))
    strategy_text = font.render(f"Version: {AGENT_STRATEGY}", True, ui_config["text_color"])
    screen.blit(strategy_text, (panel_rect.x + 10, panel_rect.y + 300))
    return mode_button_rect


def check_play_again(screen, font, final_score):
    """
    Display the game over screen and prompt for replay.

    Args:
        screen (pygame.Surface): The game screen.
        font (pygame.font.Font): Font for text.
        final_score (int): The final score.

    Returns:
        bool: True if the player chooses to replay, False otherwise.
    """
    board_width = SCREEN_WIDTH - PANEL_WIDTH - PANEL_MARGIN
    board_height = SCREEN_HEIGHT
    overlay = pygame.Surface((board_width, board_height))
    overlay.set_alpha(200)
    overlay.fill(ui_config["background_color"])
    screen.blit(overlay, (0, 0))
    game_over_text = font.render("Game Over!", True, ui_config["text_color"])
    score_text = font.render(f"Score: {final_score}", True, ui_config["text_color"])
    play_again_text = font.render("Play again?", True, ui_config["text_color"])
    center_x = board_width // 2
    center_y = board_height // 2
    game_over_rect = game_over_text.get_rect(center=(center_x, center_y - 100))
    score_rect = score_text.get_rect(center=(center_x, center_y - 50))
    play_again_rect = play_again_text.get_rect(center=(center_x, center_y))
    screen.blit(game_over_text, game_over_rect)
    screen.blit(score_text, score_rect)
    screen.blit(play_again_text, play_again_rect)
    button_width = 100
    button_height = 50
    spacing = 20
    yes_button_rect = pygame.Rect(center_x - button_width - spacing // 2, center_y + 50, button_width, button_height)
    no_button_rect = pygame.Rect(center_x + spacing // 2, center_y + 50, button_width, button_height)
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
        pygame.display.update(pygame.Rect(0, 0, board_width, board_height))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if yes_button_rect.collidepoint(event.pos):
                    return True
                elif no_button_rect.collidepoint(event.pos):
                    return False