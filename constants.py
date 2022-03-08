"""
Global config constants for BitQuest
"""
# TODO read this in from a file - using file_parser?

VERSION = "0.7"  # 0.x = beta testing phase
CONSOLE_VERBOSE = True  # when true enables extra debug messages in the console
SHOW_COLLIDERS = False  # draws outline around object colliders
SHOW_LOGIN_MENU = True  # displays the initial menu screen before play
ALLOW_COPY_PASTE = True
BYPASS_SENTRIES = False  # setting True, makes sentries non-collidable, for testing
X = 0  # index values into a variety of positional tuples
Y = 1

# fonts
CODE_FONT_FILE = "assets/DejaVuSansMono.ttf"
GRID_FONT_FILE = "assets/Pixel.ttf"
MENU_FONT_FILE = "assets/Vanilla.ttf"

# asset files
CHARACTER_SPRITE_FILE = 'assets/new_character.png'
DOG_SPRITE_FILE = 'assets/bit basic1.png'
ROBOT_SPRITE_FILE = 'assets/robots.png'
EDITOR_ICON_FILE = 'assets/editor icons.png'
BLOCK_TILE_DICTIONARY_FILE = 'assets/BitQuest_tileset.txt'
BLOCK_TILESET_FILE = 'assets/block tiles.png'
LEVEL_MAP_FILE_STEM = 'levels/BitQuest_level'
LEVEL_MAP_FILE_EXTENSION = '.txt'
USER_PROGRAM_FILE = 'assets/BitQuest_user_program.py'
SAVE_FILES_FOLDER = 'logs/'
SAVE_FILE_EXTENSION = '.log'
BACKUP_EXTENSION = '.bak'
REWIND_ICON_FILE = 'assets/rewind.png'
REWIND_HOVER_ICON_FILE = 'assets/rewind_hover.png'
PLAY_ICON_FILE = 'assets/play.png'
PLAY_HOVER_ICON_FILE = 'assets/play_hover.png'
PLAY_DISABLED_ICON_FILE = 'assets/play_disabled.png'
PUZZLE_FILE = 'levels/robot_puzzles.txt'
SENTRY_FILE = 'levels/robot_puzzles.txt'
USERNAMES_FILE = 'users/users.txt'

# XML stuff for files
SENTRY_START = '<SENTRY>'
SENTRY_END = '</SENTRY>'

# Robot Sentry constants
SENTRY_LISTENING_RANGE = 15

# editor constants
DEBUG = False  # when true enables extra debug messages in the console
MSG_VERBOSITY = 8  # 0-9, 0= no console messages, 9 = max
ALLOW_MAP_EDITOR = False  # allows the game map to be edited with Ctrl-Shift-G
SKY_BLUE = (0, 155, 255)
LIGHT_GREY = (230, 230, 230)
BLACK = (0, 0, 0)
YELLOW = (255, 229, 153)
GREEN = (113, 201, 168)

