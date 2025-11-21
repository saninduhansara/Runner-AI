import pygame
from random import randint, choice
import numpy as np

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        player_walk_1 = pygame.image.load('graphics/player/player_walk_1.png').convert_alpha()
        player_walk_2 = pygame.image.load('graphics/player/player_walk_2.png').convert_alpha()
        self.player_walk = [player_walk_1,player_walk_2]
        self.player_index = 0
        self.player_jump = pygame.image.load('graphics/player/jump.png').convert_alpha()

        self.image = self.player_walk[self.player_index]
        self.rect = self.image.get_rect(midbottom = (80,300))
        self.gravity = 0

    def jump(self):
        if self.rect.bottom >= 300:
            self.gravity = -20

    def apply_gravity(self):
        self.gravity += 1
        self.rect.y += self.gravity
        if self.rect.bottom >= 300:
            self.rect.bottom = 300

    def animation_state(self):
        if self.rect.bottom < 300: 
            self.image = self.player_jump
        else:
            self.player_index += 0.1
            if self.player_index >= len(self.player_walk):self.player_index = 0
            self.image = self.player_walk[int(self.player_index)]

    def update(self):
        self.apply_gravity()
        self.animation_state()

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, type):
        super().__init__()
        
        if type == 'fly':
            fly_1 = pygame.image.load('graphics/fly/fly1.png').convert_alpha()
            fly_2 = pygame.image.load('graphics/fly/fly2.png').convert_alpha()
            self.frames = [fly_1,fly_2]
            y_pos = 210
        else:
            snail_1 = pygame.image.load('graphics/snail/snail1.png').convert_alpha()
            snail_2 = pygame.image.load('graphics/snail/snail2.png').convert_alpha()
            self.frames = [snail_1,snail_2]
            y_pos  = 300

        self.animation_index = 0
        self.image = self.frames[self.animation_index]
        self.rect = self.image.get_rect(midbottom = (randint(900,1100),y_pos))
        self.passed = False # New flag to track reward

    def animation_state(self):
        self.animation_index += 0.1 
        if self.animation_index >= len(self.frames): self.animation_index = 0
        self.image = self.frames[int(self.animation_index)]

    def update(self):
        self.animation_state()
        self.rect.x -= 10 
        if self.rect.x <= -100: 
            self.kill()

class RunnerGameAI:
    def __init__(self):
        pygame.init()
        self.w = 800
        self.h = 400
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Runner AI')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font('font/Pixeltype.ttf', 50)
        
        self.sky_surface = pygame.image.load('graphics/Sky.png').convert()
        self.ground_surface = pygame.image.load('graphics/ground.png').convert()
        
        self.reset()

    def reset(self):
        self.score = 0
        self.frame_iteration = 0
        self.player = pygame.sprite.GroupSingle()
        self.player.add(Player())
        self.obstacle_group = pygame.sprite.Group()
        return self.score

    def play_step(self, action):
        self.frame_iteration += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        
        # 2. Move
        if np.array_equal(action, [0, 1]):
            self.player.sprite.jump()
            
        # 3. Update Game Logic
        self.player.update()
        self.obstacle_group.update()
        
        # Spawning Logic
        spawn_flag = False
        if len(self.obstacle_group) == 0:
            spawn_flag = True
        else:
            obstacles = self.obstacle_group.sprites()
            right_most = max(obs.rect.x for obs in obstacles)
            if right_most < 600 and randint(0, 10) < 2: 
                spawn_flag = True
        
        if spawn_flag:
             self.obstacle_group.add(Obstacle(choice(['fly','snail','snail','snail'])))

        # 4. Check Collision & Reward
        game_over = False
        reward = 0.01 # Small survival reward every frame

        # Check for passed obstacles
        player_left = self.player.sprite.rect.left
        for obs in self.obstacle_group:
            # If obstacle is now behind the player and wasn't marked 'passed'
            if obs.rect.right < player_left and not obs.passed:
                obs.passed = True
                reward = 5 # Big reward for jumping over
                self.score += 1
        
        # Check collision
        if pygame.sprite.spritecollide(self.player.sprite, self.obstacle_group, False):
            game_over = True
            reward = -10 # Penalty for death
            return reward, game_over, self.score

        # 5. Update UI
        self._update_ui()
        # Set to 0 for max speed, or 60 to watch it slowly
        self.clock.tick(0) 
        
        return reward, game_over, self.score

    def _update_ui(self):
        self.display.blit(self.sky_surface,(0,0))
        self.display.blit(self.ground_surface,(0,300))
        self.player.draw(self.display)
        self.obstacle_group.draw(self.display)
        
        score_surf = self.font.render(f'Score: {self.score}',False,(64,64,64))
        score_rect = score_surf.get_rect(center = (400,50))
        self.display.blit(score_surf,score_rect)
        pygame.display.flip()