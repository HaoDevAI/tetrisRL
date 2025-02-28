import sys
import os
import torch
import time
import pygame
import numpy as np
from engine import TetrisEngine, BOARD_WIDTH, BOARD_HEIGHT, BLOCK_SIZE, BG_COLOR, GRID_COLOR, PIECE_COLOR
from agent import DuelingDQN, ReplayMemory, Transition
from torch.autograd import Variable

use_cuda = torch.cuda.is_available()

FloatTensor = torch.cuda.FloatTensor if use_cuda else torch.FloatTensor
LongTensor = torch.cuda.LongTensor if use_cuda else torch.LongTensor

# Initialize the Tetris engine with standard dimensions
engine = TetrisEngine(BOARD_WIDTH, BOARD_HEIGHT)
input_dim = 10 * 20  # adjust if you have extra features

n_actions = engine.nb_actions  # assuming your engine provides the number of legal actions

def load_model(filename):
    model = DuelingDQN(input_dim, n_actions)
    if use_cuda:
        model.cuda()
    checkpoint = torch.load(filename, weights_only=False)
    model.load_state_dict(checkpoint['state_dict'])
    return model


def run(model):
    # Initialize Pygame window
    pygame.init()
    screen = pygame.display.set_mode((BOARD_WIDTH * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE))
    pygame.display.set_caption("Tetris - DQN Run")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)

    # Reset environment and get initial state
    state = FloatTensor(engine.clear()[None, None, :, :])
    score = 0
    done = False

    while not done:
        # Use the model to choose an action
        with torch.no_grad():
            # Forward pass through the model
            action = model(Variable(state).type(FloatTensor)).data.max(1)[1].view(1, 1).type(LongTensor)

        # Take a step in the environment
        state, reward, done = engine.step(action.item())
        state = FloatTensor(state[None, None, :, :])
        score += int(reward)

        # Process Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        # Render the board using the engine's draw method
        engine.draw(screen)

        # Render score information on the screen
        score_text = font.render(f"Cumulative Reward: {score}   Reward: {reward}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(10)  # Adjust FPS as needed
        time.sleep(0.1)

    print(f'score {score}')


if len(sys.argv) <= 1:
    print('specify a filename to load the model')
    sys.exit(1)

if __name__ == '__main__':
    filename = sys.argv[1]
    if os.path.isfile(filename):
        print("=> loading model '{}'".format(filename))
        model = load_model(filename).eval()
        run(model)
    else:
        print("=> no file found at '{}'".format(filename))
