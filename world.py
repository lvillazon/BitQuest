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
        #        self.scenery = scenery.Scenery('Day', 'Desert')
        self.scenery = scenery.Scenery(self, 'Day', 'Field')

        self.true_scroll = [0.0, 0.0]
        self.scroll = [0, 0]  # integer version of true_scroll
        # location of the game area on the window
        # used to scroll the game area out of the way of the code editor
        self.game_origin = [0, 0]

        # load puzzle blocks
        self.blocks = blocks.BlockMap(self,
                                      BLOCK_TILE_DICTIONARY_FILE,
                                      BLOCK_TILESET_FILE)
        console_msg("Map loaded", 1)

        # set the starting positions for each puzzle
        player_start_pos = [(4, 6),  # puzzle 0 - the pillar
                            (58, 6),  # puzzle 1- the pit
                            (80, 6),  # puzzle 2 - the lift
                            (91, 6),  # puzzle 3 - the staircase
                            (105, 6),  # puzzle 4 - the choice
                            (8, 6),  # puzzle 5 - test position
                            ]
        dog_start_pos = [(6, 8),  # puzzle 0 - the pillar
                         (57, 8),  # puzzle 1- the pit
                         (78, 8),  # puzzle 2 - the lift
                         (90, 8),  # puzzle 3 - the staircase
                         (103, 8),  # puzzle 4 - the choice
                         (12, 5),  # puzzle 5 - test position
                         ]
        puzzle = 0

        # initialise the environmental dust effect
        # DEBUG disabled due to looking bad
        # self.dust_storm = DustStorm(self)

        # load character sprites
        self.player = characters.Person(self,
                                        'player',
                                        CHARACTER_SPRITE_FILE,
                                        (16, 20))
        console_msg("player sprite initialised", 1)
        self.dog = characters.Dog(self,
                                  'dog',
                                  DOG_SPRITE_FILE,
                                  (16, 16),
                                  )
        console_msg("BIT sprite initialised", 1)
        self.player.set_position(player_start_pos[puzzle])
        self.dog.set_position(dog_start_pos[puzzle])

        self.dog.facing_right = False
        self.show_fps = False
        # this flag prevents certain key actions from automatically repeating
        # it is cleared when any key is released
        self.repeat_lock = False

        # intialise the python interpreter and editor
        if pygame.font.get_init() is False:
            pygame.font.init()
        console_msg("Font system initialised", 2)
        # we're not using the built-in SysFont any more
        # so that the TTF file can be bundled to run on other PCs
        self.code_font = pygame.font.Font(CODE_FONT_FILE, 18)
        console_msg("Deja Vu Sans Mono font loaded", 3)
        self.grid_font = pygame.font.Font(GRID_FONT_FILE, 8)
        console_msg("Pixel font loaded", 3)

        if pygame.scrap.get_init() is False:
            pygame.scrap.init()
        console_msg("Clipboard initialised", 2)

        self.program = interpreter.VirtualMachine(self)
        console_msg("Interpreter initialised", 2)

        self.editor = editor.CodeWindow(screen, 300,
                                        self.code_font,
                                        self.program)
        input_height = self.code_font.get_linesize() * 3
        self.input = editor.InputDialog(screen, input_height, self.code_font)
        console_msg("Editors initialised", 2)

        self.camera_shake = False
        self.camera_pan = [0, 0]
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
        distance = int(new_x) - self.dog.gridX()
        self.dog.move_by_amount((distance, 0))

    def set_bit_y(self, new_y):
        # attempt to move the dog to the new position
        distance = int(new_y) - self.dog.gridY()
        self.dog.move_by_amount((0, distance))

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

    def busy(self):
        """ returns true if there is anything happening that must complete
        before the interpreter continues running the player's code.
        This allows us to halt code execution while platforms move
        for example, which makes it much easier to write programs to solve
        the puzzles, since you don't need busy loops to check BIT's position

        At the moment the following things trigger the busy state:
        * dog is moving
        * blocks are moving
        """
        if self.dog.busy or self.blocks.busy:
            return True
        else:
            return False

    def update(self, focus):
        """update all the game world stuff
        focus is the character that the camera follows
        This is the dog when a program is running, otherwise the player"""

        display = self.display  # for brevity

        frame_start_time = time.time_ns()  # used to calculate fps

        # track the camera with the focus character, but with a bit of lag
        self.true_scroll[X] += (focus.location.x -
                                self.true_scroll[X] - CAMERA_X_OFFSET) / 16
        if self.true_scroll[X] < 0:
            # can't scroll past the start of the world
            self.true_scroll[X] = 0
        self.true_scroll[Y] += (focus.location.y -
                                self.true_scroll[Y] - CAMERA_Y_OFFSET) / 16
        self.scroll = [int(self.true_scroll[X]) + self.camera_pan[X],
                       int(self.true_scroll[Y]) + self.camera_pan[Y]]
        if self.camera_shake:
            self.scroll[X] += random.randint(-1, 1)
            self.scroll[Y] += random.randint(-1, 1)

        # render the background
        self.scenery.draw_background(display)

        # move and render the player sprite
        self.player.update(display)

        # move and render the dog
        self.dog.update(display)

        # draw the foreground scenery on top of the characters
        self.blocks.update(display)
        # self.scenery.draw_foreground(display)

        # update the input window and editor, if necessary
        # the input window takes precedence if both are open
        if self.input.is_active():
            self.input.update()
        elif self.editor.is_active():
            self.editor.update()
        else:
            # only handle keystrokes for game control
            # if the code editor isn't open
            pressed = pygame.key.get_pressed()
            if pressed[K_a]:
                self.player.moving_left = True
                self.player.moving_right = False
            elif pressed[K_d]:
                self.player.moving_left = False
                self.player.moving_right = True
            # DEBUG give player the ability to fly!
            # elif pressed[K_w]:
            #     self.player.moving_down = False;
            #     self.player.moving_up = True
            # elif pressed[K_s]:
            #     self.player.moving_down = True;
            #     self.player.moving_up = False
            if pressed[K_w] or pressed[K_s]:
                if pressed[K_w]:
                    self.camera_pan[Y] -= 2
                else:
                    self.camera_pan[Y] += 2
            elif not self.blocks.show_grid:
                self.camera_pan[Y] = int(self.camera_pan[Y] * 0.9)

            if pressed[K_ESCAPE]:
                # only show editor when it is completely hidden
                # this prevents it immediately reshowing after hiding
                if self.game_origin[Y] == 0:
                    self.editor.show()

            if MAP_EDITOR_ENABLED and self.blocks.show_grid:
                ctrl = pygame.key.get_mods() & KMOD_CTRL
                shift = pygame.key.get_mods() & KMOD_SHIFT

                if shift and not self.blocks.selecting:
                    self.blocks.begin_selection()
                elif not shift and self.blocks.selecting:
                    self.blocks.end_selection()

                # these actions do not auto repeat when held down
                if not self.repeat_lock:
                    self.repeat_lock = True

                    if pressed[K_F9]:
                        console_msg("Saving map...", 1, line_end='')
                        self.blocks.save_grid()
                        console_msg("done", 1)
                    elif pressed[K_RIGHT]:
                        self.blocks.cursor_right()
                    elif pressed[K_LEFT]:
                        self.blocks.cursor_left()
                    elif pressed[K_UP]:
                        if ctrl:
                            self.camera_pan[Y] -= BLOCK_SIZE
                        else:
                            self.blocks.cursor_up()
                    elif pressed[K_DOWN]:
                        if ctrl:
                            self.camera_pan[Y] += BLOCK_SIZE
                        else:
                            self.blocks.cursor_down()
                    elif pressed[K_LEFTBRACKET]:  # [
                        self.blocks.previous_editor_tile()
                    elif pressed[K_RIGHTBRACKET]:  # ]
                        self.blocks.next_editor_tile()
                    elif pressed[K_BACKSPACE]:
                        if shift:
                            self.blocks.cancel_selection()
                            self.blocks.remove_moveable_group()
                        else:
                            self.blocks.blank_editor_tile()
                    elif pressed[K_RETURN]:
                        # change/add a block
                        # at the current grid cursor location
                        self.blocks.change_block()
                    elif pressed[K_TAB]:
                        # switch between midground and foreground block layers
                        self.blocks.switch_layer()
                    elif pressed[K_r]:
                        # reset all block triggers
                        self.blocks.reset()
                    elif pressed[K_h]:
                        # home the cursor to the centre of the screen
                        self.blocks.home_cursor()
                    else:
                        self.repeat_lock = False  # reset, since no key pressed

                        for event in pygame.event.get():
                            if event.type == pygame.MOUSEBUTTONDOWN and \
                                    event.button == 1:  # left button
                                mouse_pos = (pygame.mouse.get_pos()[X]
                                             / SCALING_FACTOR
                                             + self.scroll[X],
                                             pygame.mouse.get_pos()[Y]
                                             / SCALING_FACTOR
                                             + self.scroll[Y]
                                             )
                                if shift:
                                    self.blocks.select_block(mouse_pos)
                                elif ctrl:
                                    self.blocks.set_trigger(mouse_pos)
                                else:
                                    # just move the cursor, without selecting
                                    self.blocks.cursor_to_mouse(mouse_pos)
                            # 2: middle button
                            # 3: right button
                            # 4: scroll up
                            # 5: scroll down

            # DEBUG stats
            if pressed[K_f]:
                if not self.repeat_lock:
                    # toggle fps stats
                    self.show_fps = not self.show_fps
                    if not self.show_fps:
                        self.frame_counter = 0

            if pressed[K_g]:
                if not self.repeat_lock:
                    # toggle the block grid overlay
                    self.blocks.show_grid = not self.blocks.show_grid
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
                (self.dog.location.x - self.scroll[X] + 16)
                * SCALING_FACTOR + self.game_origin[X],
                (self.dog.location.y - self.scroll[Y])
                * SCALING_FACTOR + self.game_origin[Y]
                - self.dog.text_size[Y]
            )
            self.dog.draw_speech_bubble(display)
            self.screen.blit(self.dog.bubble, position)

        # draw the swirling dust - DEBUG disabled due to looking bad
        # self.dust_storm.update(self.screen, self.game_origin[Y], scroll)

        # draw the grid overlay last so it is on top of everything
        if self.blocks.show_grid:
            self.blocks.draw_grid(self.screen, self.game_origin, (0, 0, 0))
        # previously, the grid took the colour from the editor choice
        #                                  self.editor.get_fg_color())

        # TODO self.end_of_level_display()
        pygame.display.update()  # actually display

        self.frame_draw_time = time.time_ns() - frame_start_time
        self.clock.tick(60)  # lock the framerate to 60fps

    def end_of_level_display(self):
        # display end of level message

        color = (255, 255, 0)  # yellow
        line = self.code_font.render("level name" + " complete!",
                                     True, color)
        line_pos = [100, 100]
        self.screen.blit(line, line_pos)