# world constants
WINDOW_SIZE = (908, 680)
EDITOR_HEIGHT = 300
SCALING_FACTOR = 4
DISPLAY_SIZE = (WINDOW_SIZE[X] // SCALING_FACTOR,
                WINDOW_SIZE[Y] // SCALING_FACTOR)
EDITOR_POPUP_SPEED = 25  # how fast the editor scrolls into view
EDITOR_UNDO_HISTORY = 100  # how many keystrokes can be undone
BLOCK_SIZE = 16  # size in pixels of a the block 'grid'
GRAVITY = .2
COLLIDE_THRESHOLD_Y = 1  # how many pixels overlap are required for a collision
BLOCK_OVERLAP = 9  # half of BLOCK_SIZE +1  - used to for collision tests
COLLIDER_WIDTH = 16
COLLIDER_HEIGHT = 16
REWIND_ICON_POS = (WINDOW_SIZE[X] - 72, 8)
PLAY_ICON_POS = (REWIND_ICON_POS[X] - 70, REWIND_ICON_POS[Y])

# puzzle definition constants
PUZZLE_NAME = 0
PLAYER_START = 1
DOG_START = 2

# character animation constants
STANDING_FRAME = 7
CHARACTER_WIDTH = 16
CHARACTER_HEIGHT = 16
# these 2 affect where the camera is centred as it follows the player
CAMERA_X_OFFSET = int(DISPLAY_SIZE[X] / 2) - CHARACTER_WIDTH * 5  # position camera to the right of the focus character
# the extra 10 means the display is not lined up exactly on the grid
CAMERA_Y_OFFSET = DISPLAY_SIZE[Y] - CHARACTER_HEIGHT * 2 - 10

# speech bubble & info panel constants
MAX_BUBBLE_TEXT_LINES = 15  # 10 lines maximum in a speech bubble
BUBBLE_MARGIN = 8  # 10-pixel border around text in the speech bubble
TEXT_MARGIN = 4  # pixel gap between the sides of the speech bubble and text
BORDER_THICKNESS = 3  # line thickness around speech bubbles & info panels
BALLOON_CORNER_RADIUS = 10
SPEECH_EXPIRY_TIME = 3000  # number of ms before the text begins to disappear
SPEECH_EXPIRY_RATE = 1000  # ms between each line of text disappearing
CROSS_THICKNESS = 2  # line thickness for the close button 'X'
DROP_SHADOW = 6  # used on info panels

# Block map constants
PALETTE_SCALE = 2  # the palette is scaled less than the normal level
GRID_LINE_WIDTH = 2
EDIT_INFO_BOX_POSITION = (0, 0)  # pixel coords
# EDIT_INFO_BOX_SIZE = (1)
PALETTE_POSITION = (182, 0)
DEFAULT_BLOCK_TYPE = '1'  # map editor defaults to basic dirt block
EDITOR_PALETTE_WIDTH = 16  # how many blocks wide for the block palette
PALETTE_GAP = 2  # pixels between tiles on the editor palette
PALETTE_CURSOR_SIZE = ((BLOCK_SIZE * PALETTE_SCALE + PALETTE_GAP),
                       (BLOCK_SIZE * PALETTE_SCALE + PALETTE_GAP))
_width = EDITOR_PALETTE_WIDTH * PALETTE_CURSOR_SIZE[X]
_height = 3 * PALETTE_CURSOR_SIZE[Y] + PALETTE_GAP
PALETTE_SIZE = (_width, _height)  # the rectangle for the map tile palette
LABEL_HEIGHT = 8

# parsing constants
NEW_LINE = '\n'

# Colour constants
COLOUR_SELECTED_BLOCK = (128, 128, 128)  # grey
COLOUR_MOVING_BLOCK = (128, 0, 0)  # red
COLOUR_TRIGGER_BLOCK = (0, 0, 128)  # blue
COLOUR_NEW_LINK = (0, 0, 255)  # bright blue
COLOUR_NORMAL_LINK = (255, 0, 0)  # bright red
COLOUR_RANDOM_LINK = (255, 255, 0)  # yellow
COLOUR_MOVER_OFFSET = (0, 255, 0)  # bright green
COLOUR_MENU_BG = (0x5D, 0x8A, 0xA8)  # air-force blue
COLOUR_MENU_TITLE = (0xFF, 0xBF, 0x00)  # amber
COLOUR_MENU_TEXT = (0xFF, 0xBF, 0x00)  # amber
COLOUR_MENU_USERNAME = (0x87, 0x3e, 0x23)  # terracotta
COLOUR_MENU_CLASSNAME = (0, 0, 0)
COLOUR_MAP_EDITOR_BOXES = (0xc2, 0xc2, 0xa3)
COLOUR_GRID_LINES = (0, 0, 0)
COLOUR_MAP_EDIT_TEXT = (0, 0, 0)
COLOUR_MAP_CURSOR = (255, 255, 255)

