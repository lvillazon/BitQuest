import contextlib
import io
import time
import pygame
from pygame.locals import *

import editor
import interpreter
import scenery
import sprite_sheet
from constants import *
'''
https://wiki.libsdl.org/Installation
https://github.com/pygame/pygame/issues/1722
'''

# set environment variables to request the window manager to position the top left of the game window
import os
position = 0, 30  # setting y to 0 will place the title bar off the screen
os.environ['SDL_VIDEO_WINDOW_POS'] = str(position[0]) + "," + str(position[1])

pygame.init()
pygame.display.set_caption("BIT Quest")
WINDOW_SIZE = (908, 680)
EDITOR_HEIGHT = 300
DISPLAY_SIZE = (227, 170)
SCALING_FACTOR = 4
EDITOR_POPUP_SPEED = 25  # how fast the editor scrolls into view
# the actual game window
screen = pygame.display.set_mode(WINDOW_SIZE)
# the rendering surface for the game (heavily scaled)
display = pygame.Surface(DISPLAY_SIZE)

# character animation constants
STANDING_FRAME = 7
PLAYER_X_OFFSET = int(DISPLAY_SIZE[X] / 2) - 16  # 16 = half of sprite width
PLAYER_Y_OFFSET = DISPLAY_SIZE[Y] - 32  # 32 = sprite height

clock = pygame.time.Clock()


###########################

class Character:
    ANIMATION_LENGTH = 8  # number of frames per movement
    STANDING_FRAME = 7  # the run frame used when standing still
    BUBBLE_MARGIN = 10  # 10-pixel border around text in the speech bubble
    MAX_TEXT_LINES = 10  # 10 lines maximum in a speech bubble

    def __init__(self, world, sprite_file, run_speed=2):
        self.world = world  # link back to the world game state
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
        self.speaking = False
        self.text = []
        self.text_size = [0,0]

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

    def speech_bubble(self, title, text, fg_col, bg_col):
        # show a speak-bubble above the character with the text in it
        new_text = str(text)
        self.text.append(new_text)
        size = self.world.code_font.size(new_text)
        if size[X] > self.text_size[X]:
            self.text_size[X] = size[X]
        if len(self.text) < self.MAX_TEXT_LINES:
            self.text_size[Y] += size[Y]
        bubble_rect = pygame.Rect((0, 0),
                                  (self.text_size[X] + self.BUBBLE_MARGIN * 2,
                                   self.text_size[Y] + self.BUBBLE_MARGIN * 2)
                                  )
        self.bubble = pygame.Surface(bubble_rect.size)
        # fill with red to use as the transparency key
        self.bubble.fill((255,0,0))
        self.bubble.set_colorkey((255,0,0))
        # create a rectangle with clipped corners for the speech bubble
        # (rounded corners aren't available until pygame 2.0)
        w = bubble_rect.width
        h = bubble_rect.height
        m = self.BUBBLE_MARGIN
        pygame.draw.polygon(self.bubble, bg_col,
                            ((m , 0)   , (w - m, 0),
                             (w, m)    , (w, h - m),
                             (w - m, h), (m, h),
                             (0, h - m), (0, m)
                            )
                           )
        # draw the lines working upwards from the most recent,
        # until the bubble is full
        output_line = len(self.text) - 1
        line_y_pos = h - m - size[Y]
        color = fg_col
        while line_y_pos >= m and output_line >= 0:
            line = self.world.code_font.render(self.text[output_line],
                                               True, color)
            self.bubble.blit(line, (m, line_y_pos))
            output_line -= 1
            line_y_pos -= size[Y]
        self.speaking = True

    def say(self, *t):
        # show the message t in a speak-bubble above the character
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            print(*t, end='')  # TODO use a different way of suppressing ugly chars for carriage returns, that allows the user programs to still us the end= keyword
            speech = f.getvalue()
        self.speech_bubble("BIT says:", speech,
                           self.world.editor.get_fg_color(),
                           self.world.editor.get_bg_color())

    def syntax_error(self, msg):
        # show the error in a speak-bubble above the character
        self.speech_bubble("Syntax error!", msg,
                           (0,0,0),
                           (254,0,0))  # red, but not 255 because that's the alpha

#######################################################

