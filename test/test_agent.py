# test_agent.py

import sys
import pygame
import time
from src.environments.env import GameManager
from src.agents.linear_agent import TetrisAgent

GAME_FPS = 60  #default 60
AGENT_DELAY = 0.05  #default 0.2
DROP_INTERVAL = 100 #default 500

# Configuration
BLOCK_SIZE = 30  # Size of one grid cell in pixels
COLUMNS = 10
ROWS = 20
WIDTH = COLUMNS * BLOCK_SIZE
HEIGHT = ROWS * BLOCK_SIZE

# Panel configuration for next piece and score
PANEL_WIDTH = 6 * BLOCK_SIZE
PANEL_MARGIN = 10
SCREEN_WIDTH = WIDTH + PANEL_WIDTH + PANEL_MARGIN * 2
SCREEN_HEIGHT = HEIGHT

# Colors (R, G, B)
BACKGROUND_COLOR = (0, 0, 0)
GRID_COLOR = (40, 40, 40)
PIECE_COLOR = (255, 0, 0)    # Color for the falling piece (agent-controlled)
PLACED_COLOR = (0, 255, 0)   # Color for the placed pieces
PANEL_BG_COLOR = (50, 50, 50)
TEXT_COLOR = (255, 255, 255)
BUTTON_BG_COLOR = (70, 70, 70)
BUTTON_HOVER_COLOR = (100, 100, 100)

def draw_grid(screen, board):
    """Draw the grid with placed blocks."""
    for y in range(ROWS):
        for x in range(COLUMNS):
            rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            # Draw grid cell border
            pygame.draw.rect(screen, GRID_COLOR, rect, 1)
            # If there is a placed block, fill it in
            if board[y][x]:
                pygame.draw.rect(screen, PLACED_COLOR, rect)

def draw_piece(screen, cells, color):
    """Draw a piece using the provided cell coordinates and color."""
    for (x, y) in cells:
        rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
        pygame.draw.rect(screen, color, rect)

def draw_panel(screen, gm, font):
    """Draw the side panel showing the next piece and score."""
    # Define panel rect
    panel_rect = pygame.Rect(WIDTH + PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH, HEIGHT - PANEL_MARGIN * 2)
    pygame.draw.rect(screen, PANEL_BG_COLOR, panel_rect)

    # Display "Next Piece" text
    next_text = font.render("Next Piece:", True, TEXT_COLOR)
    screen.blit(next_text, (panel_rect.x + 10, panel_rect.y + 10))

    # Draw next piece in the panel (center it in a small box)
    next_piece = gm.next_piece
    # Create a temporary copy và reset vị trí để vẽ
    temp_piece = next_piece.clone()
    temp_piece.x = 0
    temp_piece.y = 0
    # Tính toán kích thước piece (giả sử piece.matrix là ma trận của piece)
    piece_height = len(temp_piece.matrix)
    piece_width = len(temp_piece.matrix[0])
    offset_x = panel_rect.x + (PANEL_WIDTH - piece_width * BLOCK_SIZE) // 2
    offset_y = panel_rect.y + 40  # khoảng cách từ text

    for i, row in enumerate(temp_piece.matrix):
        for j, val in enumerate(row):
            if val:
                rect = pygame.Rect(offset_x + j * BLOCK_SIZE, offset_y + i * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(screen, PIECE_COLOR, rect)

    # Display "Lines Cleared" (score)
    score_text = font.render(f"Lines: {gm.score}", True, TEXT_COLOR)
    screen.blit(score_text, (panel_rect.x + 10, panel_rect.y + 150))

def check_play_again(screen, font, final_score):
    """Display a game over screen with score and Yes/No buttons for replay.
       Returns True if player clicks Yes, False if No.
    """
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    game_over_text = font.render("Game Over!", True, TEXT_COLOR)
    score_text = font.render(f"Score: {final_score}", True, TEXT_COLOR)
    play_again_text = font.render("Play again?", True, TEXT_COLOR)

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

    yes_text = font.render("Yes", True, TEXT_COLOR)
    no_text = font.render("No", True, TEXT_COLOR)

    waiting = True
    while waiting:
        screen.blit(overlay, (0, 0))
        screen.blit(game_over_text, game_over_rect)
        screen.blit(score_text, score_rect)
        screen.blit(play_again_text, play_again_rect)

        mouse_pos = pygame.mouse.get_pos()
        yes_color = BUTTON_HOVER_COLOR if yes_button_rect.collidepoint(mouse_pos) else BUTTON_BG_COLOR
        no_color = BUTTON_HOVER_COLOR if no_button_rect.collidepoint(mouse_pos) else BUTTON_BG_COLOR

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
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris AI Agent")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    running = True
    while running:
        # Khởi tạo game mới và agent
        gm = GameManager()
        agent = TetrisAgent(gm)
        drop_interval = DROP_INTERVAL
        DROP_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(DROP_EVENT, drop_interval)

        game_active = True

        # Agent sẽ tính toán và thực hiện nước đi ngay khi có thể.
        agent_move_made = False
        last_move_time = time.time()

        while game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_active = False
                    running = False
                elif event.type == DROP_EVENT:
                    # Nếu agent chưa thực hiện nước đi và đã chờ đủ thời gian, thực hiện nước đi tự động.
                    if not agent_move_made and (time.time() - last_move_time) > AGENT_DELAY:
                        best_move = agent.get_best_move()
                        if best_move is not None:
                            # Thực hiện các xoay cần thiết
                            for _ in range(best_move["rotations"]):
                                gm.rotate_piece(clockwise=True)
                            # Di chuyển mảnh về vị trí x được chọn
                            gm.current_piece.x = best_move["x"]
                            # Thực hiện hard drop
                            gm.hard_drop()
                        agent_move_made = True
                        last_move_time = time.time()
                    else:
                        # Nếu agent đã thực hiện nước đi, cập nhật game theo drop_piece (hoặc tự động)
                        gm.drop_piece()
                        agent_move_made = False

            screen.fill(BACKGROUND_COLOR)
            draw_grid(screen, gm.grid.board)
            draw_piece(screen, gm.current_piece.get_cells(), PIECE_COLOR)
            draw_panel(screen, gm, font)
            pygame.display.flip()

            if gm.game_over:
                game_active = False

            clock.tick(GAME_FPS)

        # Sau khi game kết thúc, hiển thị màn hình game over với lựa chọn chơi lại.
        play_again = check_play_again(screen, font, gm.score)
        if not play_again:
            running = False

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
