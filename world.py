"""
 BitQuest module to handle the game world rendering
 and character movement
"""
import random
import time
import pygame
from pygame.locals import *

import blocks
import characters
import editor
import interpreter
import scenery
from console_messages import console_msg
from constants import *
from particles import DustStorm

'''
https://wiki.libsdl.org/Installation
https://github.com/pygame/pygame/issues/1722
'''


class World:
    def __init__(self, screen, display):
        console_msg('Started.', 0)
        self.screen = screen
        self.display = display

        # load scenery layers
        self.scenery = scenery.Scenery('Day', 'Desert')
        self.true_scroll = [0.0, 0.0]
        # location of the game area on the window
        # used to scroll the game area out of the way of the code editor
        self.game_origin = [0, 0]

        # load puzzle blocks
        self.blocks = blocks.BlockMap(self)
        console_msg("Map loaded", 1)

        # initialise the environmental dust effect
        # DEBUG disabled due to looking bad
        # self.dust_storm = DustStorm(self)

        # load character sprites
        self.player = characters.Character(self, 'player', 'new_character.png')
        console_msg("player sprite initialised", 1)
        self.dog = characters.Character(self, 'dog', 'bit basic1.png',
                                        run_speed=2)
        console_msg("BIT sprite initialised", 1)
        self.player.location.x = 4 * BLOCK_SIZE
        self.player.location.y = 8 * BLOCK_SIZE
        self.dog.location.x = 11 * BLOCK_SIZE
        self.dog.location.y = self.player.location.y
        self.show_fps = False
        self.show_grid = False
        # this flag prevents certain key actions from automatically repeating
        # it is cleared when any key is released
        self.repeat_lock = False

        # intialise the python interpreter and editor
        if pygame.font.get_init() is False:
            pygame.font.init()
        console_msg("Font system initialised", 2)
        # we're not using the built-in SysFont any more
        # so that the TTF file can be bundled to run on other PCs
        # self.code_font = pygame.font.SysFont("dejavusansmono", 18)
        self.code_font = pygame.font.Font("DejaVuSansMono.ttf", 18)
        console_msg("Deja Vu Sans Mono font loaded", 3)

        if pygame.scrap.get_init() is False:
            pygame.scrap.init()
        console_msg("Clipboard initialised", 2)

        self.program = interpreter.VirtualMachine(self)
        console_msg("Interpreter initialised", 2)

        self.editor = editor.CodeWindow(screen, 300,
                                        self.code_font,
                                        self.program)
        input_height = self.code_font.get_linesize()*3
        self.input = editor.InputDialog(screen, input_height, self.code_font)
        console_msg("Editors initialised", 2)

        self.camera_shake = False
        self.game_running = True
        self.frame_draw_time = 1
        self.frame_counter = 0
        self.clock = pygame.time.Clock()

    def get_bit_x(self):
        return self.dog.gridX()

    def get_bit_y(self):
        return self.dog.gridY()

    def set_bit_x(self, new_x):
        # attempt to move the dog to the new position
        distance = new_x - self.dog.gridX()
        if distance < 0:
            self.dog.move_left(abs(distance))
        elif distance > 0:
            self.dog.move_right(abs(distance))

    def set_bit_y(self, new_y):
        # attempt to move the dog to the new position
        distance = new_y - int(self.dog.location.y / BLOCK_SIZE)
        if distance < 0:
            self.dog.move_up(distance)
            self.dog.flying = True
        elif distance > 0:
            self.dog.move_down(distance)

    bit_x = property(get_bit_x, set_bit_x)
    bit_y = property(get_bit_y, set_bit_y)

    def get_player_x(self):
        return self.player.gridX()

    def get_player_y(self):
        return self.player.gridY()

    def set_player_x(self, dummy):  # variable is read only
        pass

    def set_player_y(self, dummy):  # variable is read only
        pass

    player_x = property(get_player_x, set_player_x)
    player_y = property(get_player_y, set_player_y)

    def update(self):
        """update all the game world stuff"""

        display = self.display  # for brevity

        frame_start_time = time.time_ns()  # used to calculate fps

        # track the camera with the player, but with a bit of lag
        self.true_scroll[X] += (self.player.location.x -
                                self.true_scroll[X] - CAMERA_X_OFFSET) / 16
        if self.true_scroll[X] < 0:
            # can't scroll past the start of the world
            self.true_scroll[X] = 0
        self.true_scroll[Y] += (self.player.location.y -
                                self.true_scroll[Y] - CAMERA_Y_OFFSET) / 16
        scroll = [int(self.true_scroll[X]), int(self.true_scroll[Y])]
        if self.camera_shake:
            scroll[X] += random.randint(-1, 1)
            scroll[Y] += random.randint(-1, 1)

        # render the background
        self.scenery.draw_background(display, scroll)

        # move and render the player sprite
        self.player.update(display, scroll)

        # move and render the dog
        self.dog.update(display, scroll)

        # draw the foreground scenery on top of the characters
        self.blocks.update(display, scroll)

        # draw the grid overlay last so it is on top of everything
        if self.show_grid:
            self.blocks.draw_grid(display, scroll, self.editor.get_fg_color())

        # update the input window and editor, if necessary
        # the input window takes precedence if both are open
        if self.input.is_active():
            self.input.update()
        elif self.editor.is_active():
            self.editor.update()
        else:
            # only handle keystrokes for game control if the editor isn't open
            pressed = pygame.key.get_pressed()
            if pressed[K_a]:
                self.player.move_left()
            elif pressed[K_d]:
                self.player.move_right()

            if pressed[K_SPACE]:
                self.player.jump()

            if pressed[K_ESCAPE]:
                # only show editor when it is completely hidden
                # this prevents it immediately reshowing after hiding
                if self.game_origin[Y] == 0:
                    self.editor.show()

            if MAP_EDITOR_MODE and not self.repeat_lock:
                if pressed[K_F9]:
                    console_msg("Saving map...", 1, line_end='')
                    self.blocks.save_grid()
                    console_msg("done", 1)
                    self.repeat_lock = True

                if pressed[K_RIGHT]:
                    self.blocks.cursor_right()
                    self.repeat_lock = True
                if pressed[K_LEFT]:
                    self.blocks.cursor_left()
                    self.repeat_lock = True
                if pressed[K_UP]:
                    self.blocks.cursor_up()
                    self.repeat_lock = True
                if pressed[K_DOWN]:
                    self.blocks.cursor_down()
                    self.repeat_lock = True
                if pressed[K_RETURN]:
                    # change/add a block to at the current grid cursor location
                    self.blocks.change_block()
                    self.repeat_lock = True

            # DEBUG stats
            if pressed[K_f]:
                # toggle fps stats
                if self.show_fps:
                    self.show_fps = False
                else:
                    self.frame_counter = 0
                    self.show_fps = True

            if pressed[K_g]:
                if not self.repeat_lock:
                    # toggle the block grid overlay
                    self.show_grid = not self.show_grid
                    self.repeat_lock = True

            # process all other events to clear the queue
            for event in pygame.event.get():
                if event.type == KEYUP:
                    self.repeat_lock = False  # release the lock
                if event.type == QUIT:
                    self.game_running = False

        if self.show_fps:
            self.frame_counter += 1
            if self.frame_counter > 60:
                self.frame_counter = 0
                console_msg(
                    'frame draw:{0}ms fps:{1} render budget left:{2}ms'.format(
                        self.frame_draw_time / 1000000,
                        int(1000000000 / self.frame_draw_time),
                        int((1000000000 - 60
                             * self.frame_draw_time) / 1000000)), 1)

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
        self.scenery.draw_foreground(self.screen, scroll)

        # the input window and code editor sit below the game surface
        # ie at a higher Y value, not below in the sense of a different layer
        editor_position = (self.game_origin[X],
                           self.game_origin[Y] + WINDOW_SIZE[Y])
        self.screen.blit(self.editor.surface, editor_position)

        # draw the input window, if it is currently active
        if self.input.is_active():
            self.input.draw()
            input_dialog_position = (self.game_origin[X],
                                     self.game_origin[Y]
                                     + WINDOW_SIZE[Y]
                                     - self.input.height)
            self.screen.blit(self.input.surface, input_dialog_position)

        # overlay all speech bubble at the native resolution
        if self.dog.speaking:
            # position the tip of the speak bubble at the middle
            # of the top edge of the sprite box
            position = (
                (self.dog.location.x - scroll[X] + 16)
                * SCALING_FACTOR + self.game_origin[X],
                (self.dog.location.y - scroll[Y])
                * SCALING_FACTOR + self.game_origin[Y]
                - self.dog.text_size[Y]
            )
            self.dog.draw_speech_bubble(display)
            self.screen.blit(self.dog.bubble, position)

        # draw the swirling dust - DEBUG disabled due to looking bad
        # self.dust_storm.update(self.screen, self.game_origin[Y], scroll)

        pygame.display.update()  # actually display

        self.frame_draw_time = time.time_ns() - frame_start_time
        self.clock.tick(60)  # lock the framerate to 60fps
