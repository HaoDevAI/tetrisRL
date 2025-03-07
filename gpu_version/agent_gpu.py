from policy_gpu import evaluate_state

class TetrisAgentGPU:
    def __init__(self, game, weights):
        """
        Khởi tạo agent với môi trường game GPU batch.
        game: đối tượng môi trường game batch (ví dụ: TetrisEnvGPU_Batch) cần cung cấp:
              - get_possible_moves(): trả về list các nước đi khả dĩ cho từng game (list có độ dài = batch_size),
              - simulate_move(move, game_index): mô phỏng nước đi cho game thứ game_index và trả về state mới.
        weights: vector trọng số dùng cho hàm evaluate_state.
        """
        self.game = game
        self.weights = weights

    def get_best_move(self):
        """
        Đối với mỗi game trong batch, duyệt qua các nước đi khả dĩ, mô phỏng và tính điểm cho state sau khi thực hiện
        nước đi đó dựa trên hàm evaluate_state. Trả về một list (độ dài = batch_size) chứa nước đi tốt nhất cho từng game.
        Mỗi nước đi được biểu diễn dưới dạng dict với khóa "rotations" và "x".
        """
        best_moves = [None] * self.game.batch_size
        # Lấy danh sách các nước đi khả dĩ cho từng game trong batch
        possible_moves_batch = self.game.get_possible_moves()  # List với độ dài = batch_size; mỗi phần tử là list các dict (hoặc None)
        for i, moves in enumerate(possible_moves_batch):
            if moves is None or len(moves) == 0:
                best_moves[i] = None
                continue
            best_score = float('-inf')
            best_move = None
            for move in moves:
                simulated_state = self.game.simulate_move(move, i)
                if simulated_state is None:
                    continue
                score = evaluate_state(simulated_state, self.weights)
                if score > best_score:
                    best_score = score
                    best_move = move
            best_moves[i] = best_move
        return best_moves

# Example usage:
if __name__ == "__main__":
    # Giả sử bạn đã khởi tạo môi trường batch (ví dụ, TetrisEnvGPU_Batch) và vector trọng số
    # Tạo agent GPU từ môi trường batch đó
    from env_gpu import TetrisEnvGPU_Batch  # đảm bảo file env.py đã được chuyển sang GPU batch
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    batch_size = 16
    # Giả sử weights được định nghĩa dưới dạng numpy array hoặc tensor
    weights = [ -0.510066, 0.760666, -0.35663, -0.184483 ]
    # Khởi tạo môi trường và agent
    env = TetrisEnvGPU_Batch(batch_size=batch_size, device=device)
    agent = TetrisAgentGPU(env, weights)
    best_moves = agent.get_best_move()
    print("Best moves for each game in batch:", best_moves)
