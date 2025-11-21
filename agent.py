import torch
import random
import numpy as np
from collections import deque
from game import RunnerGameAI
from model import Linear_QNet, QTrainer
from helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 2000 # Increased for stability
LR = 0.001

class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0 
        self.gamma = 0.9 
        self.memory = deque(maxlen=MAX_MEMORY) 
        #  (Added Gravity)
        self.model = Linear_QNet(4, 256, 2)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def get_state(self, game):
        player = game.player.sprite
        
        dist_to_obstacle = 1000
        obstacle_y = 0 
        
        if len(game.obstacle_group) > 0:
            obstacles = [obs for obs in game.obstacle_group if obs.rect.right > player.rect.left]
            if obstacles:
                closest_obstacle = min(obstacles, key=lambda obs: obs.rect.x)
                dist_to_obstacle = closest_obstacle.rect.x - player.rect.right
                obstacle_y = closest_obstacle.rect.midbottom[1] 

        # NORMALIZED STATE
        state = [
            player.rect.bottom / 400.0,   # 1. Y Position (0-1)
            dist_to_obstacle / 800.0,     # 2. Distance (0-1)
            obstacle_y / 300.0,           # 3. Obs Type (0-1)
            player.gravity / 20.0         # 4. Velocity (-1 to 1)
        ]

        return np.array(state, dtype=float)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # Epsilon decay with a floor of 10 to keep exploring a little bit
        self.epsilon = 80 - self.n_games
        final_move = [0,0] 
        
        # Only use random moves if epsilon is high enough
        if random.randint(0, 200) < self.epsilon and self.epsilon > 0:
            move = random.randint(0, 1)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = RunnerGameAI()
    
    while True:
        state_old = agent.get_state(game)
        final_move = agent.get_action(state_old)

        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        agent.train_short_memory(state_old, final_move, reward, state_new, done)
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)

if __name__ == '__main__':
    train()