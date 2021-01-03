"""
 BitQuest module to handle the game world rendering
 and character movement
"""
import random
import time
from datetime import datetime

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
from sprite_sheet import SpriteSheet

'''
https://wiki.libsdl.org/Installation
https://github.com/pygame/pygame/issues/1722
'''


class World:
    def __init__(self, screen, display, session):
        console_msg('Initialising world.', 0)
        self.screen = screen
        self.display = display
        self.session = session

        # load play/rewind icon images
        self.rewinding = False
        self.rewind_rotation = 0
        self.rewind_icon = pygame.image.load(REWIND_ICON_FILE).convert()
        self.rewind_icon.set_colorkey((255, 255, 255), RLEACCEL)
        self.rewind_hover_icon = pygame.image.load(
            REWIND_HOVER_ICON_FILE).convert()
        self.rewind_hover_icon.set_colorkey((255, 255, 255), RLEACCEL)

        self.play_icon = pygame.image.load(PLAY_ICON_FILE).convert()
        self.play_icon.set_colorkey((255, 255, 255), RLEACCEL)
        self.play_hover_icon = pygame.image.load(
            PLAY_HOVER_ICON_FILE).convert()
        self.play_hover_icon.set_colorkey((255, 255, 255), RLEACCEL)
        self.play_disabled_icon = pygame.image.load(
            PLAY_DISABLED_ICON_FILE).convert()
        self.rewind_button_rect = pygame.Rect(REWIND_ICON_POS, (64, 64))
        self.play_button_rect = pygame.Rect(PLAY_ICON_POS, (64, 64))
        # when True the play button is displayed and programs can be run
        # once a program runs, this is set to false and the rewind button
        # is shown instead.
        self.run_enabled = True

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

        # set the names and player/dog start positions for all the puzzles
        # TODO this should be part of the level map file
        self.puzzle_info = {0: ("the pillar", (4, 6), (6, 8)),
                            1: ("the pit", (58, 6), (57, 8)),
                            2: ("the lift", (80, 6), (78, 8)),
                            3: ("the staircase", (91, 6), (90, 8)),
                            4: ("the choice", (105, 6), (103, 8)),
                            }
        self.puzzle = 0
        self.session.set_current_level(
            self.puzzle_info[self.puzzle][PUZZLE_NAME]
        )
        self.session.save_header()

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
        self.player.set_position(self.puzzle_info[self.puzzle][PLAYER_START])
        self.dog.set_position(self.puzzle_info[self.puzzle][DOG_START])

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

        self.python_interpreter = interpreter.VirtualMachine(self)
        console_msg("Interpreter initialised", 2)

        self.editor = editor.CodeWindow(screen, 300,
                                        self.code_font,
                                        self.python_interpreter,
                                        self.session)
        input_height = self.code_font.get_linesize() * 3
        self.input = editor.InputDialog(screen, input_height, self.code_font)
        console_msg("Editors initialised", 2)

        self.camera_shake = False
        self.camera_pan = [0, 0]
        self.running = True  # true when we are playing a level (not a menu)
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
            # still need to check if buttons outside the editor were clicked
            self.check_buttons()
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

            if self.blocks.map_edit_mode:
                ctrl = pygame.key.get_mods() & KMOD_CTRL
                shift = pygame.key.get_mods() & KMOD_SHIFT

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
# not used, now we have a block palette on-screen
#                        self.blocks.previous_editor_tile()
                        pass
                    elif pressed[K_RIGHTBRACKET]:  # ]
