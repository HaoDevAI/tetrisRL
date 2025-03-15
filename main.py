import sys
import pygame
import numpy as np
import yaml
from pathlib import Path
from src.environments.env import TetrisEnv
from src.agents.tetris_agent import TetrisAgent

# === Load configuration ===
FILE_DIR = Path(__file__).parent
CONFIG_PATH = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
with open(CONFIG_PATH, 'r') as f:
    config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]

env_params = {
    "piece_generator": config["generator"],
    # Using fixed seed for consistency.
    "random_seed": None,
    "rows": config["rows"],
    "cols": config["cols"]
}

ui_config = {
    "fps": config["fps"],
    "drop_interval": config["drop_interval"],  # base drop interval in ms
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

BLOCK_SIZE = ui_config["block_size"]
ROWS = env_params["rows"]
COLUMNS = env_params["cols"]
WIDTH = COLUMNS * BLOCK_SIZE
HEIGHT = ROWS * BLOCK_SIZE
PANEL_WIDTH = ui_config["panel_width"]
PANEL_MARGIN = ui_config["panel_margin"]
SCREEN_WIDTH = WIDTH + PANEL_WIDTH + PANEL_MARGIN * 2
SCREEN_HEIGHT = HEIGHT

# Define two drop intervals.
MANUAL_DROP_INTERVAL = ui_config["drop_interval"]
AGENT_DROP_INTERVAL = int(ui_config["drop_interval"] / 10)  # faster drop in agent mode

# Define an interval for agent actions (the step-by-step moves).
AGENT_ACTION_INTERVAL = 10# in ms

# === Agent setup ===
AGENT = "ref"
VERSION = "best"
AGENT_DIR = FILE_DIR / 'logs' / AGENT
WEIGHTS_PATH = AGENT_DIR / f"{VERSION}.npy"
agent_weights = np.load(WEIGHTS_PATH)
AGENT_STRATEGY = config["strategy"]

# === Timer event identifiers ===
DROP_EVENT = pygame.USEREVENT + 1
AGENT_ACTION_EVENT = pygame.USEREVENT


# === Drawing functions ===
def draw_block_3d(screen, color, x, y):
    rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, ui_config["border_color"], rect, ui_config["border_width"])


def draw_grid(screen, board):
    for y in range(ROWS):
        for x in range(COLUMNS):
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(screen, ui_config["grid_color"], rect, ui_config["grid_width"])
            if board[y][x]:
                draw_block_3d(screen, board[y][x], x, y)


def draw_piece(screen, cells, color):
    for (x, y) in cells:
        draw_block_3d(screen, color, x, y)


def draw_ghost_piece(screen, ghost_piece):
    ghost_color = (ghost_piece.color[0], ghost_piece.color[1], ghost_piece.color[2], 100)
    for (x, y) in ghost_piece.get_cells():
        ghost_cell = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        ghost_cell.fill(ghost_color)
        screen.blit(ghost_cell, (x * BLOCK_SIZE, y * BLOCK_SIZE))


def draw_panel(screen, env, font, agent_mode):
    """
    Draws a side panel showing the next piece, current score, and a toggle button
    to switch between Manual and Agent modes.
    """
    panel_rect = pygame.Rect(WIDTH + PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH, HEIGHT - PANEL_MARGIN * 2)
    pygame.draw.rect(screen, ui_config["panel_bg_color"], panel_rect)

    # Next Piece preview.
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
                pygame.draw.rect(screen, ui_config["border_color"], rect, ui_config["border_width"])

    # Display Score.
    score_text = font.render(f"Score: {env.score}", True, ui_config["text_color"])
    screen.blit(score_text, (panel_rect.x + 10, panel_rect.y + 150))

    # Draw toggle button.
    button_width = PANEL_WIDTH - 20
    button_height = 40
    button_x = panel_rect.x + 10
    button_y = panel_rect.y + 300
    mode_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Set button color based on mode: RED when manual, GREEN when agent.
    if agent_mode:
        button_color = (153, 255, 153)  # Green for agent mode.
        button_text = "AI Mode"
    else:
        button_color = (255, 153, 153) # Red for manual mode.
        button_text = "Manual"

    # (Optional) You can add a hover effect here if desired.
    mouse_pos = pygame.mouse.get_pos()
    if mode_button_rect.collidepoint(mouse_pos):
        # For example, darken the color on hover.
        button_color = tuple(max(0, c - 50) for c in button_color)

    pygame.draw.rect(screen, button_color, mode_button_rect)
    button_text = font.render(button_text, True, ui_config["text_color"])
    text_rect = button_text.get_rect(center=mode_button_rect.center)
    screen.blit(button_text, text_rect)
    return mode_button_rect


