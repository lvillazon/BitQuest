"""
 BitQuest module to handle the game world rendering
 and character movement
"""
import time

import pygame
from pygame.locals import *

import blocks
import characters
import code_editor
import input_dialog
import interpreter
import scenery
from camera import Camera
from console_messages import console_msg
from constants import *
from input_handler import KeyboardHandler, MouseHandler

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

        self.camera = Camera()
        # location of the game area on the window
        # used to scroll the game area out of the way of the code editor
        # this can't be done by the camera, because the editor is always just 'below' the visible part of the map
        # regardless of where the camera is currently panned to. In other words, the editor is not part of the
        # game world.
        self.game_origin = [0, 0]

        # load puzzle blocks
        self.blocks = blocks.BlockMap(self,
                                      BLOCK_TILE_DICTIONARY_FILE,
                                      BLOCK_TILESET_FILE, self.camera)
        console_msg("Map loaded", 1)

        self.puzzle = 0  # TODO: load current progress from log file
        self.session.set_current_level(
            self.blocks.get_puzzle_name(self.puzzle)
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
        self.player.set_position(self.blocks.get_player_start(self.puzzle))
        self.dog.set_position(self.blocks.get_dog_start(self.puzzle))

        self.dog.facing_right = False
        self._show_fps = False
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

        self.editor = code_editor.CodeWindow(screen, 300,
                                             self.code_font,
                                             self.python_interpreter,
                                             self.session)
        input_height = self.code_font.get_linesize() * 3
        self.input = input_dialog.InputDialog(screen, input_height, self.code_font)
        console_msg("Editors initialised", 2)

        self.camera_shake = False
        self.camera_pan = [0, 0]
        self.camera_up = False  # true when the view is panning up
        self.camera_down = False  # true when the view is panning down
        self.running = True  # true when we are playing a level (not a menu)
        self.frame_draw_time = 1
        self.frame_counter = 0
        self.clock = pygame.time.Clock()

        # register all the keyboard and mouse actions
        self.keyboard_input = KeyboardHandler()
        self.mouse_input = MouseHandler(self.camera)
        self.keyboard_input.register_key_down('A', self.player.move_left)
        self.keyboard_input.register_key_down('D', self.player.move_right)
        self.keyboard_input.register_key_down('W', self.camera_pan_up)
        self.keyboard_input.register_key_up('W', self.camera_pan_up_release)
        self.keyboard_input.register_key_down('S', self.camera_pan_down)
        self.keyboard_input.register_key_up('S', self.camera_pan_down_release)
        self.keyboard_input.register_key_press('ESCAPE', self.show_editor)
        self.keyboard_input.register_key_press('G', self.blocks.toggle_grid)
        self.keyboard_input.register_key_press('F', self.toggle_fps_stats)

        # the number keys allow jumping directly to that puzzle
        # this is only enabled if the user has map editing privileges
        if ALLOW_MAP_EDITOR:
            for k in "0123456789":
                # dynamically create a function that jumps to the required level and register it to that key press
                jump_to_level = self.get_level_shortcut(int(k))
                self.keyboard_input.register_key_press(k, jump_to_level)

            """
            keyboard actions for map edit mode
            K_a:  # move left
            K_d:  # move right
            K_w:  # look up
            K_s:  # look down
            K_Escape:  # toggle editor
            K_0 ... K_9:  # level shortcuts

            # map edit mode
            K_F9  # save map
            K_LEFT/RIGHT/UP/DOWN:  # move cursor
            CTRL+K_UP/DOWN:  # pan camera
            K_BACKSPACE:  # delete block/mover/trigger
            K_RETURN:     # change/add a block at the current grid cursor location
            K_TAB:  # switch between midground and foreground block layers
            K_r:    # reset all block triggers and movers
            K_h:    # home the cursor to the centre of the screen
            K_m:    # turn the selection into a movable group
            K_t     # turn the block at the cursor into a trigger or link an existing trigger to a mover
            K_l     # toggle random mode for the trigger actions if the cursor is currently on a trigger
            K_INSERT  # insert a new column of blocks at the cursor
            K_DELETE  # remove a column at the cursor

            # left click: select current block
            # SHIFT+left click: add current block to selection
            # right click:  set current block as the selected block type ('eyedropper' tool)


            K_f:  # display framerate stats
            K_g:  # toggle grid
            CTRL+SHIFT+K_g:  # toggle map editor
            """
            self.keyboard_input.register_key_press('CTRL+SHIFT+G', self.blocks.toggle_map_editor)
            self.keyboard_input.register_key_press('F9', self.blocks.save_grid)
            self.keyboard_input.register_key_press('RIGHT', self.blocks.cursor_right)
            self.keyboard_input.register_key_press('LEFT', self.blocks.cursor_left)
            self.keyboard_input.register_key_press('UP', self.blocks.cursor_up)
            self.keyboard_input.register_key_press('CTRL+UP', self.camera_pan_up)
            self.keyboard_input.register_key_press('DOWN', self.blocks.cursor_down)
            self.keyboard_input.register_key_press('CTRL+DOWN', self.camera_pan_down)
            self.keyboard_input.register_key_press('BACKSPACE', self.blocks.delete)
            self.keyboard_input.register_key_press('RETURN', self.blocks.change_block)
            self.keyboard_input.register_key_press('TAB', self.blocks.switch_layer)
            self.keyboard_input.register_key_press('R', self.blocks.reset)
            self.keyboard_input.register_key_press('H', self.blocks.home_cursor)
            self.keyboard_input.register_key_press('M', self.blocks.create_mover)
            self.keyboard_input.register_key_press('T', self.blocks.set_trigger)
            self.keyboard_input.register_key_press('L', self.blocks.toggle_trigger_randomness)
            self.keyboard_input.register_key_press('INSERT', self.blocks.insert_column)
            self.keyboard_input.register_key_press('DELETE', self.blocks.delete_column)

            self.mouse_input.register_left_click(self.blocks.add_to_selection, 'SHIFT')
            self.mouse_input.register_left_click(self.blocks.select_block, 'NONE')
            self.mouse_input.register_right_click(self.blocks.pick_block, 'NONE')

        console_msg("Input handler initialised", 2)
        console_msg("World initialisation complete", 1)

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

        self.camera.update(focus)

        # render the background
        self.scenery.draw_background(display, self.camera.scroll())

        # move and render the player sprite
        self.player.update(display, self.camera.scroll())

        # move and render the dog
        self.dog.update(display, self.camera.scroll())

        # draw the foreground scenery on top of the characters
        self.blocks.update(display, self.camera.scroll())
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
            self.keyboard_input.handle_actions()
            self.mouse_input.handle_actions()
            # process all other events to clear the queue
            # for event in pygame.event.get():
            #     if event.type == QUIT:
            #         self.running = False

        if self._show_fps:
            self.show_fps()

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
            position = self.dog.speech_position()
            position[X] = (position[X] - self.camera.scroll_x()) * SCALING_FACTOR + self.game_origin[X]
            position[Y] = (position[Y] - self.camera.scroll_y()) * SCALING_FACTOR + self.game_origin[Y]
            self.screen.blit(self.dog.get_speech_bubble(display), position)

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

    def show_fps(self):
        # debug info - display current fps stats to console.
        self.frame_counter += 1
        if self.frame_counter > 60:
            self.frame_counter = 0
            console_msg(
                'frame draw:{0}ms fps:{1} render budget left:{2}ms'.format(
                    self.frame_draw_time / 1000000,
                    int(1000000000 / self.frame_draw_time),
                    int((1000000000 - 60
                         * self.frame_draw_time) / 1000000)), 1)

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
        self.player.set_position(self.blocks.get_player_start(self.puzzle))
        self.dog.set_position(self.blocks.get_dog_start(self.puzzle))
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

    def camera_pan_up(self):
        if self.blocks.map_edit_mode:
            self.camera_pan[Y] -= BLOCK_SIZE
        else:
            self.camera_pan[Y] -= 2
        self.camera_up = True

    def camera_pan_down(self):
        if self.blocks.map_edit_mode:
            self.camera_pan[Y] += BLOCK_SIZE
        else:
            self.camera_pan[Y] += 2
        self.camera_down = True

    def camera_pan_up_release(self):
        self.camera_up = False
        self.camera_recentre()

    def camera_pan_down_release(self):
        self.camera_down = False
        self.camera_recentre()

    def camera_recentre(self):
        if not (self.camera_up or self.camera_down) and not self.blocks.map_edit_mode:
            self.camera_pan[Y] = int(self.camera_pan[Y] * 0.9)

    def show_editor(self):
        # only show editor when it is completely hidden
        # this prevents it immediately reshowing after hiding
        if self.game_origin[Y] == 0:
            self.editor.show()

    def get_level_shortcut(self, level_number):
        # returns a function that jumps straight to the start of a level

        def short_cut():
            self.puzzle = level_number
            self.rewind_level()

        return short_cut

    def toggle_fps_stats(self):
        self._show_fps = not self._show_fps
        if not self._show_fps:
            self.frame_counter = 0


    # def test_multiple(self, key):
    #     print("handling",key)