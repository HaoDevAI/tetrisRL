from src.agents.reward import evaluate_state


class TetrisAgent:
    """Agent for selecting the best Tetris move using linear evaluation."""

    def __init__(self, env, weights, mode='normal'):
        """
        Initialize the agent.

        Args:
            env: Tetris environment.
            weights (np.array): Weight vector for state evaluation.
        """
        self.env = env
        self.weights = weights
        self.mode = mode

    def get_best_move_normal(self):
        """
        Compute the best move based on state evaluation.

        Returns:
            dict: The best move.
        """
        best_score = float('-inf')
        best_move = None
        for move in self.env.get_possible_moves():
            simulated_state = self.env.simulate_move(move)
            score = evaluate_state(simulated_state, self.weights)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def get_best_move_promax(self):
        """
        Compute the best move considering current and next moves.

        Returns:
            dict: The best move.
        """
        beam_width = 10
        possible_moves = self.env.get_possible_moves()

        current_moves_info = []
        for move in possible_moves:
            simulated_state = self.env.simulate_move(move)
            if simulated_state is None:
                continue
            current_score = evaluate_state(simulated_state, self.weights)
            current_moves_info.append((move, current_score, simulated_state))

        current_moves_info.sort(key=lambda x: x[1], reverse=True)

        best_total_score = float('-inf')
        best_move = None

        for move, current_score, simulated_state in current_moves_info[:beam_width]:
            next_moves = simulated_state.get_possible_moves()
            best_next_score = float('-inf')
            for next_move in next_moves:
                next_state = simulated_state.simulate_move(next_move)
                if next_state is None:
                    continue
                score_next = evaluate_state(next_state, self.weights)
                if score_next > best_next_score:
                    best_next_score = score_next
            if best_next_score == float('-inf'):
                best_next_score = 0
            total_score = current_score + best_next_score
            if total_score > best_total_score:
                best_total_score = total_score
                best_move = move

        return best_move

    def get_best_move(self):
        """
        Select the best move based on the agent's evaluation mode.

        Returns:
            dict: The best move.
        """
        if self.mode == "normal":
            return self.get_best_move_normal()
        elif self.mode == "promax":
            return self.get_best_move_promax()
