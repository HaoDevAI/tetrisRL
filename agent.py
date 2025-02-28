import math
import random
import sys, os, shutil
import numpy as np
from collections import namedtuple
from itertools import count
from copy import deepcopy

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.autograd import Variable

from engine import TetrisEngine

# Tetris game dimensions and engine setup
width, height = 10, 20  # Standard Tetris dimensions
engine = TetrisEngine(width, height)

# Device configuration
use_cuda = torch.cuda.is_available()
if use_cuda:
    print("....Using GPU...")
FloatTensor = torch.cuda.FloatTensor if use_cuda else torch.FloatTensor
LongTensor = torch.cuda.LongTensor if use_cuda else torch.LongTensor
ByteTensor = torch.cuda.ByteTensor if use_cuda else torch.ByteTensor

# -------------------------------
# Replay Memory (Uniform version shown; you may swap in a prioritized version)
# -------------------------------
Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))


class ReplayMemory(object):
    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def push(self, *args):
        """Save a transition."""
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


# -------------------------------
# New Dueling DQN Network Architecture
# -------------------------------
class DuelingDQN(nn.Module):
    def __init__(self, input_dim, n_actions):
        """
        input_dim: dimension of flattened state vector (e.g., board features)
        n_actions: number of possible actions in Tetris
        """
        super().__init__()
        # Common feature layers
        self.fc1 = nn.Linear(input_dim, 512)
        self.fc2 = nn.Linear(512, 256)

        # Value stream
        self.value_fc = nn.Linear(256, 128)
        self.value = nn.Linear(128, 1)

        # Advantage stream
        self.advantage_fc = nn.Linear(256, 128)
        self.advantage = nn.Linear(128, n_actions)

    def forward(self, x):
        # Flatten if needed (assumes x is of shape [batch, ...])
        if len(x.shape) > 2:
            x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        # Separate streams
        val = F.relu(self.value_fc(x))
        val = self.value(val)
        adv = F.relu(self.advantage_fc(x))
        adv = self.advantage(adv)
        # Combine: Q = V + (A - mean(A))
        q_vals = val + (adv - adv.mean(dim=1, keepdim=True))
        return q_vals


# Hyperparameters
MAX_EPISODES = 1000
BATCH_SIZE = 64
GAMMA = 0.99  # Use a slightly lower discount to help with long-term credit assignment
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 200
TARGET_UPDATE = 10  # Update target network every TARGET_UPDATE episodes
CHECKPOINT_FILE = 'checkpoint_dueling_dqn.pth.tar'

steps_done = 0


# -------------------------------
# Epsilon-Greedy Action Selection
# -------------------------------
@torch.no_grad()
def select_action(state):
    global EPS_DECAY, EPS_START, EPS_END
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1
    if sample > eps_threshold:
        # Use online network to select best action
        model.eval()
        q_vals = model(state.type(FloatTensor))
        action = q_vals.max(1)[1].view(1, 1)
        model.train()
        return action, steps_done
    else:
        return LongTensor([[random.randrange(engine.nb_actions)]]), steps_done


# -------------------------------
# Initialize Networks and Optimizer
# -------------------------------
# Determine the input dimension for your network.
# For example, if engine.clear() returns a (height, width) grid, then:
input_dim = width * height  # adjust if you have extra features

n_actions = engine.nb_actions  # assuming your engine provides the number of legal actions

model = DuelingDQN(input_dim, n_actions)
target_model = DuelingDQN(input_dim, n_actions)
target_model.load_state_dict(model.state_dict())
target_model.eval()

if use_cuda:
    model.cuda()
    target_model.cuda()

optimizer = optim.Adam(model.parameters(), lr=1e-4)  # Adam is robust and commonly used

memory = ReplayMemory(10000)


