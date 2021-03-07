import pygame

# the modifier keys that are recognised by the game - any others will not be checked
VALID_MODIFIER_KEYS = [pygame.KMOD_CTRL, pygame.KMOD_SHIFT, pygame.KMOD_ALT]


def get_key_code(key_combo):
    # key combo is the name of the key, with modifiers optionally preceding it
    # eg Ctrl+A or ESCAPE or Alt+Shift+UP
    # modifiers can be in any order and separated by any non-alphanumeric character
    # case is not significant
    # to find the key name, work back from the end of the string,
    # until you reach the first non-alphanumeric, or the beginning of the string, whichever is 1st#
    position = len(key_combo) - 1
    while position >= 0 and key_combo[position].isalnum():
        position -= 1
    key_name = key_combo[position + 1:]
    name = pygame.key.key_code(key_name)
    return name


def get_modifier_list(key_combo):
    # looks for the names of any modifier keys in the key_combo string
    # and returns a list of the pygame modifier codes for any it finds
    key_mods = []
    if "CTRL" in key_combo.upper():
        key_mods.append(pygame.KMOD_CTRL)
    if "ALT" in key_combo.upper():
        key_mods.append(pygame.KMOD_ALT)
    if "SHIFT" in key_combo.upper():
        key_mods.append(pygame.KMOD_SHIFT)
    return key_mods


class InputHandler(object):
    """
    dictionary mapping key presses to actions
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

        def __init__(self, key_combo, action):
            self.key_code = get_key_code(key_combo)
            self.key_modifiers = get_modifier_list(key_combo)
            self.action = action
            print("Adding key action for", key_combo, self.key_code, self.key_modifiers)

        def check_mods(self):
            # check that each of the modifiers required for this key action match the current keyboard state
            for mod in VALID_MODIFIER_KEYS:
                # if the modifier is listed for this key action, then it must be pressed for the mod check to pass
                # if it isn't listed then it must NOT be pressed for the mod check to pass
                if mod in self.key_modifiers:
                    if pygame.key.get_mods() & mod == 0:
                        return False
                else:
                    if pygame.key.get_mods() & mod == 1:
                        return False
            return True

    def __init__(self):
        # create empty dictionary for key -> action mappings
        self.down_actions = {}
        self.up_actions = {}
        self.press_actions = {}

    def register_key_press(self, key_combo, action):
        self.press_actions[key_combo] = self.KeyAction(key_combo, action)

    def register_key_release(self):
        pass

    def register_key_up(self, key_combo, action):
        self.up_actions[key_combo] = self.KeyAction(key_combo, action)

    def register_key_down(self, key_combo, action):
        self.down_actions[key_combo] = self.KeyAction(key_combo, action)

    def handle_keyboard_input(self):
        # call the registered actions for any keyboard events

        # get a list of all the keys that are currently pressed
        all_key_states = pygame.key.get_pressed()
        for key_combo in self.down_actions:
            if (all_key_states[self.down_actions[key_combo].key_code]  # key is pressed
                    and self.down_actions[key_combo].check_mods()):    # modifiers match too
                self.down_actions[key_combo].action()                  # so call the registered action

        # now check for those actions that trigger when a key is NOT pressed
        for key_combo in self.up_actions:
            if not all_key_states[self.up_actions[key_combo].key_code]:  # key is NOT pressed
                self.up_actions[key_combo].action()  # so call the registered action

        # now check for actions that only trigger at the moment the key is pressed down
        for event in pygame.event.get(pygame.KEYDOWN):
            for key_combo in self.press_actions:
                if (self.press_actions[key_combo].key_code == event.key
                        and self.press_actions[key_combo].check_mods()):
                    self.press_actions[key_combo].action()
