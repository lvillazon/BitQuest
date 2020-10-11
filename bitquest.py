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
from speech_bubble import SpeechBubble

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

# TEST - experimenting with speech bubbles
# bubble = SpeechBubble("Hello world")
# bubble2 = SpeechBubble("test")
# bubble2.position = (100, 600)
# # TEST green bg, just to check colour key
# screen.fill((113, 201, 168))
#
# while True:
#     for height in range(50, 450, 50):
#         bubble.set_target_size((300, height))
#         bubble2.set_target_size((300, 500-height))
#
#         while bubble.resizing or bubble2.resizing:
#             bubble.draw(screen)
#             bubble2.draw(screen)
#             pygame.display.update()
#         time.sleep(2)
#
#     for height in range(450, 50, -50):
#         bubble.set_target_size((300, height))
#         bubble2.set_target_size((300, 500-height))
#
#         while bubble.resizing or bubble2.resizing:
#             bubble.draw(screen)
#             bubble2.draw(screen)
#             pygame.display.update()
#         time.sleep(2)
#
# END TEST

# create the world
world = world.World(screen, display)
console_msg("World initialisation complete", 1)

# set it in motion
while world.game_running:
    # when programs are running, the world is updated from the interpreter
    # so we don't want to do it here as well, because it will just slow the
    # intepreter down
    if not world.program.running:
        world.update()

# tidy up and quit
pygame.quit()
