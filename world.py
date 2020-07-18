import time
import pygame
from pygame.locals import *
import editor
import interpreter
import scenery
import sprite_sheet

pygame.init()
pygame.display.set_caption("BIT Quest")
WINDOW_SIZE = (1024, 768)
EDITOR_HEIGHT = 300
DISPLAY_SIZE = (227, 170)
EDITOR_POPUP_SPEED = 25  # how fast the editor scrolls into view
# the actual game window
screen = pygame.display.set_mode(WINDOW_SIZE)
# the rendering surface for the game (heavily scaled)
display = pygame.Surface(DISPLAY_SIZE)

# general constants
X = 0  # index values into a variety of positional tuples
Y = 1
DEBUG = False  # when true enables extra debug messages in the console

# character animation constants
STANDING_FRAME = 7
PLAYER_X_OFFSET = int(DISPLAY_SIZE[X] / 2) - 16  # 16 = half of sprite width
PLAYER_Y_OFFSET = DISPLAY_SIZE[Y] - 32  # 32 = sprite height

clock = pygame.time.Clock()


###########################

class Character:
    ANIMATION_LENGTH = 8  # number of frames per movement
    STANDING_FRAME = 7  # the run frame used when standing still

    def __init__(self, sprite_file, run_speed=2):
        # load character animation frames
        self.character_sheet = \
            sprite_sheet.SpriteSheet('assets/' + sprite_file)
        self.run_right_frames = self.character_sheet.load_block_of_8(0, 0, -1)
        self.run_left_frames = [pygame.transform.flip(sprite, True, False)
                                for sprite in self.run_right_frames]
        self.jump_right_frames = self.character_sheet.load_block_of_8(0, 152,
                                                                      -1)
        self.jump_left_frames = [pygame.transform.flip(sprite, True, False)
                                 for sprite in self.jump_right_frames]
        self.die_right_frames = self.character_sheet.load_block_of_8(144, 0,
                                                                     -1)
        self.die_left_frames = [pygame.transform.flip(sprite, True, False)
                                for sprite in self.die_right_frames]
        self.moving = False
        self.facing_right = True
        self.location = {'x': 0, 'y': 0}
        self.frame_number = 0
        self.frame_count = len(self.run_right_frames)
        self.jumping = False
        self.run_speed = run_speed

    def update(self, surface, scroll):
        f = int(self.frame_number) % self.frame_count
        self.frame_number = self.frame_number + .25
        if self.moving:
            if self.facing_right:
                self.location['x'] += self.run_speed
            else:
                self.location['x'] -= self.run_speed
                # can't move past start of the world
                if self.location['x'] < 0:
                    self.location['x'] = 0

        if self.jumping:
            if self.facing_right:
                frame = self.jump_right_frames[f]
            else:
                frame = self.jump_left_frames[f]
            if self.frame_number == self.ANIMATION_LENGTH:
                self.jumping = False
        elif self.moving:
            if self.facing_right:
                frame = self.run_right_frames[f]
            else:
                frame = self.run_left_frames[f]
        else:  # standing
            if self.facing_right:
                # standing still is frame 7 on the animation cycle
                frame = self.run_right_frames[self.STANDING_FRAME]
            else:
                frame = self.run_left_frames[self.STANDING_FRAME]

        surface.blit(frame, (self.location['x'] - scroll['x'],
                             self.location['y'] - scroll['y']))

    def move_left(self):
        self.facing_right = False
        self.moving = True

    def move_right(self):
        self.facing_right = True
        self.moving = True

    def jump(self):
        self.jumping = True
        self.frame_number = 2  # reset frame counter for the jump animation

    def stop_moving(self):
        self.moving = False


#######################################################
# load scenery layers
scenery = scenery.Scenery('day', 'field')
true_scroll = {'x': 0.0, 'y': 0.0}
# location of the game area on the window
# used to scroll the game area out of the way of the code editor
game_origin = [0, 0]

# load character sprites
player = Character('character.png')
dog = Character('dog basic.png', run_speed=1)
player.location = {'x': 150, 'y': 170 - 32 - 2}
dog.location = {'x': player.location['x'] + 50,
                'y': player.location['y']}

# intialise the python interpreter
code = interpreter.Interpreter()
editor = editor.Editor(screen, 300)

game_running = True
frame_draw_time = 1

# game loop
while game_running:
    frame_start_time = time.time_ns()  # used to calculate fps

    # track the camera with the player, but with a bit of lag
    true_scroll['x'] += (player.location['x']
                         - true_scroll['x'] - PLAYER_X_OFFSET) / 16
    if true_scroll['x'] < 0:  # can't scroll past the start of the world
        true_scroll['x'] = 0
    true_scroll['y'] += (player.location['y']
                         - true_scroll['y'] - PLAYER_Y_OFFSET) / 16
    scroll = {'x': int(true_scroll['x']), 'y': int(true_scroll['y'])}

    # render the background
    scenery.draw_background(display, scroll)

    # move and render the player sprite
    player.update(display, scroll)

    # move and render the dog
    dog.update(display, scroll)
    # dog follows the player
    if dog.location['x'] > player.location['x'] + 30:
        dog.move_left()
    elif dog.location['x'] < player.location['x'] - 30:
        dog.move_right()
    else:
        dog.stop_moving()

    # draw the foreground scenery on top of the characters
    scenery.draw_foreground(display, scroll)

    # draw and update the editor, if necessary
    if editor.is_active():
        editor.update()
    else:
        # only handle keystrokes for game control if the editor isn't open
        pressed = pygame.key.get_pressed()
        if pressed[K_a]:
            player.move_left()
        elif pressed[K_d]:
            player.move_right()
        else:
            player.stop_moving()

        if pressed[K_SPACE]:
            player.jump()

        if pressed[K_ESCAPE]:
            # only show editor when it is completely hidden
            # this prevents it immediately reshowing after hiding
            if game_origin[Y] == 0:
                editor.show()

        # process all other events to clear the queue
        for event in pygame.event.get():
            if event.type == QUIT:
                game_running = False

    # DEBUG stats
    if pressed[K_f] or DEBUG == True:
        # display fps stats
        print('frame draw:{0}ms fps:{1} render budget left:{2}ms'.format(
            frame_draw_time / 1000000,
            int(1000000000 / frame_draw_time),
            int((1000000000 - 60 * frame_draw_time) / 1000000)))

    # scroll the editor in and out of view as required
    if editor.is_active():
        if game_origin[Y] > -editor.height:
            game_origin[Y] -= EDITOR_POPUP_SPEED
        editor.draw()
    elif game_origin[Y] < 0:
        game_origin[Y] += EDITOR_POPUP_SPEED

    # scale the rendering area to the actual game window
    screen.blit(pygame.transform.scale(display, WINDOW_SIZE), game_origin)
    # blit the editor underneath the game surface
    editor_position = (game_origin[X], game_origin[Y] + WINDOW_SIZE[Y])
    screen.blit(editor.surface, editor_position)

    pygame.display.update()  # actually display

    frame_draw_time = time.time_ns() - frame_start_time
    clock.tick(60)  # lock the framerate to 60fps

################################
# tidy up and quit
pygame.quit()
