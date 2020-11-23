"""
 BitQuest module to handle the game world rendering
 and character movement
"""
import random
import time

import pygame

import world
from console_messages import console_msg
from constants import *

'''
https://wiki.libsdl.org/Installation
https://github.com/pygame/pygame/issues/1722
'''

# set environment variables to request the window manager to position the top left of the game window
import os
position = 0, 30  # setting y to 0 will place the title bar off the screen
os.environ['SDL_VIDEO_WINDOW_POS'] = str(position[0]) + "," + str(position[1])

pygame.init()
pygame.display.set_caption("BIT Quest")

# the actual game window
screen = pygame.display.set_mode(WINDOW_SIZE)
# the rendering surface for the game (heavily scaled)
display = pygame.Surface(DISPLAY_SIZE)

# create the world
world = world.World(screen, display)
console_msg("World initialisation complete", 1)

# set it in motion
while world.game_running:
    # when programs are running, the world is updated from the interpreter
    # so we don't want to do it here as well, because it will just slow the
    # intepreter down
    if not world.program.running:
        # keep the camera focussed on BIT while he is doing something
        if world.dog.busy:
            world.update(world.dog)
        else:
            world.update(world.player)

# tidy up and quit
pygame.quit()
