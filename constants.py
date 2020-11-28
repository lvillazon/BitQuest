"""
Global constants for BitQuest
"""

CONSOLE_VERBOSE = True  # when true enables extra debug messages in the console
SHOW_COLLIDERS = False  # draws outline around object colliders
X = 0  # index values into a variety of positional tuples
Y = 1

# asset files
CHARACTER_SPRITE_FILE = 'assets/new_character.png'
DOG_SPRITE_FILE = 'assets/bit basic1.png'
EDITOR_ICON_FILE = 'assets/editor icons.png'
CODE_FONT_FILE = "assets/DejaVuSansMono.ttf"
GRID_FONT_FILE = "assets/Pixel.ttf"
BLOCK_TILE_DICTIONARY_FILE = 'assets/BitQuest_tileset.txt'
BLOCK_TILESET_FILE = 'assets/block tiles.png'
LEVEL_MAP_FILE_STEM = 'assets/BitQuest_level'
LEVEL_MAP_FILE_EXTENSION = '.txt'
USER_PROGRAM_FILE = 'assets/BitQuest_user_program.py'

# editor constants
DEBUG = False  # when true enables extra debug messages in the console
MSG_VERBOSITY = 8  # 0-9, 0= no console messages, 9 = max
MAP_EDITOR_ENABLED = True  # when true allows the game map to be edited in-game
SKY_BLUE = (0, 155, 255)
LIGHT_GREY = (230, 230, 230)
BLACK = (0, 0, 0)
YELLOW = (255, 229, 153)
GREEN = (113, 201, 168)

# world constants
WINDOW_SIZE = (908, 680)
EDITOR_HEIGHT = 300
DISPLAY_SIZE = (227, 170)
SCALING_FACTOR = 4
EDITOR_POPUP_SPEED = 25  # how fast the editor scrolls into view
EDITOR_UNDO_HISTORY = 100  # how many keystrokes can be undone
BLOCK_SIZE = 16  # size in pixels of a the block 'grid'
GRAVITY = .2
COLLIDE_THRESHOLD_Y = 1  # how many pixels overlap are required for a collision
BLOCK_OVERLAP = 9 # half of BLOCK_SIZE +1  - used to for collision tests
COLLIDER_WIDTH = 16
COLLIDER_HEIGHT = 16

# character animation constants
STANDING_FRAME = 7
# these 2 affect where the camera is centred as it follows the player
CAMERA_X_OFFSET = int(DISPLAY_SIZE[X] / 2) - 16  # 16 = half of sprite width
CAMERA_Y_OFFSET = DISPLAY_SIZE[Y] - 32 - 10  # 32 = sprite height
CHARACTER_SIZE = 32
CHARACTER_WIDTH = 16
CHARACTER_HEIGHT = 16

# speech bubble constants
MAX_BUBBLE_TEXT_LINES = 10  # 10 lines maximum in a speech bubble
BUBBLE_MARGIN = 8  # 10-pixel border around text in the speech bubble
TEXT_MARGIN = 4  # pixel gap between the sides of the speech bubble and text
BALLOON_THICKNESS = 3  # line thickness around speech bubbles
SPEECH_EXPIRY_TIME = 3000 # number of ms before the text begins to disappear
SPEECH_EXPIRY_RATE = 1000 # ms between each line of text disappearing

# Block map constants
GRID_LINE_WIDTH = 2

# Colour constants
COLOUR_SELECTED_BLOCK = (128, 128, 128)  # grey
COLOUR_MOVING_BLOCK = (128, 0, 0)  # red
COLOUR_TRIGGER_BLOCK = (0, 0, 128)  # red
