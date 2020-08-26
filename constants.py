'''
Global constants for BitQuest
'''
CONSOLE_VERBOSE = True # when true enables extra debug messages in the console

X = 0  # index values into a variety of positional tuples
Y = 1
DEBUG = False  # when true enables extra debug messages in the console
EDITOR_MODE = True

# world constants
WINDOW_SIZE = (908, 680)
EDITOR_HEIGHT = 300
DISPLAY_SIZE = (227, 170)
SCALING_FACTOR = 4
EDITOR_POPUP_SPEED = 25  # how fast the editor scrolls into view
BLOCK_SIZE = 16  # size in pixels of a the block 'grid'
GRAVITY = 0.2
COLLIDE_THRESHOLD = 1  # how many pixels overlap are required for a collision

# character animation constants
STANDING_FRAME = 7
# these 2 affect where the camera is centred as it follows the player
CAMERA_X_OFFSET = int(DISPLAY_SIZE[X] / 2) - 16  # 16 = half of sprite width
CAMERA_Y_OFFSET = DISPLAY_SIZE[Y] - 32 - 10  # 32 = sprite height
CHARACTER_SIZE = 32