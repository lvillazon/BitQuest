"""
 BitQuest module to handle the game world rendering
 and character movement
"""
import random
import time
import uuid

import pygame

import menu
import world
from console_messages import console_msg
from constants import *

'''
https://wiki.libsdl.org/Installation
https://github.com/pygame/pygame/issues/1722
'''
console_msg('Started. Version ' + VERSION, 0)

# set environment variables to request the window manager to position the top left of the game window
import os
DEFAULT = 0, 30  # used for single monitor display - put window in top left
DEVON_OFFICE = -1250, 780  # centred on laptop display
position = DEFAULT
os.environ['SDL_VIDEO_WINDOW_POS'] = str(position[0]) + "," + str(position[1])

pygame.init()
pygame.display.set_caption("BIT Quest")

# the actual game window
screen = pygame.display.set_mode(WINDOW_SIZE)
# the rendering surface for the game (heavily scaled)
display = pygame.Surface(DISPLAY_SIZE)

game_world = None
game_menu = menu.Menu(screen, bypass=not SHOW_LOGIN_MENU)
game_menu.display()

if not game_menu.quit():
    # create the world
    game_world = world.World(screen, display, game_menu.session)

    # set it in motion
    while not game_menu.quit():
        # when programs are running, the world is updated from the interpreter
        # so we don't want to do it here as well, because it will just slow the
        # intepreter down
        if game_world.playing:
            # keep the camera focussed on BIT while he is doing something
            if game_world.dog.busy:
                game_world.update(game_world.dog)
            else:
                game_world.update(game_world.player)
        else:
            # the return value from the menu determines whether
            # we keep playing or quit
            game_world.playing = game_menu.display()

# tidy up and quit
pygame.quit()
