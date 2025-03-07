import random
import torch
from piece_gpu import PieceGPUBatch, SHAPES

def random_piece_generator_gpu_batch(batch_size, device='cuda'):
    """
    Chọn ngẫu nhiên một Tetris piece và trả về một instance của PieceGPUBatch với batch_size.
    Lưu ý: Hiện tại, toàn bộ batch sẽ có cùng một shape được chọn ngẫu nhiên.
    """
    shape = random.choice(list(SHAPES.keys()))
    return PieceGPUBatch(batch_size, shape, device=device)

# Example usage:
if __name__ == "__main__":
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    batch_size = 4
    piece_batch = random_piece_generator_gpu_batch(batch_size, device=device)
    print("Generated piece shape:", piece_batch.shape)
    cells = piece_batch.get_cells_batch()
    for i, cell in enumerate(cells):
        print(f"Game {i} cells:", cell.cpu().numpy())
