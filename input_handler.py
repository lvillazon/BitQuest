import pygame


class InputHandler(object):

    """
    dictionary mapping keypresses to actions
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

    class KeyAction(object):
        # defines the response for a single key

        def __init__(self, code, down=None, up=None, repeat=False, ctrl=False, alt=False, shift=False):
            self.key_code = code        # pygame keycode
            self.up_action = up         # function reference
            self.down_action = down     # function reference
            self.auto_repeat = repeat   # booleans
            self.ctrl = ctrl
            self.alt = alt
            self.shift = shift

        def check_modifiers(self, ctrl, alt, shift):
            return (ctrl == self.ctrl) and (alt == self.alt) and (shift == self.shift)

    def __init__(self):
        # create empty dictionary for key -> action mappings
        self.actions = {}
        self.repeat_lock = False

    def get_keystroke_name(self, key_code, ctrl, alt, shift):
        c = "CTRL+" if ctrl else ""
        a = "ALT+" if alt else ""
        s = "SHIFT+" if shift else ""
        return c + a + s + str(key_code)

    def register_key_press(self, key_code, action, release_action=None,
                           auto_repeat=False, ctrl=False, alt=False, shift=False):
        # associate the methods with the corresponding key
        # this allows other classes to define behaviour that should occur when a key is pressed or released
        # without needing to include the code to actually detect that event
        # key_code is one of the pygame key constants eg K_a
        # action and release_action are function calls

        self.actions[self.get_keystroke_name(key_code, ctrl, alt, shift)] = \
            self.KeyAction(key_code, action, release_action, auto_repeat, ctrl, alt, shift)

    def handle_key_presses(self):
        # tests for key presses and calls any registered actions

        # create a list of all the keys that are currently pressed
        all_key_states = pygame.key.get_pressed()
        ctrl = (pygame.key.get_mods() & pygame.KMOD_CTRL) > 0  # get current state of modifier keys
        shift = (pygame.key.get_mods() & pygame.KMOD_SHIFT) > 0
        alt = (pygame.key.get_mods() & pygame.KMOD_ALT) > 0

        # execute any registered actions that correspond to pressed keys
        for key_stroke in self.actions.keys():
            # keys without the auto_repeat flag set do not trigger additional actions if the key is held down
            if not self.repeat_lock or self.actions[key_stroke].auto_repeat:
                # check the key is pressed and the modifier key states match the registered values
                if all_key_states[self.actions[key_stroke].key_code] \
                        and self.actions[key_stroke].check_modifiers(ctrl, alt, shift) \
                        and self.actions[key_stroke].down_action != None:
                    self.actions[key_stroke].down_action()
                    self.repeat_lock = True

            if not all_key_states[self.actions[key_stroke].key_code] and self.actions[key_stroke].up_action:
                self.actions[key_stroke].up_action()

        # process all other events to clear the queue
        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                self.repeat_lock = False  # release the lock
            # if event.type == pygame.QUIT:
            #     self.running = False


"""        
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

        # the number keys allow jumping directly to that puzzle
        # this is only enabled if the user has map editing privileges
        if ALLOW_MAP_EDITOR:
            level_shortcuts = [
                K_0, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9
            ]
            for k in level_shortcuts:
                if pressed[k]:
                    self.puzzle = level_shortcuts.index(k)
                    self.rewind_level()

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
        # currently just the rewind and play button
        self.check_buttons()

        # process all other events to clear the queue
        for event in pygame.event.get():
            if event.type == KEYUP:
                self.repeat_lock = False  # release the lock
            if event.type == QUIT:
                self.running = False
"""