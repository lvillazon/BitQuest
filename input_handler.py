import pygame
from console_messages import console_msg
from constants import *

# the modifier keys that are recognised by the game - any others will not be checked
VALID_MODIFIER_KEYS = [pygame.KMOD_CTRL, pygame.KMOD_SHIFT, pygame.KMOD_ALT]
VALID_MODIFIER_NAMES = ['CTRL', 'SHIFT', 'ALT']


def get_modifier_list(key_combo):
    # looks for the names of any modifier keys in the key_combo string
    # and returns a list of the pygame modifier codes for any it finds
    key_mods = []
    for i in range(len(VALID_MODIFIER_NAMES)):
        if VALID_MODIFIER_NAMES[i] in key_combo.upper():
            key_mods.append(VALID_MODIFIER_KEYS[i])
    return key_mods


def normalise_mod_string(mod_string):
    # makes sure the string of mods is in a standard form
    # eg it will convert 'SHIFT-CTRL' to 'CTRL+SHIFT'

    # standardise the order
    mod_names = []
    for mod in VALID_MODIFIER_NAMES:
        if mod in mod_string.upper():
            mod_names.append(mod)
    if len(mod_names) == 0:
        return 'NONE'
    else:
        return "+".join(mod_names)          # standardises the separator


def mods_to_string(modifier_code):
    shift = ''
    ctrl = ''
    alt = ''
    if modifier_code & pygame.KMOD_SHIFT:
        shift = 'SHIFT'
    if modifier_code & pygame.KMOD_CTRL:
        ctrl = 'CTRL'
    if modifier_code & pygame.KMOD_ALT:
        alt = 'ALT'
    if len(ctrl+shift+alt) > 0:
        print(ctrl+shift+alt)
        return normalise_mod_string(ctrl+shift+alt)
    else:
        print('none')
        return 'NONE'


def get_key_name(key_combo):
    # key combo is the name of the key, with modifiers optionally preceding it
    # eg Ctrl+A or ESCAPE or Alt+Shift+UP
    # modifiers can be in any order and separated by any non-alphanumeric character
    # case is not significant
    # to find the key name, work back from the end of the string,
    # until you reach the first non-alphanumeric, or the beginning of the string, whichever is 1st
    position = len(key_combo) - 1
    while position >= 0 and key_combo[position].isalnum():
        position -= 1
    key_name = key_combo[position + 1:]
    return key_name


def get_key_code(key_name):
    return pygame.key.key_code(key_name)


class InputAction(object):
    # generic class for defined mouse or keyboard actions

    def __init__(self, input_combo, action):
        self.combo = input_combo  # string representing the event eg CTRL+S or ESCAPE or LEFT_CLICK
        self.modifier_keys = get_modifier_list(input_combo)  # list of pygame KMOD_xxx values eg KMOD_SHIFT
        self.action = action  # the function that is called when the input event is detected
        console_msg("Registering event for " + self.combo + " mods=" + str(self.modifier_keys), 9)

    def check_mods(self):
        # check that each of the modifiers required for this key action match the current keyboard state
        for mod in VALID_MODIFIER_KEYS:
            # if the modifier is listed for this key action, then it must be pressed for the mod check to pass
            # if it isn't listed then it must NOT be pressed for the mod check to pass
            if mod in self.modifier_keys:
                if pygame.key.get_mods() & mod == 0:
                    return False
            else:
                if pygame.key.get_mods() & mod == 1:
                    return False
        return True


class KeyboardAction(InputAction):
    def __init__(self, input_combo, action):
        super().__init__(input_combo, action)
        self.key_name = get_key_name(self.combo)  # separate the key eg 'A' from the combo eg 'CTRL+A'
        # make sure the mod names are in a standard order
        self.combo = normalise_mod_string(self.combo) + '+' + self.key_name
        self.key_code = pygame.key.key_code(self.key_name)


class KeyboardHandler(object):
    def __init__(self):
        # create empty dictionary for key -> action mappings
        self.down_actions = {}
        self.up_actions = {}
        self.press_actions = {}

    def register_key_press(self, key_combo, action):
        # assigns a single keypress or key+modifiers combo to a function call
        # eg 'A' or 'ESCAPE' or 'CTRL+S'
        self.press_actions[key_combo] = KeyboardAction(key_combo, action)

    def register_key_up(self, key_combo, action):
        self.up_actions[key_combo] = KeyboardAction(key_combo, action)

    def register_key_down(self, key_combo, action):
        self.down_actions[key_combo] = KeyboardAction(key_combo, action)

    def handle_actions(self):
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


class MouseHandler(object):
    def __init__(self, camera):
        self.camera = camera  # link to camera so that the mouse can return coords that take scroll into account

        # click actions are stored in a dictionary indexed by a string representing the modifier keys
        # so the action for Ctrl+Shift+left click would be in
        # self.left_click['CTRL+SHIFT']
        self.left_click_actions = {}
        self.right_click_actions = {}

    def get_pos(self):
        mouse_x = pygame.mouse.get_pos()[X] / SCALING_FACTOR + self.camera.scroll_x()
        mouse_y = pygame.mouse.get_pos()[Y] / SCALING_FACTOR + self.camera.scroll_y()
        return [mouse_x, mouse_y]

    def register_left_click(self, action, modifiers=''):
        # assigns the left mouse button to a function call
        # the modifier text is converted to the pygame numeric code and back again
        self.left_click_actions[normalise_mod_string(modifiers)] = InputAction(modifiers, action)

    def register_right_click(self, action, modifiers=''):
        # assigns the right mouse button to a function call
        # the modifier text is converted to the pygame numeric code and back again
        self.right_click_actions[normalise_mod_string(modifiers)] = InputAction(modifiers, action)

    def handle_actions(self):
        # call the registered actions for any mouse events

        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            action_list = None
            if event.button == 1:  # left click
                action_list = self.left_click_actions
            elif event.button == 3:  # right_click
                action_list = self.right_click_actions
            # # 2: middle button
            # # 4: scroll up
            # # 5: scroll down

            if action_list is not None:
                current_mod_code = pygame.key.get_mods()
                current_mod_string = mods_to_string(current_mod_code)
                # check if we have a left-click action registered for this particular modifier key combination
                if current_mod_string in action_list.keys():
                    # call the action and pass the mouse position as a parameter
                    # mouse coords take into account the camera position, to give game world coords
                    action_list[current_mod_string].action(self.get_pos())
