import sys
import pygame
from src.environments.env import TetrisEnv

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
PIECE_COLOR = (255, 0, 0)    # Color for the falling piece
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
    """Draw the side panel showing the next piece and lines cleared."""
    # Define panel rect
    panel_rect = pygame.Rect(WIDTH + PANEL_MARGIN, PANEL_MARGIN, PANEL_WIDTH, HEIGHT - PANEL_MARGIN * 2)
    pygame.draw.rect(screen, PANEL_BG_COLOR, panel_rect)

    # Display "Next Piece" text
    next_text = font.render("Next Piece:", True, TEXT_COLOR)
    screen.blit(next_text, (panel_rect.x + 10, panel_rect.y + 10))

    # Draw next piece in the panel (center it in a small box)
    next_piece = gm.next_piece
    # Create a temporary copy and reset its position for drawing
    temp_piece = next_piece.clone()
    # Reset position so that its drawing is relative to 0,0
    temp_piece.x = 0
    temp_piece.y = 0
    # Get the dimensions of the piece matrix
    piece_height = len(temp_piece.matrix)
    piece_width = len(temp_piece.matrix[0])
    # Calculate an offset to center the piece in a 4x4 box (or similar)
    offset_x = panel_rect.x + (PANEL_WIDTH - piece_width * BLOCK_SIZE) // 2
    offset_y = panel_rect.y + 40  # leave some space for text

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
    # Create a semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Display final score and message
    game_over_text = font.render("Game Over!", True, TEXT_COLOR)
    score_text = font.render(f"Score: {final_score}", True, TEXT_COLOR)
    play_again_text = font.render("Play again?", True, TEXT_COLOR)

    # Calculate positions for texts
    center_x = SCREEN_WIDTH // 2
    game_over_rect = game_over_text.get_rect(center=(center_x, SCREEN_HEIGHT // 2 - 100))
    score_rect = score_text.get_rect(center=(center_x, SCREEN_HEIGHT // 2 - 50))
    play_again_rect = play_again_text.get_rect(center=(center_x, SCREEN_HEIGHT // 2))

    screen.blit(game_over_text, game_over_rect)
    screen.blit(score_text, score_rect)
    screen.blit(play_again_text, play_again_rect)

    # Define button dimensions
    button_width = 100
    button_height = 50
    spacing = 20

    # Calculate positions for the two buttons (Yes and No)
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

    # Button texts
    yes_text = font.render("Yes", True, TEXT_COLOR)
    no_text = font.render("No", True, TEXT_COLOR)

    # Button loop
    waiting = True
    while waiting:
        # Redraw overlay and texts to update button hover states
        screen.blit(overlay, (0, 0))
        screen.blit(game_over_text, game_over_rect)
        screen.blit(score_text, score_rect)
        screen.blit(play_again_text, play_again_rect)

        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        # Check hover states
        yes_color = BUTTON_HOVER_COLOR if yes_button_rect.collidepoint(mouse_pos) else BUTTON_BG_COLOR
        no_color = BUTTON_HOVER_COLOR if no_button_rect.collidepoint(mouse_pos) else BUTTON_BG_COLOR

        # Draw buttons
        pygame.draw.rect(screen, yes_color, yes_button_rect)
        pygame.draw.rect(screen, no_color, no_button_rect)

        # Center text in buttons
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
    pygame.display.set_caption("Tetris AI with Pygame")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 24)

    running = True
    while running:
        env = TetrisEnv()
        drop_interval = 500
        DROP_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(DROP_EVENT, drop_interval)

        game_active = True
        while game_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_active = False
                    running = False
                elif event.type == DROP_EVENT:
                    env.drop_piece()
                elif event.type == pygame.KEYDOWN:
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


            screen.fill(BACKGROUND_COLOR)
            draw_grid(screen, env.grid.board)
            draw_piece(screen, env.current_piece.get_cells(), PIECE_COLOR)
            draw_panel(screen, env, font)
            pygame.display.flip()

            if env.game_over:
                game_active = False

            clock.tick(60)

        # Show game over screen with play again option
        play_again = check_play_again(screen, font, env.score)
        if not play_again:
            running = False

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
