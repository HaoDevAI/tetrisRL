import numpy as np
from src.environments.env import TetrisEnv
from src.agents.tetris_agent import TetrisAgent
from utils.UI import *

# === Load configuration ===
FILE_DIR = Path(__file__).parent
CONFIG_PATH = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
with open(CONFIG_PATH, 'r') as f:
    config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]

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
def draw_panel(screen, env, font, agent_mode):
    """
    Draws a side panel showing the next piece, current score, and a toggle button
    to switch between Manual and Agent modes.
    """
    panel_rect = pygame.Rect(WIDTH + PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH, HEIGHT - PANEL_MARGIN * 2)
    pygame.draw.rect(screen, ui_config["panel_bg_color"], panel_rect)

    # Next Piece preview.
    draw_next_piece(screen,env,panel_rect,font)
    # Display Score.
    score_text = font.render(f"Score: {env.score}", True, ui_config["text_color"])
    screen.blit(score_text, (panel_rect.x + 10, panel_rect.y + 150))

    # Draw toggle button.
    button_width = PANEL_WIDTH - 20
    button_height = 40
    button_x = panel_rect.x + 10
    button_y = panel_rect.y + 200
    mode_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Set button color based on mode: RED when manual, GREEN when agent.
    if agent_mode:
        button_color = (255, 153, 153)  # Red for manual mode.
        button_text = "Stop"
    else:
        button_color = (153, 255, 153)  # Green for agent mode.
        button_text = "Run AI"


    # (Optional) You can add a hover effect here if desired.
    mouse_pos = pygame.mouse.get_pos()
    if mode_button_rect.collidepoint(mouse_pos):
        # For example, darken the color on hover.
        button_color = tuple(max(0, c - 50) for c in button_color)

    pygame.draw.rect(screen, button_color, mode_button_rect)
    button_text = font.render(button_text, True, ui_config["text_color"])
    text_rect = button_text.get_rect(center=mode_button_rect.center)
    screen.blit(button_text, text_rect)

    agent_text = font.render(f"Agent: {AGENT}", True, ui_config["text_color"])
    screen.blit(agent_text, (panel_rect.x + 10, panel_rect.y + 250))
    strategy_text = font.render(f"Version: {AGENT_STRATEGY}", True, ui_config["text_color"])
    screen.blit(strategy_text, (panel_rect.x + 10, panel_rect.y + 300))
    screen.blit(strategy_text, (panel_rect.x + 10, panel_rect.y + 300))

    return mode_button_rect

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