# -------------------------------
# Optimize Model with Double DQN update
# -------------------------------
def optimize_model():
    if len(memory) < BATCH_SIZE:
        return None
    transitions = memory.sample(BATCH_SIZE)
    batch = Transition(*zip(*transitions))

    # Create masks for non-terminal states
    non_final_mask = ByteTensor(tuple(s is not None for s in batch.next_state))
    non_final_mask = non_final_mask.bool()
    non_final_next_states = torch.cat([s for s in batch.next_state if s is not None])
    state_batch = torch.cat(batch.state)
    action_batch = torch.cat(batch.action)
    reward_batch = torch.cat(batch.reward)

    # Compute current Q values from online network
    state_action_values = model(state_batch).gather(1, action_batch)

    # Double DQN: select next action using online network, evaluate with target network
    next_state_q = torch.zeros(BATCH_SIZE).type(FloatTensor)
    if non_final_next_states.size(0) > 0:
        # Get the actions with max Q from the online network
        next_actions = model(non_final_next_states).max(1)[1].unsqueeze(1)
        # Evaluate those actions using the target network
        next_state_q[non_final_mask] = target_model(non_final_next_states).gather(1, next_actions).squeeze(1)

    # Compute expected Q values
    expected_state_action_values = reward_batch + (GAMMA * next_state_q)

    # Compute Huber loss (Smooth L1)
    loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(1))
    optimizer.zero_grad()
    loss.backward()
    # Gradient clipping
    for param in model.parameters():
        param.grad.data.clamp_(-1, 1)
    optimizer.step()
    return loss.item()


# -------------------------------
# Checkpointing functions (unchanged)
# -------------------------------
def save_checkpoint(state, is_best, filename=CHECKPOINT_FILE):
    torch.save(state, filename)
    if is_best:
        shutil.copyfile(filename, 'model_best_dueling_dqn.pth.tar')


def load_checkpoint(filename):
    checkpoint = torch.load(filename)
    model.load_state_dict(checkpoint['state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer'])
    memory_loaded = checkpoint.get('memory', None)
    return checkpoint['epoch'], checkpoint['best_score'], memory_loaded


# -------------------------------
# Main Training Loop
# -------------------------------
if __name__ == '__main__':
    start_episode = 0
    best_score = -float('inf')
    if len(sys.argv) > 1 and sys.argv[1] == 'resume':
        if len(sys.argv) > 2:
            CHECKPOINT_FILE = sys.argv[2]
        if os.path.isfile(CHECKPOINT_FILE):
            print("=> loading checkpoint '{}'".format(CHECKPOINT_FILE))
            start_episode, best_score, mem = load_checkpoint(CHECKPOINT_FILE)
            if mem is not None:
                memory.memory = mem.memory
            print("=> loaded checkpoint '{}' (episode {})".format(CHECKPOINT_FILE, start_episode))
        else:
            print("=> no checkpoint found at '{}'".format(CHECKPOINT_FILE))

    steps_done = 0

    f = open('log_dueling.out', 'w+')
    for i_episode in range(start_episode, MAX_EPISODES):
        # Reset environment and get initial state.
        # Here we assume engine.clear() returns a 2D grid; we flatten it.
        state_np = engine.clear()  # shape: [height, width]
        state = FloatTensor(state_np.flatten()[None, :])  # [1, input_dim]

        episode_score = 0
        for t in count():
            action, steps_done = select_action(state)
            last_state = state.clone()
            # Execute action in the engine:
            next_state_np, reward, done = engine.step(action.item())
            next_state = FloatTensor(next_state_np.flatten()[None, :])
            episode_score += int(reward)
            reward_tensor = FloatTensor([float(reward)])
            # Save transition only if reward is significant (optional filter)
            if reward != 0:
                memory.push(last_state, action, next_state if not done else None, reward_tensor)
            # Move to next state
            state = next_state

            # Perform optimization step
            loss_val = optimize_model()

            if done:
                print(f"Episode {i_episode}: score {episode_score} (steps: {t})")
                f.write(f"Episode {i_episode}: score {episode_score}\n")
                break

        # Update target network periodically (Double DQN)
        if i_episode % TARGET_UPDATE == 0:
            target_model.load_state_dict(model.state_dict())

        # Save checkpoint every 100 episodes
        if i_episode % 100 == 0:
            is_best = episode_score > best_score
            best_score = max(episode_score, best_score)
            save_checkpoint({
                'episode': i_episode,
                'state_dict': model.state_dict(),
                'best_score': best_score,
                'optimizer': optimizer.state_dict(),
                'memory': memory
            }, is_best)
    f.close()
    print('Training Complete')