class World:
    def __init__(self):
        print('Started.')
        # load scenery layers
        self.scenery = scenery.Scenery('Day', 'Desert')
        self.true_scroll = {'x': 0.0, 'y': 0.0}
        # location of the game area on the window
        # used to scroll the game area out of the way of the code editor
        self.game_origin = [0, 0]

        # load character sprites
        self.player = Character(self, 'character.png')
        self.dog = Character(self, 'dog basic.png', run_speed=2)
        self.player.location = {'x': 150, 'y': 170 - 32 - 2}
        self.dog.location = {'x': self.player.location['x'] + 50,
                        'y': self.player.location['y']}
        self.debug_mode = False

        # intialise the python interpreter
        if pygame.font.get_init() is False:
            pygame.font.init()
        if pygame.scrap.get_init() is False:
            pygame.scrap.init()
        self.code_font = pygame.font.SysFont("dejavusansmono", 18)
        self.program = interpreter.VirtualMachine(self)
        self.editor = editor.Editor(screen, 300, self.code_font, self.program)

        self.game_running = True
        self.frame_draw_time = 1

    def update(self):
        '''update all the game world stuff'''''

        frame_start_time = time.time_ns()  # used to calculate fps

        # track the camera with the player, but with a bit of lag
        self.true_scroll['x'] += (self.player.location['x']
                             - self.true_scroll['x'] - PLAYER_X_OFFSET) / 16
        if self.true_scroll['x'] < 0:
            # can't scroll past the start of the world
            self.true_scroll['x'] = 0
        self.true_scroll['y'] += (self.player.location['y']
                             - self.true_scroll['y'] - PLAYER_Y_OFFSET) / 16
        scroll = {'x': int(self.true_scroll['x']),
                  'y': int(self.true_scroll['y'])}

        # render the background
        self.scenery.draw_background(display, scroll)

        # move and render the player sprite
        self.player.update(display, scroll)

        # move and render the dog
        self.dog.update(display, scroll)
        # dog follows the player
        if self.dog.location['x'] > self.player.location['x'] + 30:
            self.dog.move_left()
        elif self.dog.location['x'] < self.player.location['x'] - 30:
            self.dog.move_right()
        else:
            self.dog.stop_moving()

        # draw the foreground scenery on top of the characters
        self.scenery.draw_foreground(display, scroll)

        # allocate some cpu time to the in-game interpreter running player's code
        if self.program.is_running():
            self.program.update()

        # draw and update the editor, if necessary
        if self.editor.is_active():
            self.editor.update()
        else:
            # only handle keystrokes for game control if the editor isn't open
            pressed = pygame.key.get_pressed()
            if pressed[K_a]:
                self.player.move_left()
            elif pressed[K_d]: # or True:  # DEBUG ensure the scene is always moving to check multitasking works

                self.player.move_right()
            else:
                self.player.stop_moving()

            if pressed[K_SPACE]:
                self.player.jump()

            if pressed[K_ESCAPE]:
                # only show editor when it is completely hidden
                # this prevents it immediately reshowing after hiding
                if self.game_origin[Y] == 0:
                    self.editor.show()

            # DEBUG stats
            if pressed[K_f]:
                # display fps stats
                self.debug_frame_counter = 0
                self.debug_mode = True

            if pressed[K_g]:
                # turn off fps stats
                self.debug_mode = False

            # process all other events to clear the queue
            for event in pygame.event.get():
                if event.type == QUIT:
                    game_running = False

        if self.debug_mode:
            self.debug_frame_counter += 1
            if self.debug_frame_counter > 60:
                self.debug_frame_counter = 0
                print(
                    'frame draw:{0}ms fps:{1} render budget left:{2}ms'.format(
                        self.frame_draw_time / 1000000,
                        int(1000000000 / self.frame_draw_time),
                        int((1000000000 - 60
                             * self.frame_draw_time) / 1000000)))

        # scroll the editor in and out of view as required
        if self.editor.is_active():
            if self.game_origin[Y] > -self.editor.height:
                self.game_origin[Y] -= EDITOR_POPUP_SPEED
            self.editor.draw()
        elif self.game_origin[Y] < 0:
            self.game_origin[Y] += EDITOR_POPUP_SPEED

        # scale the rendering area to the actual game window
        screen.blit(pygame.transform.scale(display, WINDOW_SIZE),
                    self.game_origin)
        # blit the editor underneath the game surface
        editor_position = (self.game_origin[X],
                           self.game_origin[Y] + WINDOW_SIZE[Y])
        screen.blit(self.editor.surface, editor_position)

        # overlay all text at the native resolution to avoid scaling ugliness
        if self.dog.speaking:
            # position the tip of the speak bubble at the middle
            # of the top edge of the sprite box
            position = ((self.dog.location['x'] - scroll['x'] + 16)
                        * SCALING_FACTOR + self.game_origin[X],
                        (self.dog.location['y'] - scroll['y'])
                        * SCALING_FACTOR  + self.game_origin[Y]
                        - self.dog.text_size[Y])
            screen.blit(self.dog.bubble, position)

        pygame.display.update()  # actually display

        self.frame_draw_time = time.time_ns() - frame_start_time
        clock.tick(60)  # lock the framerate to 60fps

################################
# create the world
world = World()

# set it in motion
while world.game_running:
    world.update()

# tidy up and quit
pygame.quit()
