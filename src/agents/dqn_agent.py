import random
import numpy as np
from collections import namedtuple, deque

import torch
import torch.nn as nn
import torch.optim as optim

# Định nghĩa một transition để lưu trữ kinh nghiệm
Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))


class DQN(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        """
        Một mạng neural đơn giản với 2 lớp ẩn.
        input_size: kích thước vector đặc trưng của state (có thể là các đặc trưng đã được trích xuất từ board).
        output_size: số lượng hành động có thể thực hiện.
        """
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)


class DQNAgent:
    def __init__(self,
                 state_size,
                 action_size,
                 device='cpu',
                 memory_size=10000,
                 batch_size=64,
                 gamma=0.99,
                 lr=1e-3,
                 epsilon_start=1.0,
                 epsilon_end=0.01,
                 epsilon_decay=0.995):
        """
        state_size: kích thước của vector đặc trưng state.
        action_size: số lượng hành động (ví dụ: số nước đi khả dĩ trong Tetris).
        device: thiết bị tính toán (cpu hoặc cuda).
        memory_size: kích thước bộ nhớ replay.
        batch_size: kích thước mini-batch dùng để tối ưu.
        gamma: hệ số giảm giá (discount factor).
        lr: learning rate.
        epsilon_*: các tham số cho chiến lược ε-greedy.
        """
        self.state_size = state_size
        self.action_size = action_size
        self.device = device

        # Replay memory để lưu trữ các trải nghiệm
        self.memory = deque(maxlen=memory_size)
        self.batch_size = batch_size
        self.gamma = gamma

        # ε-greedy parameters
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay

        # Policy network và target network
        self.policy_net = DQN(state_size, 128, action_size).to(device)
        self.target_net = DQN(state_size, 128, action_size).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)

    def select_action(self, state):
        """
        Lựa chọn hành động theo chiến lược ε-greedy.
        state: vector đặc trưng của trạng thái hiện tại (đã được tiền xử lý).
        """
        if random.random() < self.epsilon:
            return random.randrange(self.action_size)
        else:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                return q_values.argmax().item()

    def store_transition(self, state, action, next_state, reward):
        """
        Lưu trữ kinh nghiệm (transition) vào bộ nhớ replay.
        next_state có thể là None nếu trạng thái kết thúc.
        """
        self.memory.append(Transition(state, action, next_state, reward))

    def optimize_model(self):
        """
        Lấy ngẫu nhiên một batch các transition từ replay memory và cập nhật mạng policy.
        """
        if len(self.memory) < self.batch_size:
            return

        transitions = random.sample(self.memory, self.batch_size)
        batch = Transition(*zip(*transitions))

        state_batch = torch.FloatTensor(batch.state).to(self.device)
        action_batch = torch.LongTensor(batch.action).unsqueeze(1).to(self.device)
        reward_batch = torch.FloatTensor(batch.reward).to(self.device)

        # Xử lý next_state (loại bỏ những transition kết thúc)
        non_final_mask = torch.tensor(tuple(s is not None for s in batch.next_state), dtype=torch.bool,
                                      device=self.device)
        non_final_next_states = torch.FloatTensor([s for s in batch.next_state if s is not None]).to(self.device)

        # Tính Q-value hiện tại từ policy network
        current_q_values = self.policy_net(state_batch).gather(1, action_batch)

        # Tính Q-value dự đoán cho các trạng thái tiếp theo từ target network
        next_q_values = torch.zeros(self.batch_size, device=self.device)
        if non_final_next_states.size(0) > 0:
            next_q_values[non_final_mask] = self.target_net(non_final_next_states).max(1)[0].detach()

        expected_q_values = reward_batch + (self.gamma * next_q_values)

        # Tính loss theo hàm MSE
        loss = nn.MSELoss()(current_q_values.squeeze(), expected_q_values)

        # Cập nhật trọng số cho policy network
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def update_epsilon(self):
        """
        Giảm epsilon dần dần theo ε-decay.
        """
        if self.epsilon > self.epsilon_end:
            self.epsilon *= self.epsilon_decay

    def update_target_network(self):
        """
        Đồng bộ trọng số từ policy network sang target network.
        """
        self.target_net.load_state_dict(self.policy_net.state_dict())


# Ví dụ sử dụng (giả sử môi trường game đã cung cấp vector đặc trưng state và danh sách hành động có thể)
if __name__ == "__main__":
    # Giả định state được biểu diễn bởi vector 4 đặc trưng: [aggregate_height, complete_lines, holes, bumpiness]
    # Bạn có thể sử dụng các hàm trong policies.py để trích xuất các đặc trưng này từ board
    state_size = 4
    action_size = 6  # ví dụ: 6 nước đi khả dĩ cho mỗi mảnh

    agent = DQNAgent(state_size, action_size, device='cpu')

    # Giả lập một số bước trong game
    for episode in range(10):
        # Reset môi trường và lấy state ban đầu (ở đây ta chỉ mô phỏng với state ngẫu nhiên)
        state = np.random.rand(state_size)
        done = False
        total_reward = 0

        while not done:
            action = agent.select_action(state)
            # Ở đây bạn sẽ tích hợp với môi trường game: thực hiện action, nhận next_state và reward
            # Ví dụ giả lập:
            next_state = np.random.rand(state_size)  # trạng thái mới
            reward = random.random()  # phần thưởng giả định
            total_reward += reward

            # Giả sử có xác định trạng thái kết thúc ngẫu nhiên
            if random.random() < 0.1:
                next_state = None
                done = True

            agent.store_transition(state, action, next_state, reward)
            state = next_state if next_state is not None else np.random.rand(state_size)

            # Tối ưu mô hình
            agent.optimize_model()
            agent.update_epsilon()

        # Cập nhật target network theo chu kỳ hoặc số bước nhất định
        agent.update_target_network()
        print(f"Episode {episode + 1}: Total Reward = {total_reward:.2f}, Epsilon = {agent.epsilon:.3f}")
