import torch
import numpy as np
import pygame
from game import RunnerGameAI
from model import Linear_QNet

# 1. Configuration
MODEL_PATH = './model/model_67.pth'
INPUT_SIZE = 4   # Must match the size used in training (Normalized: Y, Dist, Type, Gravity)
HIDDEN_SIZE = 256
OUTPUT_SIZE = 2  # [Run, Jump]

def get_state(game):
    """
    Recreates the exact same state logic used in agent.py.
    If you changed agent.py, you must update this to match.
    """
    player = game.player.sprite
    
    dist_to_obstacle = 1000
    obstacle_y = 0 
    
    if len(game.obstacle_group) > 0:
        # Find closest obstacle to the right of the player
        obstacles = [obs for obs in game.obstacle_group if obs.rect.right > player.rect.left]
        if obstacles:
            closest_obstacle = min(obstacles, key=lambda obs: obs.rect.x)
            dist_to_obstacle = closest_obstacle.rect.x - player.rect.right
            obstacle_y = closest_obstacle.rect.midbottom[1] 

    # Normalize inputs exactly like in agent.py
    state = [
        player.rect.bottom / 400.0,
        dist_to_obstacle / 800.0,
        obstacle_y / 300.0,
        player.gravity / 20.0
    ]
    return np.array(state, dtype=float)

def test():
    # 2. Initialize Game and Model
    game = RunnerGameAI()
    model = Linear_QNet(INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE)
    
    # 3. Load the saved weights
    try:
        state_dict = torch.load(MODEL_PATH)
        model.load_state_dict(state_dict)
        model.eval() # Set to evaluation mode
        print("Model loaded successfully!")
    except FileNotFoundError:
        print(f"Error: Could not find {MODEL_PATH}. Make sure you trained the agent first.")
        return

    n_games = 0
    
    while True:
        # 4. Get State
        state = get_state(game)
        state_tensor = torch.tensor(state, dtype=torch.float)

        # 5. Get Prediction (No Randomness)
        with torch.no_grad():
            prediction = model(state_tensor)
            move_idx = torch.argmax(prediction).item()
        
        final_move = [0, 0]
        final_move[move_idx] = 1

        # 6. Play Move
        # Note: We don't care about reward or 'done' for training, just for game logic
        reward, done, score = game.play_step(final_move)

        # 7. Visuals
        # Force a delay so we can watch (60 FPS)
        # In the training code, we often used clock.tick(0) for speed
        game.clock.tick(60) 

        if done:
            game.reset()
            n_games += 1
            print(f'Game {n_games} finished. Score: {score}')

if __name__ == '__main__':
    test()