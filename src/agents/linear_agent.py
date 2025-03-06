from src.agents.policy import evaluate_state


class TetrisAgent:
    def __init__(self, game,weights):
        """
        Khởi tạo agent với game environment.
        game: đối tượng môi trường game của bạn cần cung cấp các hàm:
              - get_possible_moves(): trả về danh sách các nước đi khả dĩ.
              - simulate_move(move): mô phỏng nước đi và trả về state mới (có thuộc tính board).
        """
        self.game = game
        self.weights = weights

    def get_best_move(self):
        """
        Duyệt qua tất cả các nước đi khả dĩ, mô phỏng và tính điểm cho state sau khi thực hiện
        nước đi đó dựa trên hàm đánh giá tuyến tính. Trả về nước đi có điểm số cao nhất.
        """
        best_score = float('-inf')
        best_move = None

        # Lấy danh sách các nước đi khả dĩ từ môi trường game
        possible_moves = self.game.get_possible_moves()

        # Duyệt qua từng nước đi
        for move in possible_moves:
            # Mô phỏng nước đi để nhận state mới
            simulated_state = self.game.simulate_move(move)
            # Tính điểm cho state dựa trên hàm đánh giá (linear evaluation function)
            score = evaluate_state(simulated_state,self.weights)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move



