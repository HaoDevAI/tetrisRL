import pygame
from src.utils.config import *
import json
import os
import sys

def get_data_dir():
    """Get the appropriate directory for saving game data."""
    # When running as a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # For Windows, use %APPDATA%\TetrisGame
        if os.name == 'nt':
            data_dir = os.path.join(os.environ['APPDATA'], 'TetrisGame')
        # For macOS, use ~/Library/Application Support/TetrisGame
        elif sys.platform == 'darwin':
            data_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'TetrisGame')
        # For Linux, use ~/.local/share/TetrisGame
        else:
            data_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'TetrisGame')
    # When running as a regular Python script
    else:
        data_dir = os.path.abspath(os.path.dirname(__file__))

    # Ensure directory exists
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def load_scores():
    """Load high scores from file."""
    scores_path = os.path.join(get_data_dir(), "scores.json")
    if os.path.exists(scores_path):
        try:
            with open(scores_path, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_score(player_name, score):
    """Save a player's score."""
    scores = load_scores()
    scores.append({"name": player_name, "score": score})
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:10]  # Keep only top 10

    scores_path = os.path.join(get_data_dir(), "scores.json")
    with open(scores_path, "w") as f:
        json.dump(scores, f)

def enter_name(screen, font):
    """Display name entry interface with leaderboard."""
    name = ""
    input_active = True

    # Load high scores
    high_scores = load_scores()

    # Calculate scaled positions and sizes
    input_box_width = 300 * scale_factor
    input_box_height = 50 * scale_factor
    start_button_width = 200 * scale_factor
    start_button_height = 50 * scale_factor
    title_y = 250 * scale_factor
    input_box_y = 300 * scale_factor
    leaderboard_title_y = 400 * scale_factor
    scores_start_y = 450 * scale_factor
    score_spacing = 30 * scale_factor
    padding = 10 * scale_factor

    while True:
        screen.fill(ui_config["background_color"])

        # Title
        title = font.render("ENTER YOUR NAME", True, ui_config["text_color"])
        screen.blit(title, (INITIAL_WIDTH//2 - title.get_width()//2, title_y))

        # Input box
        input_box = pygame.Rect(INITIAL_WIDTH//2 - input_box_width//2, input_box_y, input_box_width, input_box_height)
        pygame.draw.rect(screen, ui_config["text_color"], input_box, 2)

        # Input text
        input_text = font.render(name + ("_" if input_active else ""), True, ui_config["text_color"])
        screen.blit(input_text, (input_box.x + padding, input_box.y + padding))

        # Leaderboard title
        leaderboard_title = font.render("HIGHEST SCORES", True, ui_config["text_color"])
        screen.blit(leaderboard_title, (INITIAL_WIDTH//2 - leaderboard_title.get_width()//2, leaderboard_title_y))

        # Display high scores
        for i, score in enumerate(high_scores[:10]):
            score_text = font.render(f"{i+1}. {score['name']}: {score['score']}", True, ui_config["text_color"])
            screen.blit(score_text, (INITIAL_WIDTH//2 - score_text.get_width()//2, scores_start_y + i * score_spacing))

        # Start button
        start_button = pygame.Rect(
            INITIAL_WIDTH//2 - start_button_width//2,
            INITIAL_HEIGHT - start_button_height - padding*10,
            start_button_width,
            start_button_height
        )
        pygame.draw.rect(screen, ui_config["text_color"], start_button, 2)
        start_text = font.render("START GAME", True, ui_config["text_color"])
        screen.blit(start_text, (
            start_button.x + start_button.width//2 - start_text.get_width()//2,
            start_button.y + start_button.height//2 - start_text.get_height()//2
        ))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos) and name:
                    return name
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name:
                    return name
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 15 and event.unicode.isalnum():
                    name += event.unicode

        pygame.display.flip()

def ask_change_name(screen, font):
    """Ask if the player wants to change their name."""
    screen.fill(ui_config["background_color"])

    title = font.render("Play as a different player?", True, ui_config["text_color"])
    screen.blit(title, (INITIAL_WIDTH//2 - title.get_width()//2, INITIAL_HEIGHT//2 - 100))

    yes_button = pygame.Rect(INITIAL_WIDTH//2 - 150, INITIAL_HEIGHT//2, 100, 50)
    pygame.draw.rect(screen, ui_config["text_color"], yes_button, 2)
    yes_text = font.render("YES", True, ui_config["text_color"])
    screen.blit(yes_text, (yes_button.x + yes_button.width//2 - yes_text.get_width()//2,
                         yes_button.y + yes_button.height//2 - yes_text.get_height()//2))

    no_button = pygame.Rect(INITIAL_WIDTH//2 + 50, INITIAL_HEIGHT//2, 100, 50)
    pygame.draw.rect(screen, ui_config["text_color"], no_button, 2)
    no_text = font.render("NO", True, ui_config["text_color"])
    screen.blit(no_text, (no_button.x + no_button.width//2 - no_text.get_width()//2,
                        no_button.y + no_button.height//2 - no_text.get_height()//2))

    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if yes_button.collidepoint(event.pos):
                    return True
                elif no_button.collidepoint(event.pos):
                    return False

def adjust_color(color, factor):
    """
    Adjust the brightness of a color (for ghost pieces).

    Args:
        color (tuple): RGB color.
        factor (float): Brightness factor.

    Returns:
        tuple: Adjusted RGB color.
    """
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def draw_block_3d(screen, color, px, py):
    """
    Draw a 3D-styled block at the specified grid coordinates.

    Args:
        screen (pygame.Surface): The game screen.
        color (tuple): RGB color of the block.
        px (int): X-coordinate.
        py (int): Y-coordinate.
    """
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
    pygame.draw.line(screen, (0, 0, 0), (px, py), (px + BLOCK_SIZE, py), BORDER_WIDTH)
    pygame.draw.line(screen, (0, 0, 0), (px, py), (px, py + BLOCK_SIZE), 3)
    pygame.draw.line(screen, (0, 0, 0), (px, py + BLOCK_SIZE), (px + BLOCK_SIZE, py + BLOCK_SIZE), BORDER_WIDTH)
    pygame.draw.line(screen, (0, 0, 0), (px + BLOCK_SIZE, py), (px + BLOCK_SIZE, py + BLOCK_SIZE), BORDER_WIDTH)


def draw_grid(id, screen, board):
    """
    Draw the game grid and any placed blocks.

    Args:
        id (int): The ID of the grid.
        screen (pygame.Surface): The game screen.
        board (list of list): Game board.
    """
    if id == 0:
        x_offset = CENTER_X - BOARD_WIDTH - PANEL_WIDTH - PANEL_MARGIN * 2
    elif id == 1:
        x_offset = CENTER_X + PANEL_WIDTH + PANEL_MARGIN * 2
    y_offset = (INITIAL_HEIGHT - BOARD_HEIGHT)//2
    for y in range(ROWS):
        for x in range(COLUMNS):
            rect = pygame.Rect(x_offset + x * BLOCK_SIZE, y_offset + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(screen, ui_config["grid_color"], rect, GRID_WIDTH)
            if board[y][x]:
                draw_block_3d(screen, board[y][x], x_offset + x * BLOCK_SIZE, y_offset +  y * BLOCK_SIZE)


def draw_piece(id, screen, cells, color):
    """
    Draw a Tetris piece.

    Args:
        screen (pygame.Surface): The game screen.
        cells (list): List of (x, y) tuples.
        color (tuple): RGB color of the piece.
    """
    if id == 0:
        x_offset = CENTER_X - BOARD_WIDTH - PANEL_WIDTH - PANEL_MARGIN * 2
    elif id == 1:
        x_offset = CENTER_X + PANEL_WIDTH + PANEL_MARGIN * 2
    y_offset = (INITIAL_HEIGHT - BOARD_HEIGHT)//2
    for (x, y) in cells:
        draw_block_3d(screen, color, x_offset + x * BLOCK_SIZE, y_offset + y * BLOCK_SIZE)


def draw_ghost_piece(id, screen, ghost_piece):
    """
    Draw the ghost (shadow) piece.

    Args:
        screen (pygame.Surface): The game screen.
        ghost_piece: The ghost piece instance.
    """
    ghost_color = (ghost_piece.color[0], ghost_piece.color[1], ghost_piece.color[2], 100)
    if id == 0:
        x_offset = CENTER_X - BOARD_WIDTH - PANEL_WIDTH - PANEL_MARGIN * 2
    elif id == 1:
        x_offset = CENTER_X + PANEL_WIDTH + PANEL_MARGIN * 2
    y_offset = (INITIAL_HEIGHT - BOARD_HEIGHT)//2
    for (x, y) in ghost_piece.get_cells():
        ghost_cell = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        ghost_cell.fill(ghost_color)
        screen.blit(ghost_cell, (x * BLOCK_SIZE + x_offset, y_offset + y * BLOCK_SIZE))


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
    piece_width = len(temp_piece.matrix[0])
    offset_x = panel_rect.x + (PANEL_WIDTH - piece_width * BLOCK_SIZE) // 2
    offset_y = panel_rect.y + 50
    for i, row in enumerate(temp_piece.matrix):
        for j, val in enumerate(row):
            if val:
                draw_block_3d(screen, temp_piece.color, offset_x + j * BLOCK_SIZE, offset_y + i * BLOCK_SIZE)


def draw_panel(id, screen, env, font, mode):
    """
    Draw the side panel.

    Args:
        id (int): The ID of the panel.
        screen (pygame.Surface): The game screen.
        env: Tetris environment.
        font (pygame.font.Font): Font for text.
        mode (str): Game mode (e.g. "Easy", "Medium", "Hard").

    Returns:
        pygame.Rect: The rectangle of the mode toggle button.
    """
    y_offset = (INITIAL_HEIGHT - BOARD_HEIGHT)//2
    if id == 0:
        panel_rect = pygame.Rect(
            CENTER_X - PANEL_WIDTH - PANEL_MARGIN,
            y_offset,
            PANEL_WIDTH,
            BOARD_HEIGHT
        )
        pygame.draw.rect(screen, ui_config["panel_bg_color"], panel_rect)
        draw_next_piece(screen, env, panel_rect, font)
        score_text = font.render(f"Score: {env.score}", True, ui_config["text_color"])
        screen.blit(score_text, (panel_rect.x + 10, panel_rect.y + 150))
        level_text = font.render(f"Level: {env.level}", True, ui_config["text_color"])
        screen.blit(level_text, (panel_rect.x + 10, panel_rect.y + 200))
        pause_text = font.render("Pause", True, ui_config["text_color"])
        pause_button_rect = pygame.Rect(panel_rect.x + 10, panel_rect.y + 250, 100, 40)
        pause_color = (122, 244, 244) if pause_button_rect.collidepoint(pygame.mouse.get_pos()) else (102, 204, 204)
        pygame.draw.rect(screen, pause_color, pause_button_rect, border_radius=10)
        pause_text_rect = pause_text.get_rect(center=pause_button_rect.center)
        screen.blit(pause_text, pause_text_rect)
        return pause_button_rect

    if id == 1:
        panel_rect = pygame.Rect(
            CENTER_X + PANEL_MARGIN,
            y_offset,
            PANEL_WIDTH,
            BOARD_HEIGHT
        )
        pygame.draw.rect(screen, ui_config["panel_bg_color"], panel_rect)
        draw_next_piece(screen, env, panel_rect, font)
        score_text = font.render(f"Score: {env.score}", True, ui_config["text_color"])
        screen.blit(score_text, (panel_rect.x + 10, panel_rect.y + 150))
        level_text = font.render(f"Level: {env.level}", True, ui_config["text_color"])
        screen.blit(level_text, (panel_rect.x + 10, panel_rect.y + 200))
        mode_text = font.render(f"Mode: {mode}", True, ui_config["text_color"])
        screen.blit(mode_text, (panel_rect.x + 10, panel_rect.y + 250))
        return None
    return None


def choose_mode(screen, font):
    """
    Display the mode selection screen.
    Args:
        screen (pygame.Surface): The game screen.
        font (pygame.font.Font): Font for text.
    Returns:
        mode (str): Selected game mode.
    """
    overlay = pygame.Surface((INITIAL_WIDTH, INITIAL_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(ui_config["background_color"])
    screen.blit(overlay, (0, 0))
    title_text = font.render("Select Difficulty:", True, ui_config["text_color"])
    easy_text = font.render("Easy", True, ui_config["text_color"])
    medium_text = font.render("Medium", True, ui_config["text_color"])
    hard_text = font.render("Hard", True, ui_config["text_color"])
    asian_text = font.render("Asian", True, ui_config["text_color"])
    center_x = INITIAL_WIDTH // 2
    center_y = INITIAL_HEIGHT // 2
    button_width = 150
    button_height = 50
    title_rect = title_text.get_rect(center=(center_x - 125, center_y - 150))
    easy_button_rect = pygame.Rect(center_x-200, center_y -125, button_width, button_height)
    medium_button_rect = pygame.Rect(center_x-200, center_y-50, button_width, button_height)
    hard_button_rect = pygame.Rect(center_x-200, center_y + 25, button_width, button_height)
    asian_button_rect = pygame.Rect(center_x-200, center_y + 100, button_width, button_height)

    mode_colors = {
        "Easy": {"base": (153, 255, 153), "hover": (183, 255, 183)},
        "Medium": {"base": (102, 153, 255), "hover": (122, 183, 255)},
        "Hard": {"base": (255, 178, 102), "hover": (255, 213, 122)},
        "Asian": {"base": (255, 153, 153), "hover": (255, 183, 183)},
    }
    waiting = True
    while waiting:
        screen.blit(overlay, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        easy_color = mode_colors["Easy"]["hover"] if easy_button_rect.collidepoint(mouse_pos) else mode_colors["Easy"]["base"]
        medium_color = mode_colors["Medium"]["hover"] if medium_button_rect.collidepoint(mouse_pos) else mode_colors["Medium"][
            "base"]
        hard_color = mode_colors["Hard"]["hover"] if hard_button_rect.collidepoint(mouse_pos) else mode_colors["Hard"]["base"]
        asian_color = mode_colors["Asian"]["hover"] if asian_button_rect.collidepoint(mouse_pos) else mode_colors["Asian"][
            "base"]

        pygame.draw.rect(screen, easy_color, easy_button_rect, border_radius=10)
        pygame.draw.rect(screen, medium_color, medium_button_rect, border_radius=10)
        pygame.draw.rect(screen, hard_color, hard_button_rect, border_radius=10)
        pygame.draw.rect(screen, asian_color, asian_button_rect, border_radius=10)
        easy_text_rect = easy_text.get_rect(center=easy_button_rect.center)
        medium_text_rect = medium_text.get_rect(center=medium_button_rect.center)
        hard_text_rect = hard_text.get_rect(center=hard_button_rect.center)
        asian_text_rect = asian_text.get_rect(center=asian_button_rect.center)

        screen.blit(title_text, title_rect)
        screen.blit(easy_text, easy_text_rect)
        screen.blit(medium_text, medium_text_rect)
        screen.blit(hard_text, hard_text_rect)
        screen.blit(asian_text, asian_text_rect)
        draw_guidelines(screen, font)
        pygame.display.update(pygame.Rect(0, 0, INITIAL_WIDTH, INITIAL_HEIGHT))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if easy_button_rect.collidepoint(event.pos):
                    return "Easy"
                elif medium_button_rect.collidepoint(event.pos):
                    return "Medium"
                elif hard_button_rect.collidepoint(event.pos):
                    return "Hard"
                elif asian_button_rect.collidepoint(event.pos):
                    return "Asian"
        pygame.time.wait(10)
    return None


def check_play_again(screen, font, winner):
    """
    Display the game over screen and prompt for replay.

    Args:
        screen (pygame.Surface): The game screen.
        font (pygame.font.Font): Font for text.
        winner (str): Name of the winner.

    Returns:
        bool: True if the player chooses to replay, False otherwise.
    """
    overlay = pygame.Surface((INITIAL_WIDTH, INITIAL_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(ui_config["background_color"])
    screen.blit(overlay, (0, 0))
    game_over_text = font.render("Game Over!", True, ui_config["text_color"])
    if winner == "player":
        winner_text = font.render(f"Victoryy!! You beat the AI", True, ui_config["text_color"])
        play_again_text = font.render("Play again?", True, ui_config["text_color"])
    elif winner == "agent":
        winner_text = font.render("Defeat :( The AI is unbeatable!", True, ui_config["text_color"])
        play_again_text = font.render("Wanna try again?", True, ui_config["text_color"])
    center_x = INITIAL_WIDTH // 2
    center_y = INITIAL_HEIGHT // 2
    game_over_rect = game_over_text.get_rect(center=(center_x, center_y - 100))
    winner_rect = winner_text.get_rect(center=(center_x, center_y - 50))
    play_again_rect = play_again_text.get_rect(center=(center_x, center_y))
    screen.blit(game_over_text, game_over_rect)
    screen.blit(winner_text, winner_rect)
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
        screen.blit(winner_text, winner_rect)
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
        pygame.display.update(pygame.Rect(0, 0, INITIAL_WIDTH, INITIAL_HEIGHT))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if yes_button_rect.collidepoint(event.pos):
                    return True
                elif no_button_rect.collidepoint(event.pos):
                    return False
            pygame.time.wait(10)
    return None


def draw_guidelines(screen, font):
    """
    Draw the guidelines for controls.
    """
    center_x = INITIAL_WIDTH // 2
    center_y = INITIAL_HEIGHT // 2

    guide_text = font.render("Controls:", True, ui_config["text_color"])
    move_left_text = font.render(f"A: Move left", True, ui_config["text_color"])
    move_right_text = font.render(f"D: Move right", True, ui_config["text_color"])
    move_down_text = font.render(f"S: Move down", True, ui_config["text_color"])
    rotate_text = font.render(f"W: Rotate", True, ui_config["text_color"])
    drop_text = font.render(f"Enter: Hard drop", True, ui_config["text_color"])
    swap_text = font.render(f"C: Swap", True, ui_config["text_color"])

    screen.blit(guide_text, (center_x + 50, center_y - 150))
    screen.blit(move_left_text, (center_x + 50, center_y - 100))
    screen.blit(move_right_text, (center_x + 50, center_y - 50))
    screen.blit(move_down_text, (center_x + 50, center_y))
    screen.blit(rotate_text, (center_x + 50, center_y + 50))
    screen.blit(swap_text, (center_x + 50, center_y + 100))
    screen.blit(drop_text, (center_x + 50, center_y + 150))


def draw_pause_menu(screen, font):
    """
    Display the pause menu.

    Args:
        screen (pygame.Surface): The game screen.
        font (pygame.font.Font): Font for text.
    """
    overlay = pygame.Surface((INITIAL_WIDTH, INITIAL_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(ui_config["background_color"])
    screen.blit(overlay, (0, 0))
    choices_colors = {
        "resume": {"base": (102, 153, 255), "hover": (122, 183, 255)},
        "restart": {"base": (255, 178, 102), "hover": (255, 213, 122)},
        "quit": {"base": (255, 153, 153), "hover": (255, 183, 183)},
    }

    pause_text = font.render("Game Paused", True, ui_config["text_color"])
    resume_text = font.render("Resume", True, ui_config["text_color"])
    play_again_text = font.render("Play Again", True, ui_config["text_color"])
    quit_text = font.render("Quit", True, ui_config["text_color"])

    center_x = INITIAL_WIDTH // 2
    center_y = INITIAL_HEIGHT // 2

    pause_text_rect = pause_text.get_rect(center=(center_x-125, center_y - 125))
    resume_button_rect = pygame.Rect(center_x - 200, center_y - 75, 150, 50)
    play_again_button_rect = pygame.Rect(center_x - 200, center_y , 150, 50)
    quit_button_rect = pygame.Rect(center_x - 200, center_y + 75, 150, 50)

    waiting = True
    while waiting:
        screen.blit(overlay, (0, 0))
        screen.blit(pause_text, pause_text_rect)

        mouse_pos = pygame.mouse.get_pos()
        resume_color = choices_colors["resume"]["hover"] if resume_button_rect.collidepoint(mouse_pos) else choices_colors["resume"]["base"]
        play_again_color = choices_colors["restart"]["hover"] if play_again_button_rect.collidepoint(mouse_pos) else choices_colors["restart"]["base"]
        quit_color = choices_colors["quit"]["hover"] if quit_button_rect.collidepoint(mouse_pos) else choices_colors["quit"]["base"]

        pygame.draw.rect(screen, resume_color, resume_button_rect, border_radius=10)
        pygame.draw.rect(screen, play_again_color, play_again_button_rect, border_radius=10)
        pygame.draw.rect(screen, quit_color, quit_button_rect, border_radius=10)

        resume_text_rect = resume_text.get_rect(center=resume_button_rect.center)
        play_again_text_rect = play_again_text.get_rect(center=play_again_button_rect.center)
        quit_text_rect = quit_text.get_rect(center=quit_button_rect.center)

        screen.blit(resume_text, resume_text_rect)
        screen.blit(play_again_text, play_again_text_rect)
        screen.blit(quit_text, quit_text_rect)
        draw_guidelines(screen, font)

        pygame.display.update(pygame.Rect(0, 0, INITIAL_WIDTH, INITIAL_HEIGHT))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if resume_button_rect.collidepoint(event.pos):
                    return "resume"
                elif play_again_button_rect.collidepoint(event.pos):
                    return "restart"
                elif quit_button_rect.collidepoint(event.pos):
                    return "quit"
        pygame.time.wait(10)
    return None


def draw_game_over(id, screen, font):
    """
    Display the game over screen.
    Args:
        id (int): The id of the player.
        screen (pygame.Surface): The game screen.
        font (pygame.font.Font): Font for text.
    """
    # Determine the board position based on the id
    if id == 0:
        x_offset = CENTER_X - BOARD_WIDTH - PANEL_WIDTH - PANEL_MARGIN * 2
    elif id == 1:
        x_offset = CENTER_X + PANEL_WIDTH + PANEL_MARGIN * 2
    y_offset = (INITIAL_HEIGHT - BOARD_HEIGHT) // 2

    # Create an overlay for the player's board
    overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))  # Semi-transparent black overlay
    screen.blit(overlay, (x_offset, y_offset))

    draw_stamp(screen, (x_offset + BOARD_WIDTH // 2, y_offset + BOARD_HEIGHT // 2), int(150*scale_factor), stamp_color)






def draw_stamp(surface, center, radius, color):
    """
    Draw an "Eliminated" stamp with the following components:
    - Thick outer circle
    - Two thinner inner circles
    - Rotated "Eliminated" text in the center

    Args:
        surface (pygame.Surface): The surface to draw on
        center (tuple): (x, y) center position of the stamp
        radius (int): Radius of the outer circle
        color (tuple): RGB color of the stamp
    """
    x_center, y_center = center

    # Scale borders based on radius
    outer_border = max(int(radius * 0.05), 3)
    middle_border = max(int(radius * 0.015), 2)
    inner_border = max(int(radius * 0.01), 1)

    # Draw circles
    pygame.draw.circle(surface, color, (x_center, y_center), radius, outer_border)
    pygame.draw.circle(surface, color, (x_center, y_center), radius - int(radius * 0.12), middle_border)
    pygame.draw.circle(surface, color, (x_center, y_center), radius - int(radius * 0.16), inner_border)


    # Draw the text
    stamp_text_surf = font_large.render("Eliminated", True, color)
    rotate_stamp_text_surf = pygame.transform.rotate(stamp_text_surf, 30)
    rotate_stamp_rect = rotate_stamp_text_surf.get_rect(center=(x_center, y_center))
    surface.blit(rotate_stamp_text_surf, rotate_stamp_rect)

