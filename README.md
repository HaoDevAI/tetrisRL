# TetrisRL: Evolving a Tetris AI with Reinforcement Learning

Welcome to **TetrisRL**, a project dedicated to training an intelligent agent to master the classic game of Tetris using evolutionary strategies and reinforcement learning principles.

## 🚀 Project Motivation

Tetris presents a rich challenge of spatial reasoning, planning, and long-term reward optimization. By evolving an evaluation function that scores each move, we aim to approximate near-human or super-human performance without requiring deep neural networks or extensive handcrafted heuristics.

## 🧩 How It Works

1. **State Representation**  
   Each board configuration is mapped to numerical features:  
   - **Aggregate Height:** Total column heights  
   - **Lines Cleared:** Rows eliminated by the move  
   - **Holes:** Empty cells concealed below blocks  
   - **Bumpiness:** Variance in adjacent column heights  

2. **Evaluation Function**  
   We compute a score for every possible move as a weighted sum:
   <br>`Score = w₁·(Aggregate Height) + w₂·(Lines Cleared) + w₃·(Holes) + w₄·(Bumpiness)`

3. **Evolutionary Training**  
   - **Population:** A set of weight vectors `[w₁, w₂, w₃, w₄]`  
   - **Selection & Mutation:** At each generation, weights are perturbed by Gaussian noise scaled by performance (standardized rewards).  
   - **Update Rule:**  
     ```
     w_new = w_old + (α / (σ·N)) × Normal(0,1) · Z_score
     ```
     - α: Learning rate  
     - σ: Noise factor  
     - N: Population size  
     - Z_score: Standardized performance across the population  

4. **Complexity**  
   - **Evaluation:** O(n) per move  
   - **Training:** O(n²) per generation (population × moves)

## 📈 Results

After training, the agent consistently clears thousands of lines and achieves high scores, demonstrating the effectiveness of simple feature-based evaluation combined with evolutionary optimization.

## ⚙️ How to use

1. **Clone the repo**  
   ```bash
   git clone https://github.com/your-username/TetrisRL.git
   cd TetrisRL
   ```

2. **Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **PLay**  
   ```bash
   python main,py
   ```
## Screenshot

![gameplay](https://github.com/user-attachments/assets/5db3146b-c1c8-4a08-8eab-5f4411e89a01)

## 🔗 References

- **Tetris AI – The Near Perfect Player** by Colin Fahey:  
  https://codemyroad.wordpress.com/2013/04/14/tetris-ai-the-near-perfect-player/

## 📝 License

This project is released under the **MIT License**.