def check_play_again(screen, font, final_score):
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
    yes_button_rect = pygame.Rect(center_x - button_width - spacing // 2, SCREEN_HEIGHT // 2 + 50, button_width,
                                  button_height)
    no_button_rect = pygame.Rect(center_x + spacing // 2, SCREEN_HEIGHT // 2 + 50, button_width, button_height)
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


# === Main game loop ===
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris: Manual vs Agent Mode")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    # Start with manual drop interval and disable agent action events.
    pygame.time.set_timer(DROP_EVENT, MANUAL_DROP_INTERVAL)
    pygame.time.set_timer(AGENT_ACTION_EVENT, 0)  # disabled in manual mode

    running = True
    agent_mode = False  # start in manual mode

    while running:
        env = TetrisEnv(env_params["rows"],
                        env_params["cols"],
                        env_params["piece_generator"],
                        env_params["random_seed"])
        game_active = True
        mode_button_rect = None
        # In agent mode, we'll maintain a queue of pending actions.
        agent_actions = []

        while game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_active = False
                    running = False

                elif event.type == DROP_EVENT:
                    # Always auto-drop the piece (simulate gravity).
                    env.drop_piece()

                elif event.type == AGENT_ACTION_EVENT and agent_mode:
                    # On each agent action event, if there are pending actions execute one.
                    if not agent_actions:
                        # Compute best move for the current piece.
                        agent = TetrisAgent(env, agent_weights)
                        best_move = None
                        if AGENT_STRATEGY == "normal":
                            best_move = agent.get_best_move()
                        elif AGENT_STRATEGY == "promax":
                            best_move = agent.get_best_move_promax()
                        if best_move is not None:
                            actions = []
                            # Append rotation actions.
                            for _ in range(best_move["rotations"]):
                                actions.append(("rotate", True))
                            # Append horizontal move actions.
                            dx = best_move["x"] - env.current_piece.x
                            if dx > 0:
                                for _ in range(dx):
                                    actions.append(("move", 1))
                            elif dx < 0:
                                for _ in range(-dx):
                                    actions.append(("move", -1))
                            # Finally, append a hard drop to save time.
                            actions.append(("hard_drop", None))
                            agent_actions = actions
                    else:
                        action, value = agent_actions.pop(0)
                        if action == "rotate":
                            env.rotate_piece(clockwise=value)
                        elif action == "move":
                            env.move_piece(value, 0)
                        elif action == "hard_drop":
                            env.hard_drop()

                elif event.type == pygame.KEYDOWN and not agent_mode:
                    # Manual mode key controls.
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

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if mode_button_rect and mode_button_rect.collidepoint(event.pos):
                        # Toggle mode and update timers accordingly.
                        agent_mode = not agent_mode
                        agent_actions = []  # clear any pending actions
                        if agent_mode:
                            pygame.time.set_timer(DROP_EVENT, AGENT_DROP_INTERVAL)
                            pygame.time.set_timer(AGENT_ACTION_EVENT, AGENT_ACTION_INTERVAL)
                        else:
                            pygame.time.set_timer(DROP_EVENT, MANUAL_DROP_INTERVAL)
                            pygame.time.set_timer(AGENT_ACTION_EVENT, 0)

            screen.fill(ui_config["background_color"])
            draw_grid(screen, env.grid.board)
            if hasattr(env, "get_ghost_piece"):
                ghost_piece = env.get_ghost_piece()
                draw_ghost_piece(screen, ghost_piece)
            draw_piece(screen, env.current_piece.get_cells(), env.current_piece.color)
            mode_button_rect = draw_panel(screen, env, font, agent_mode)
            pygame.display.flip()

            if env.game_over:
                play_again = check_play_again(screen, font, env.score)
                if play_again:
                    game_active = False  # restart game
                else:
                    game_active = False
                    running = False
            clock.tick(ui_config["fps"])
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
