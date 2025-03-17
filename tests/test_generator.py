import pygame
import time
from pathlib import Path
import numpy as np
import yaml
from src.environments.env import TetrisEnv
from src.agents.agent import TetrisAgent
from src.utils.display import draw_grid, draw_piece, draw_panel, draw_next_piece
from src.utils.config import ui_config, SCREEN_WIDTH, SCREEN_HEIGHT, env_params, WIDTH, HEIGHT, PANEL_MARGIN, PANEL_WIDTH

# Count the generated pieces in a game
piece_count = {"I": 0, "O": 0, "T": 0, "S": 0, "Z": 0, "J": 0, "L": 0}

# Load agent weights and config (agent info)
FILE_DIR = Path(__file__).parent.parent
CONFIG_PATH = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
AGENT_DIR = FILE_DIR / 'logs' / "ref"
VERSION = "best"
WEIGHTS_PATH = AGENT_DIR / f"{VERSION}.npy"
agent_weights = np.load(WEIGHTS_PATH)


def draw_panel(screen, env, font):
    panel_rect = pygame.Rect(WIDTH + PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH, HEIGHT - 2 * PANEL_MARGIN)
    pygame.draw.rect(screen, ui_config["panel_bg_color"], panel_rect)
    draw_next_piece(screen, env, panel_rect, font)
    y_offset = panel_rect.y + 150
    title = font.render("Piece Counts:", True, ui_config["text_color"])
    screen.blit(title, (panel_rect.x + 10, y_offset))

    y_offset = panel_rect.y + 200
    for piece, count in piece_count.items():
        text = font.render(f"{piece}: {count}", True, ui_config["text_color"])
        screen.blit(text, (panel_rect.x + 10, y_offset))
        y_offset += 30


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Test Generator")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    env = TetrisEnv(env_params["rows"], env_params["cols"],
                    env_params["piece_generator"], env_params["random_seed"])
    agent = TetrisAgent(env, agent_weights)
    DROP_EVENT = pygame.USEREVENT + 1
    # Set timer from configuration to control game speed
    pygame.time.set_timer(DROP_EVENT, int(ui_config["drop_interval"]/10))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == DROP_EVENT:
                # Update piece count for the current piece
                if env.current_piece:
                    piece_type = env.current_piece.shape
                    if piece_type in piece_count:
                        piece_count[piece_type] += 1
                best_move = agent.get_best_move()
                if best_move:
                    for _ in range(best_move["rotations"]):
                        env.rotate_piece(clockwise=True)
                    dx = best_move["x"] - env.current_piece.x
                    if dx > 0:
                        for _ in range(dx):
                            env.move_piece(1, 0)
                    elif dx < 0:
                        for _ in range(-dx):
                            env.move_piece(-1, 0)
                    env.hard_drop()
                else:
                    env.drop_piece()

        screen.fill(ui_config["background_color"])
        draw_grid(screen, env.grid.board)
        draw_piece(screen, env.current_piece.get_cells(), env.current_piece.color)
        draw_panel(screen, env, font)
        pygame.display.flip()

        if env.game_over:
            running = False

        clock.tick(ui_config["fps"])
    pygame.quit()

if __name__ == "__main__":
    main()
