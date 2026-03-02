import os
import random
import sys
import pygame
from itertools import cycle
from pygame.locals import *

try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except:
    pass

# Constants
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

    try:
        for name in ['die', 'hit', 'point', 'wing']:
            sounds[name] = pygame.mixer.Sound(f'audio/{name}.ogg')
    except:
        pass

    while True:
        raw_bg = pygame.image.load(random.choice(backgrounds_list)).convert()
        images['background'] = pygame.transform.scale(raw_bg, (screen_width, screen_height))
        images['player'] = tuple(pygame.image.load(s).convert_alpha() for s in random.choice(players_list))
        
        pipe_path = random.choice(pipes_list)
        images['pipe'] = (
            pygame.transform.flip(pygame.image.load(pipe_path).convert_alpha(), False, True),
            pygame.image.load(pipe_path).convert_alpha(),
        )

        hitmasks['pipe'] = (get_hitmask(images['pipe'][0]), get_hitmask(images['pipe'][1]))
        hitmasks['player'] = tuple(get_hitmask(img) for img in images['player'])

        # GAME PHASES
        movement_info = show_welcome_animation()
        crash_info = main_game(movement_info)
        # This function now finishes and allows the loop to restart
        show_game_over_screen(crash_info)

def show_welcome_animation():
    player_index_gen = cycle([0, 1, 2, 1])
    player_x = int(screen_width * 0.2)
    player_y = int((screen_height - images['player'][0].get_height()) / 2)
    message_x = int((screen_width - images['message'].get_width()) / 2)
    message_y = int(screen_height * 0.12)
    base_x, player_shm_vals = 0, {'val': 0, 'dir': 1}

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN:
                sounds['wing'].play()
                return {'playery': player_y + player_shm_vals['val'], 'basex': base_x, 'playerIndexGen': player_index_gen}

        player_shm(player_shm_vals)
        screen.blit(images['background'], (0, 0))
        screen.blit(images['player'][next(player_index_gen)], (player_x, player_y + player_shm_vals['val']))
        screen.blit(images['message'], (message_x, message_y))
        screen.blit(images['base'], (base_x, base_y))
        pygame.display.update()
        fps_clock.tick(fps)

def main_game(movement_info):
    score = player_index = loop_iter = 0
    player_index_gen = movement_info['playerIndexGen']
    player_x, player_y = int(screen_width * 0.2), movement_info['playery']
    base_x = movement_info['basex']

    new_p1 = get_random_pipe()
    new_p2 = get_random_pipe()
    upper_pipes = [{'x': screen_width + 200, 'y': new_p1[0]['y']},
                   {'x': screen_width + 200 + (screen_width / 2), 'y': new_p2[0]['y']}]
    lower_pipes = [{'x': screen_width + 200, 'y': new_p1[1]['y']},
                   {'x': screen_width + 200 + (screen_width / 2), 'y': new_p2[1]['y']}]

    pipe_vel_x, player_vel_y, player_acc_y, player_flap_acc = -4, -9, 1, -9
    player_rot, player_flapped = 45, False

    while True:
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
            if event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN:
                if player_y > -2 * images['player'][0].get_height():
                    player_vel_y, player_flapped, player_rot = player_flap_acc, True, 45
                    sounds['wing'].play()

        crash_test = check_crash({'x': player_x, 'y': player_y, 'index': player_index}, upper_pipes, lower_pipes)
        if crash_test[0]:
            return {'y': player_y, 'groundCrash': crash_test[1], 'basex': base_x, 'upperPipes': upper_pipes, 'lowerPipes': lower_pipes, 'score': score, 'playerVelY': player_vel_y, 'playerRot': player_rot}

        # Scoring
        player_mid = player_x + images['player'][0].get_width() / 2
        for pipe in upper_pipes:
            pipe_mid = pipe['x'] + images['pipe'][0].get_width() / 2
            if pipe_mid <= player_mid < pipe_mid + 4:
                score += 1; sounds['point'].play()

        if (loop_iter + 1) % 3 == 0: player_index = next(player_index_gen)
        loop_iter = (loop_iter + 1) % 30
        if player_rot > -90: player_rot -= 3
        if player_vel_y < 10 and not player_flapped: player_vel_y += player_acc_y
        player_flapped = False
        player_y += min(player_vel_y, base_y - player_y - images['player'][0].get_height())

        for u, l in zip(upper_pipes, lower_pipes):
            u['x'] += pipe_vel_x; l['x'] += pipe_vel_x
        
        if 0 < upper_pipes[0]['x'] < 5:
            new_p = get_random_pipe()
            upper_pipes.append(new_p[0]); lower_pipes.append(new_p[1])
        if upper_pipes[0]['x'] < -images['pipe'][0].get_width():
            upper_pipes.pop(0); lower_pipes.pop(0)

        screen.blit(images['background'], (0, 0))
        for u, l in zip(upper_pipes, lower_pipes):
            screen.blit(images['pipe'][0], (u['x'], u['y']))
            screen.blit(images['pipe'][1], (l['x'], l['y']))
        screen.blit(images['base'], (base_x, base_y))
        show_score(score)
        visible_rot = player_rot if player_rot <= 20 else 20
        player_surface = pygame.transform.rotate(images['player'][player_index], visible_rot)
        screen.blit(player_surface, (player_x, player_y))
        pygame.display.update()
        fps_clock.tick(fps)

