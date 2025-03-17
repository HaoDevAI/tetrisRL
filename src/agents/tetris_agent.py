from src.agents.reward import evaluate_state

class TetrisAgent:
    """
    Agent for selecting the best move in a Tetris game environment using a linear evaluation function.
    """
    def __init__(self, game, weights):
        """
        Initialize the TetrisAgent with the game environment.

        Args:
            game: The game environment object which must provide:
                  - get_possible_moves(): returns a list of possible moves.
                  - simulate_move(move): simulates the move and returns a new state (with a board attribute).
            weights (np.array): A 4-dimensional weight vector for evaluating game states.
        """
        self.game = game
        self.weights = weights

    def get_best_move(self):
        """
        Evaluate all possible moves by simulating each move and scoring the resulting state
        using a linear evaluation function. Returns the move with the highest score.

        Returns:
            dict: The best move as a dictionary.
        """
        best_score = float('-inf')
        best_move = None

        possible_moves = self.game.get_possible_moves()

        for move in possible_moves:
            simulated_state = self.game.simulate_move(move)
            score = evaluate_state(simulated_state, self.weights)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def get_best_move_promax(self):
        """
        Find the best move by considering both the current piece and the next piece.

        For each move of the current piece, simulate and then iterate through all moves of the next piece
        (currently the current piece of the state after simulating the first move) to find the maximum total reward.

        Returns:
            dict: The move of the current piece with the highest total reward (current + next move).
        """
        beam_width = 5
        best_total_score = float('-inf')
        best_move = None

        possible_moves = self.game.get_possible_moves()

        for move in possible_moves:
            simulated_state = self.game.simulate_move(move)
            if simulated_state is None:
                continue

            current_score = evaluate_state(simulated_state, self.weights)

            next_moves = simulated_state.get_possible_moves()

            if len(next_moves) > beam_width:
                next_moves = next_moves[:beam_width]

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
