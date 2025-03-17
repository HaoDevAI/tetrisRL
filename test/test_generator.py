import numpy as np
import pygame
import time
from src.environments.env import TetrisEnv
from src.agents.tetris_agent import TetrisAgent
from utils.UI import *
piece_count = {"I": 0, "O": 0, "T": 0, "S": 0, "Z": 0, "J": 0, "L": 0}
# Agent information and file paths
AGENT = "ref"
VERSION = "best"

FILE_DIR = Path(__file__).parent.parent
CONFIG_PATH = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
AGENT_DIR = FILE_DIR / 'logs' / AGENT
WEIGHTS_PATH = AGENT_DIR / f"{VERSION}.npy"
TEST_LOGS_PATH = AGENT_DIR / 'test_results.txt'
SAVE_MODE = False

# Load game config
with open(CONFIG_PATH, 'r') as f:
    config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]

#Agent strategy
AGENT_STRATEGY = config['strategy']


NUM_GAMES = 0  # Background games for agent's evaluation

def draw_panel(screen, env, font):
    """
    Draw the side panel including next piece, current score, and background simulation statistics.

    Args:
        screen (pygame.Surface): The game screen surface.
        env (TetrisEnv): The current Tetris game environment.
        font (pygame.font.Font): The font used for rendering text.
    """
    panel_rect = pygame.Rect(WIDTH + PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH, HEIGHT - PANEL_MARGIN * 2)
    pygame.draw.rect(screen, ui_config["panel_bg_color"], panel_rect)

    # Next Piece preview.
    draw_next_piece(screen, env, panel_rect, font)

    score_text = font.render(f"Score: {env.score}", True, ui_config["text_color"])
    screen.blit(score_text, (panel_rect.x + 10, panel_rect.y + 150))

    y_offset = 250
    for piece, count in piece_count.items():
        piece_text = font.render(f"{piece}: {count}", True, ui_config["text_color"])
        screen.blit(piece_text, (panel_rect.x + 10, panel_rect.y + y_offset))
        y_offset += 30

def main():
    """
    Main function to run the Tetris agent UI and background simulation.
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris AI Agent")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    env = TetrisEnv(env_params["rows"], env_params["cols"],
                    generator=env_params["piece_generator"], seed=env_params["random_seed"])
    load_weights = np.load(WEIGHTS_PATH)
    pygame.time.set_timer(pygame.USEREVENT + 1, int(ui_config["drop_interval"]/10))
    running = True

    while running:
        env.reset()
        agent = TetrisAgent(env, load_weights)
        game_active = True
        last_move_time = time.time()

        while game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_active = False
                    running = False
                elif event.type == pygame.USEREVENT + 1:
                    if env.current_piece:
                        piece_type = env.current_piece.shape  # Giả sử mỗi viên có thuộc tính piece_type
                        if piece_type in piece_count:
                            piece_count[piece_type] += 1
                    if (time.time() - last_move_time) > ui_config["agent_delay"]:
                        best_move = agent.get_best_move_promax()
                        if best_move is not None:
                            for _ in range(best_move["rotations"]):
                                env.rotate_piece(clockwise=True)
                            env.current_piece.x = best_move["x"]
                            env.hard_drop()
                            env.moves_played += 1
                        else:
                            env.drop_piece()
                            env.moves_played += 1
                        last_move_time = time.time()

            screen.fill(ui_config["background_color"])
            draw_grid(screen, env.grid.board)
            draw_piece(screen, env.current_piece.get_cells(), env.current_piece.color)
            draw_panel(screen, env, font)
            pygame.display.flip()

            if env.game_over:
                play_again = check_play_again(screen, font, env.score)
                if play_again:
                    game_active = False  # Restart game
                else:
                    running = False
                    game_active = False

            clock.tick(ui_config["fps"])

    pygame.quit()

if __name__ == "__main__":
    main()