#                        self.blocks.next_editor_tile()
                        pass
                    elif pressed[K_BACKSPACE]:
                        if self.blocks.mover_is_selected():
                            console_msg("deleting mover", 8)
                            self.blocks.remove_moveable_group()
                        elif self.blocks.trigger_is_selected():
                            console_msg("deleting trigger", 8)
                            self.blocks.remove_trigger()
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
                        # reset all block triggers and movers
                        self.blocks.reset()
                    elif pressed[K_h]:
                        # home the cursor to the centre of the screen
                        self.blocks.home_cursor()
                    elif pressed[K_m]:
                        # turn the selection into a movable group
                        self.blocks.create_mover()
                    elif pressed[K_t]:
                        # turn the block at the cursor into a trigger
                        # or link an existing trigger to a mover
                        self.blocks.set_trigger()
                    elif pressed[K_l]:
                        # toggle random mode for the trigger actions
                        # if the cursor is currently on a trigger
                        self.blocks.toggle_trigger_randomness()
                    elif pressed[K_INSERT]:
                        # insert a new column of blocks at the cursor
                        self.blocks.insert_column()
                    elif pressed[K_DELETE]:
                        # remove a column at the cursor
                        self.blocks.delete_column()
                    else:
                        self.repeat_lock = False  # reset, since no key pressed

                        for event in pygame.event.get():
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                mouse_pos = (pygame.mouse.get_pos()[X]
                                             / SCALING_FACTOR
                                             + self.scroll[X],
                                             pygame.mouse.get_pos()[Y]
                                             / SCALING_FACTOR
                                             + self.scroll[Y]
                                             )
                                if event.button == 1:  # left click
                                    if shift:
                                        self.blocks.select_block(mouse_pos,
                                                                 'add')
                                    else:
                                        # just select a single block
                                        self.blocks.select_block(mouse_pos,
                                                                 'set')
                                elif event.button == 3:  # right click
                                    self.blocks.select_block(mouse_pos, 'pick')
                            # 2: middle button
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
                ctrl = pygame.key.get_mods() & KMOD_CTRL
                shift = pygame.key.get_mods() & KMOD_SHIFT
                if not self.repeat_lock:
                    if ALLOW_MAP_EDITOR and ctrl and shift:
                        self.blocks.toggle_map_editor()
                    else:
                        self.blocks.toggle_grid()
                    self.repeat_lock = True
            # check the mouse to see if any buttons were clicked
            # currently just the rewind button
            self.check_buttons()

            # process all other events to clear the queue
            for event in pygame.event.get():
                if event.type == KEYUP:
                    self.repeat_lock = False  # release the lock
                if event.type == QUIT:
                    self.running = False

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

        # draw the grid overlay next so it is on top of all blocks
        if self.blocks.show_grid:
            self.blocks.draw_grid(self.screen, self.game_origin)
        # previously, the grid took the colour from the editor choice
        #                                  self.editor.get_fg_color())

        # draw the map editor info panel and block palette
        if self.blocks.map_edit_mode:
            self.blocks.draw_edit_info_box(self.screen)
            # self.blocks.draw_block_palette(self.screen, self.game_origin)

        # draw the rewind button in the top right corner
        if self.rewinding:
            # update the rotation animation
            self.rewind_rotation = (self.rewind_rotation + 10)
            if self.rewind_rotation >= 360:
                self.rewind_rotation = 0
                self.rewinding = False
            rewind_animation_icon = pygame.transform.rotate(
                self.rewind_hover_icon,
                self.rewind_rotation
            )
            icon_size = rewind_animation_icon.get_size()
            self.screen.blit(rewind_animation_icon,
                             (REWIND_ICON_POS[X] + 32 - icon_size[X] / 2,
                              REWIND_ICON_POS[Y] + 32 - icon_size[Y] / 2)
                             )
        else:
            if self.rewind_button_rect.collidepoint(pygame.mouse.get_pos()):
                self.screen.blit(self.rewind_hover_icon, REWIND_ICON_POS)
            else:
                self.screen.blit(self.rewind_icon, REWIND_ICON_POS,
                                 special_flags=BLEND_RGB_MULT
                                 )
        # play button
        if self.python_interpreter.run_enabled:
            if self.play_button_rect.collidepoint(pygame.mouse.get_pos()):
                self.screen.blit(self.play_hover_icon, PLAY_ICON_POS)
            else:
                self.screen.blit(self.play_icon, PLAY_ICON_POS,
                                 special_flags=BLEND_RGB_MULT
                                 )
        else:
            self.screen.blit(self.play_disabled_icon, PLAY_ICON_POS,
                             special_flags=BLEND_RGB_MULT
                             )

            # TODO self.end_of_level_display()
        pygame.display.update()  # actually display

        self.frame_draw_time = time.time_ns() - frame_start_time
        self.clock.tick(60)  # lock the framerate to 60fps

    def check_buttons(self):
        """ react to any button clicks """
        # currently just checking the rewind & play button
        if self.rewind_button_rect.collidepoint(*pygame.mouse.get_pos()):
            # button 0 is left click
            if not self.rewinding and pygame.mouse.get_pressed()[0]:
                # Rewind everything to the start of the level
                self.rewind_level()
                self.python_interpreter.run_enabled = True
        elif self.play_button_rect.collidepoint(*pygame.mouse.get_pos()):
            if (self.python_interpreter.run_enabled and
                    pygame.mouse.get_pressed()[0]):
                # run user program
                self.editor.run_program()

    def rewind_level(self):
        console_msg("Rewinding!", 8)
        self.rewinding = True
        self.blocks.reset()
        self.player.set_position(
            self.puzzle_info[self.puzzle][PLAYER_START])
        self.dog.set_position(
            self.puzzle_info[self.puzzle][DOG_START])
        self.dog.clear_speech_bubble()

    def end_of_level_display(self):
        # display end of level message

        color = (255, 255, 0)  # yellow
        line = self.code_font.render("level name" + " complete!",
                                     True, color)
        line_pos = [100, 100]
        self.screen.blit(line, line_pos)

    def complete_level(self, name):
        self.session.save_checkpoint_reached(name)
        self.puzzle += 1
        self.python_interpreter.run_enabled = True