def show_game_over_screen(crash_info):
    """Wait for input then return to main loop to restart"""
    score = crash_info['score']
    
    # High Score Logic
    high_score = 0
    try:
        if os.path.exists('highscore.txt'):
            with open('highscore.txt', 'r') as f:
                high_score = int(f.read())
    except: pass

    if score > high_score:
        high_score = score
        with open('highscore.txt', 'w') as f:
            f.write(str(high_score))

    sounds['hit'].play()
    if not crash_info['groundCrash']: sounds['die'].play()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit(); sys.exit()
            if event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN:
                # RESTART TRIGGER: Returning to the while loop in main()
                return 

        screen.blit(images['background'], (0, 0))
        # Keep showing pipes and base so it looks natural
        for u, l in zip(crash_info['upperPipes'], crash_info['lowerPipes']):
            screen.blit(images['pipe'][0], (u['x'], u['y']))
            screen.blit(images['pipe'][1], (l['x'], l['y']))
        screen.blit(images['base'], (crash_info['basex'], base_y))
        
        # Show Game Over and Score
        screen.blit(images['gameover'], (50, 180))
        show_score(score)
        
        pygame.display.update()
        fps_clock.tick(fps)

# --- Helper Functions ---
def get_random_pipe():
    gap_y = random.randrange(0, int(base_y * 0.6 - pipe_gap_size)) + int(base_y * 0.2)
    pipe_h = images['pipe'][0].get_height()
    return [{'x': screen_width + 10, 'y': gap_y - pipe_h},
            {'x': screen_width + 10, 'y': gap_y + pipe_gap_size}]

def show_score(score):
    digits = [int(x) for x in str(score)]
    w = sum(images['numbers'][d].get_width() for d in digits)
    offset = (screen_width - w) / 2
    for d in digits:
        screen.blit(images['numbers'][d], (offset, screen_height * 0.1))
        offset += images['numbers'][d].get_width()

def check_crash(player, upper_pipes, lower_pipes):
    if player['y'] + images['player'][0].get_height() >= base_y - 1: return [True, True]
    p_rect = pygame.Rect(player['x'], player['y'], images['player'][0].get_width(), images['player'][0].get_height())
    for u, l in zip(upper_pipes, lower_pipes):
        u_rect = pygame.Rect(u['x'], u['y'], images['pipe'][0].get_width(), images['pipe'][0].get_height())
        l_rect = pygame.Rect(l['x'], l['y'], images['pipe'][0].get_width(), images['pipe'][0].get_height())
        if pixel_collision(p_rect, u_rect, hitmasks['player'][player['index']], hitmasks['pipe'][0]) or \
           pixel_collision(p_rect, l_rect, hitmasks['player'][player['index']], hitmasks['pipe'][1]):
            return [True, False]
    return [False, False]

def pixel_collision(r1, r2, m1, m2):
    clip = r1.clip(r2)
    if not clip.width or not clip.height: return False
    for x in range(clip.width):
        for y in range(clip.height):
            if m1[clip.x - r1.x + x][clip.y - r1.y + y] and m2[clip.x - r2.x + x][clip.y - r2.y + y]: return True
    return False

def get_hitmask(img):
    return [[bool(img.get_at((x, y))[3]) for y in range(img.get_height())] for x in range(img.get_width())]

def player_shm(data):
    if abs(data['val']) >= 8: data['dir'] *= -1
    data['val'] += data['dir']

if __name__ == '__main__':
    main()