"""
 BitQuest module to handle the game world rendering
 and character movement
"""

import time
import pygame
from pygame.locals import *

import characters
import editor
import interpreter
import scenery
from constants import *
'''
https://wiki.libsdl.org/Installation
https://github.com/pygame/pygame/issues/1722
'''

class World:
    def __init__(self, screen, display):
        print('Started.')
        self.screen = screen
        self.display = display

        # load scenery layers
        self.scenery = scenery.Scenery('Day', 'Desert')
        self.true_scroll = {'x': 0.0, 'y': 0.0}
        # location of the game area on the window
        # used to scroll the game area out of the way of the code editor
        self.game_origin = [0, 0]

        # load character sprites
        self.player = characters.Character(self, 'character.png')
        self.dog = characters.Character(self, 'dog basic.png', run_speed=2)
        self.player.location = {'x': 150, 'y': 170 - 32 - 2}
        self.dog.location = {'x': self.player.location['x'] + 50,
                        'y': self.player.location['y']}
        self.debug_mode = False

        # intialise the python interpreter and editor
        if pygame.font.get_init() is False:
            pygame.font.init()
        if pygame.scrap.get_init() is False:
            pygame.scrap.init()
        self.code_font = pygame.font.SysFont("dejavusansmono", 18)
        self.program = interpreter.VirtualMachine(self)
        self.editor = editor.Editor(screen, 300, self.code_font, self.program)

        self.game_running = True
        self.frame_draw_time = 1
        self.clock = pygame.time.Clock()

    def get_bit_x(self):
        #        return 6
        return self.dog.location['x']

    def set_bit_x(self, new_x):
#        self.dog.location['x'] = new_x

        if new_x < self.dog.location['x']:
            while (abs(self.dog.location['x'] - new_x) >= self.dog.run_speed):
                self.dog.move_left()
                self.update()
        elif new_x > self.dog.location['x']:
            while (abs(self.dog.location['x'] - new_x) >= self.dog.run_speed):
                self.dog.move_right()
                self.update()

        self.dog.stop_moving()

    bit_x = property(get_bit_x, set_bit_x)

    def get_dog_X(self):
        return self.dog.location['x']

    def update(self):
        '''update all the game world stuff'''''
        display = self.display  # for brevity

        frame_start_time = time.time_ns()  # used to calculate fps

        # track the camera with the player, but with a bit of lag
        self.true_scroll['x'] += (self.player.location['x']
                             - self.true_scroll['x'] - PLAYER_X_OFFSET) / 16
        if self.true_scroll['x'] < 0:
            # can't scroll past the start of the world
            self.true_scroll['x'] = 0
        self.true_scroll['y'] += (self.player.location['y']
                             - self.true_scroll['y'] - PLAYER_Y_OFFSET) / 16
        scroll = {'x': int(self.true_scroll['x']),
                  'y': int(self.true_scroll['y'])}

        # render the background
        self.scenery.draw_background(display, scroll)

        # move and render the player sprite
        self.player.update(display, scroll)

        # move and render the dog
        self.dog.update(display, scroll)
        # dog follows the player
        #if self.dog.location['x'] > self.player.location['x'] + 30:
        #    self.dog.move_left()
        #elif self.dog.location['x'] < self.player.location['x'] - 30:
        #    self.dog.move_right()
        #else:
        #    self.dog.stop_moving()

        # draw the foreground scenery on top of the characters
        self.scenery.draw_foreground(display, scroll)

        # allocate some cpu time to the in-game interpreter running player's code
        if self.program.is_running():
            self.program.update()

        # draw and update the editor, if necessary
        if self.editor.is_active():
            self.editor.update()
        else:
            # only handle keystrokes for game control if the editor isn't open
            pressed = pygame.key.get_pressed()
            if pressed[K_a]:
                self.player.move_left()
            elif pressed[K_d]: # or True:  # DEBUG ensure the scene is always moving to check multitasking works

                self.player.move_right()
            else:
                self.player.stop_moving()

            if pressed[K_SPACE]:
                self.player.jump()

            if pressed[K_ESCAPE]:
                # only show editor when it is completely hidden
                # this prevents it immediately reshowing after hiding
                if self.game_origin[Y] == 0:
                    self.editor.show()

            # DEBUG stats
            if pressed[K_f]:
                # display fps stats
                self.debug_frame_counter = 0
                self.debug_mode = True

            if pressed[K_g]:
                # turn off fps stats
                self.debug_mode = False

            # process all other events to clear the queue
            for event in pygame.event.get():
                if event.type == QUIT:
                    game_running = False

        if self.debug_mode:
            self.debug_frame_counter += 1
            if self.debug_frame_counter > 60:
                self.debug_frame_counter = 0
                print(
                    'frame draw:{0}ms fps:{1} render budget left:{2}ms'.format(
                        self.frame_draw_time / 1000000,
                        int(1000000000 / self.frame_draw_time),
                        int((1000000000 - 60
                             * self.frame_draw_time) / 1000000)))

        # scroll the editor in and out of view as required
        if self.editor.is_active():
            if self.game_origin[Y] > -self.editor.height:
                self.game_origin[Y] -= EDITOR_POPUP_SPEED
            self.editor.draw()
        elif self.game_origin[Y] < 0:
            self.game_origin[Y] += EDITOR_POPUP_SPEED

        # scale the rendering area to the actual game window
        self.screen.blit(pygame.transform.scale(display, WINDOW_SIZE),
                    self.game_origin)
        # blit the editor underneath the game surface
        editor_position = (self.game_origin[X],
                           self.game_origin[Y] + WINDOW_SIZE[Y])
        self.screen.blit(self.editor.surface, editor_position)

        # overlay all text at the native resolution to avoid scaling ugliness
        if self.dog.speaking:
            # position the tip of the speak bubble at the middle
            # of the top edge of the sprite box
            position = ((self.dog.location['x'] - scroll['x'] + 16)
                        * SCALING_FACTOR + self.game_origin[X],
                        (self.dog.location['y'] - scroll['y'])
                        * SCALING_FACTOR  + self.game_origin[Y]
                        - self.dog.text_size[Y])
            self.screen.blit(self.dog.bubble, position)

        pygame.display.update()  # actually display

        self.frame_draw_time = time.time_ns() - frame_start_time
        self.clock.tick(60)  # lock the framerate to 60fps

