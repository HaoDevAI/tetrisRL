import sys
import pygame
import yaml
import numpy as np
from pathlib import Path
from src.environments.env import TetrisEnv
from src.agents.agent import TetrisAgent
from src.utils.display import draw_grid, draw_piece, draw_panel, draw_ghost_piece, check_play_again
from src.utils.config import ui_config, SCREEN_WIDTH, SCREEN_HEIGHT, env_params

DROP_EVENT = pygame.USEREVENT + 1
AGENT_ACTION_EVENT = pygame.USEREVENT

def main():
    """Main game loop."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris: Manual vs Agent Mode")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    MANUAL_DROP_INTERVAL = ui_config["drop_interval"]
    AGENT_DROP_INTERVAL = ui_config["drop_interval"] // 1
    AGENT_ACTION_INTERVAL = 50

    FILE_DIR = Path(__file__).parent
    CONFIG_PATH = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
    with open(CONFIG_PATH, 'r') as f:
        config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]
    AGENT = "ref"
    VERSION = "best"
    AGENT_DIR = FILE_DIR / 'logs' / AGENT
    WEIGHTS_PATH = AGENT_DIR / f"{VERSION}.npy"
    agent_weights = np.load(WEIGHTS_PATH)
    AGENT_STRATEGY = config["strategy"]

    pygame.time.set_timer(DROP_EVENT, MANUAL_DROP_INTERVAL)
    pygame.time.set_timer(AGENT_ACTION_EVENT, 0)

    running = True
    agent_mode = False
    while running:
        env = TetrisEnv(env_params["rows"],
                        env_params["cols"],
                        env_params["piece_generator"],
                        env_params["random_seed"])
        game_active = True
        mode_button_rect = None
        agent_actions = []

        while game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_active = False
                    running = False
                elif event.type == DROP_EVENT:
                    env.drop_piece()
                elif event.type == AGENT_ACTION_EVENT and agent_mode:
                    if not agent_actions:
                        agent = TetrisAgent(env, agent_weights,AGENT_STRATEGY)
                        best_move = agent.get_best_move()
                        if best_move is not None:
                            actions = []
                            for _ in range(best_move["rotations"]):
                                actions.append(("rotate", True))
                            dx = best_move["x"] - env.current_piece.x
                            if dx > 0:
                                for _ in range(dx):
                                    actions.append(("move", 1))
                            elif dx < 0:
                                for _ in range(-dx):
                                    actions.append(("move", -1))
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
                        agent_mode = not agent_mode
                        agent_actions = []
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
            mode_button_rect = draw_panel(screen, env, font,AGENT , agent_mode)
            pygame.display.flip()
            if env.game_over:
                play_again = check_play_again(screen, font, env.score)
                if play_again:
                    game_active = False
                else:
                    game_active = False
                    running = False
            clock.tick(ui_config["fps"])
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
