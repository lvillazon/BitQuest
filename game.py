"""
 BitQuest module to handle the game world rendering
 and character movement
"""

import pygame

import world
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

#######################################################

# create the world
world = world.World(screen, display)

# set it in motion
while world.game_running:
    world.update()

# tidy up and quit
pygame.quit()
