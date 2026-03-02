import os
import random
import sys
import pygame
from itertools import cycle
from pygame.locals import *

fps = 30
screen_width = 288
screen_height = 512
pipe_gap_size = 100
base_y = screen_height * 0.79
images, sounds, hitmasks = {}, {}, {}

players_list = (
    ('sprites/redbird-upflap.png', 'sprites/redbird-midflap.png', 'sprites/redbird-downflap.png'),
    ('sprites/bluebird-upflap.png', 'sprites/bluebird-midflap.png', 'sprites/bluebird-downflap.png'),
    ('sprites/yellowbird-upflap.png', 'sprites/yellowbird-midflap.png', 'sprites/yellowbird-downflap.png'),
)

backgrounds_list = ('sprites/background-day.png', 'sprites/background-night.png')
pipes_list = ('sprites/pipe-green.png', 'sprites/pipe-red.png')

def main():
    global screen, fps_clock
    pygame.init()
    fps_clock = pygame.time.Clock()
    
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.SCALED | pygame.FULLSCREEN)
    pygame.display.set_caption('Flappy Box')

    images['numbers'] = tuple(pygame.image.load(f'sprites/{i}.png').convert_alpha() for i in range(10))
    images['gameover'] = pygame.image.load('sprites/gameover.png').convert_alpha()
    images['message'] = pygame.image.load('sprites/message.png').convert_alpha()
    images['base'] = pygame.image.load('sprites/base.png').convert_alpha()
    