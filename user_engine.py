import numpy as np
import os
import pygame
from engine import TetrisEngine, BOARD_WIDTH, BOARD_HEIGHT, BLOCK_SIZE, BG_COLOR, GRID_COLOR, PIECE_COLOR

pygame.init()
# Create a Pygame window based on the board dimensions and block size
screen = pygame.display.set_mode((BOARD_WIDTH * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE))
pygame.display.set_caption("Tetris")

def play_game():
    db = []  # to store (state, reward, done, action) for training
    reward_sum = 0
    done = False
    clock = pygame.time.Clock()

    # Timer variables for automatic drop
    drop_interval = 500  # milliseconds between automatic soft drops
    last_drop_time = pygame.time.get_ticks()

    while not done:
        action = None  # no immediate action by default

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
                break
            elif event.type == pygame.KEYDOWN:
                # Map key presses to engine actions
                if event.key == pygame.K_a:      # Shift left
                    action = 0
                elif event.key == pygame.K_d:    # Shift right
                    action = 1
                elif event.key == pygame.K_w:    # Hard drop
                    action = 2
                elif event.key == pygame.K_s:    # Soft drop
                    action = 3
                elif event.key == pygame.K_q:    # Rotate left
                    action = 4
                elif event.key == pygame.K_e:    # Rotate right
                    action = 5

        # Check timer for automatic soft drop if no key was pressed
        current_time = pygame.time.get_ticks()
        if action is None and (current_time - last_drop_time >= drop_interval):
            action = 3  # soft drop action

        # If an action was triggered (either by key or auto drop), update the engine
        if action is not None:
            state, reward, done = env.step(action)
            reward_sum += reward
            db.append(np.array((state, reward, done, action), dtype="object"))
            last_drop_time = current_time  # reset drop timer

        # Render the game
        env.draw(screen)
        pygame.display.flip()

        # Limit the loop to 60 FPS
        clock.tick(60)

    return db

def play_again():
    choice = input("Play Again? [y/n] > ")
    return True if choice.lower() == 'y' else False

def prompt_save_game(db):
    print('Accumulated reward: {0} | {1} moves'.format(sum([i[1] for i in db]), len(db)))
    choice = input('Would you like to store the game info as training data? [y/n] > ')
    return True if choice.lower() == 'y' else False

def save_game(db, path='training_data.npy'):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        print('No training file exists. Creating one now...')
        print('Saving {0} moves...'.format(len(db)))
        np.save(path, db)
    else:
        x = np.load(path, allow_pickle=True)
        x = np.concatenate((x, db))
        np.save(path, x)
        print('{0} data points in the training set'.format(len(x)))

if __name__ == '__main__':
    # Initialize the Tetris engine with board dimensions (e.g. 10x20)
    width, height = 10, 20
    env = TetrisEngine(width, height)

    # Main game loop (play multiple games)
    while True:
        env.clear()       # Reset the board and game state
        db = play_game()  # Play one game and collect training data

        # After the game ends, prompt the user for saving data
        if prompt_save_game(db):
            save_game(db)
        # Ask if the user wants to play again
        if not play_again():
            print('Thanks for contributing!')
            break

    pygame.quit()
