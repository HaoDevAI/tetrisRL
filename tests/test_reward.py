import pygame
import time
from pathlib import Path
import numpy as np
import yaml
from src.environments.env import TetrisEnv
from src.agents.reward import compute_column_heights, compute_aggregate_height, compute_holes, compute_bumpiness, evaluate_state
from src.agents.agent import TetrisAgent
from src.utils.display import draw_grid, draw_piece, draw_panel, draw_next_piece
from src.utils.config import ui_config, SCREEN_WIDTH, SCREEN_HEIGHT, env_params, WIDTH, HEIGHT, PANEL_MARGIN, PANEL_WIDTH, AGENT_STRATEGY

# Load agent weights and config for evaluation
FILE_DIR = Path(__file__).parent.parent
CONFIG_PATH = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
AGENT_DIR = FILE_DIR / 'logs' / "ref"
VERSION = "best"
WEIGHTS_PATH = AGENT_DIR / f"{VERSION}.npy"
agent_weights = np.load(WEIGHTS_PATH)


def draw_panel(screen, env, font, agent_weights):
    panel_rect = pygame.Rect(WIDTH + PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH, HEIGHT - 2 * PANEL_MARGIN)
    pygame.draw.rect(screen, ui_config["panel_bg_color"], panel_rect)
    draw_next_piece(screen, env, panel_rect, font)
    y_offset = panel_rect.y + 150
    title = font.render(f"Score: {env.score}", True, ui_config["text_color"])
    screen.blit(title, (panel_rect.x + 10, y_offset))

    board = env.grid.board
    rows, cols = env.grid.rows, env.grid.cols
    heights = compute_column_heights(board, rows, cols)
    aggregate = compute_aggregate_height(heights)
    holes = compute_holes(board, rows, cols)
    bumpiness = compute_bumpiness(heights)
    reward_value = evaluate_state(env, agent_weights)

    lines = [
        f"Aggregate: {aggregate}",
        f"Lines: {env.grid.lines_cleared}",
        f"Holes: {holes}",
        f"Bumpiness: {bumpiness}",
        f"Reward: {reward_value:.2f}"
    ]

    y_offset = panel_rect.y + 200
    for line in lines:
        text_surface = font.render(line, True, ui_config["text_color"])
        screen.blit(text_surface, (panel_rect.x + 10, y_offset))
        y_offset += 30


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Test Reward")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    # Fixed weight vector for reward evaluation (could be same as agent_weights)
    # For this example, we use the agent_weights loaded from file.

    env = TetrisEnv(env_params["rows"], env_params["cols"],
                    env_params["piece_generator"], env_params["random_seed"])
    agent = TetrisAgent(env, agent_weights, AGENT_STRATEGY)
    DROP_EVENT = pygame.USEREVENT + 1
    # Set timer based on config drop_interval
    pygame.time.set_timer(DROP_EVENT, int(ui_config["drop_interval"]/10))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == DROP_EVENT:
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
        draw_panel(screen, env, font, agent_weights)
        pygame.display.flip()

        if env.game_over:
            running = False

        clock.tick(ui_config["fps"])
    pygame.quit()


if __name__ == "__main__":
    main()
