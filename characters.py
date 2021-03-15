""" movement and animation for all the player and npc sprites """
import math
import random
from math import copysign

import pygame
import contextlib
import io
from constants import *
import sprite_sheet
from particles import Jet
from console_messages import console_msg
from text_panel import TextPanel


class Character:
    """Base class for player and NPC sprites
    can move in all 4 directions and is not subject to gravity"""
    #ANIMATION_LENGTH = 8  # number of frames per movement
    STANDING_FRAME = 7  # the run frame used when standing still

    def __init__(self, world, name,
                 sprite_file="", size=(BLOCK_SIZE, BLOCK_SIZE)):
        self.world = world  # link back to the world game state
        self.name = name  # for debugging only, right now
        self.size = size
        if sprite_file != "":
            self.load_sprites(sprite_file)
        else:
            # create placeholder sprites
            self.move_right_frames = [sprite_sheet.default_image()]
            self.frame_count = 1
            self.move_left_frames = [sprite_sheet.default_image()]
            self.standing_left_frame = sprite_sheet.default_image()
            self.standing_right_frame = sprite_sheet.default_image()
            self.move_vertical_left_frames = [sprite_sheet.default_image()]
            self.move_vertical_right_frames = [sprite_sheet.default_image()]
        self.facing_right = True
        self.moving_right = False;
        self.moving_left = False;
        self.moving_up = False;
        self.moving_down = False;
        self.location = pygame.Rect((0, 0), self.size)
        self.frame_number = 0
        self.run_speed = 2  # default run speed
        self.x_speed = self.run_speed
        self.y_speed = self.run_speed  # x & y speeds default to run speed
        self.subject_to_gravity = False
        self.y_momentum = 0.0
        # TODO different collider heights for different characters
        self.collider = pygame.Rect(0, 0, size[X], size[Y])
        self.collisions = {'left': None,
                           'right': None,
                           'up': None,
                           'down': None,
                           }
        self.collidable = False
        self.collision_test = None
        self.trigger_test = None

    def set_collision_test(self, collision_tester):
        # inject the routine that handles collision checking with the block map
        self.collision_test = collision_tester

    def set_trigger_test(self, trigger_tester):
        # inject the routine that handles trigger checking (collisions) with the block map
        self.trigger_test = trigger_tester

    def load_sprites(self, sprite_file):
        # load character animation frames
        self.character_sheet = \
            sprite_sheet.SpriteSheet(sprite_file)
        self.move_right_frames = self.character_sheet.load_strip(
            pygame.Rect((0, 0), self.size), 8, -1)
        self.frame_count = len(self.move_right_frames)
        self.move_left_frames = [pygame.transform.flip(sprite, True, False)
                                 for sprite in self.move_right_frames]
        self.standing_left_frame = self.move_left_frames[self.STANDING_FRAME]
        self.standing_right_frame = self.move_right_frames[self.STANDING_FRAME]
        self.move_vertical_left_frames = [self.standing_left_frame]\
                                         * self.frame_count
        self.move_vertical_right_frames = [self.standing_right_frame]\
                                          * self.frame_count

    def update(self, surface, scroll):
        """movement system & collisions based on daFluffyPotato
        (https://www.youtube.com/watch?v=abH2MSBdnWc)"""

        if self.subject_to_gravity:
            self.y_momentum += GRAVITY
            if self.y_momentum > 3:
                self.y_momentum = 3
            movement = [0, self.y_momentum]
        else:
            movement = [0, 0]
        if self.moving_right:
            movement[X] += self.x_speed
            self.facing_right = True
        if self.moving_left:
            movement[X] -= self.x_speed
            self.facing_right = False
        if self.moving_up:
            movement[Y] -= self.y_speed
        if self.moving_down:
            movement[Y] += self.y_speed

        if self.collidable:
            # activate any triggers we have collided with or otherwise set off
            self.trigger_test(self)

        # perform collision detection and update position
        self.location, self.collisions = self.move(self.location, movement)

        # figure out the correct animation frame to show, based on movement
        f = int(self.frame_number) % self.frame_count
        self.frame_number = self.frame_number + .25
        if self.moving_right:
            frame = self.move_right_frames[f]
        elif self.moving_left:
            frame = self.move_left_frames[f]
        elif self.moving_up or self.moving_down:
            if self.facing_right:
                frame = self.move_vertical_right_frames[f]
            else:
                frame = self.move_vertical_left_frames[f]
        else:  # standing
            if self.facing_right:
                frame = self.standing_right_frame
            else:
                frame = self.standing_left_frame

        # cancel movement if we have collided in that direction
        if self.collisions['up']:
            self.moving_up = False;
        if self.collisions['down']:
            self.moving_down = False;
            self.y_momentum = 0.0
        if self.collisions['left']:
            self.moving_left = False;
        if self.collisions['right']:
            self.moving_right = False;

        # also cancel movement when we reach an integer grid position
        if self.location.x % BLOCK_SIZE < self.run_speed:
            self.moving_right = False;
            self.moving_left = False;
            self.location.x = round(self.location.x / BLOCK_SIZE) * BLOCK_SIZE
        if self.location.bottom % BLOCK_SIZE < self.run_speed:
            self.moving_up = False;
            self.moving_down = False;
            self.location.bottom = (round(self.location.bottom / BLOCK_SIZE)
                                    * BLOCK_SIZE)

        surface.blit(frame, (self.location.x - scroll[X],
                         self.location.y - scroll[Y]))

    def move_left(self):
        # request the character to begin moving
        self.moving_left = True
        self.moving_right = False

    def move_right(self):
        # request the character to begin moving
        self.moving_left = False
        self.moving_right = True

    def move(self, rectangle, movement):
        """ Move in the x, check for collisions, then move in the y and
        check again. This helps to avoid glitches at corner collisions."""

        collision_directions = {'up': False,
                                'down': False,
                                'left': False,
                                'right': False,
                                }

        # check if moving blocks will hit the character
        # first in the X direction
        hit_list = self.collision_test(rectangle)
        for block in hit_list:
            if block.movement[X] < 0 and rectangle.right > block.left():
                rectangle.right = block.left()
                collision_directions['right'] = True
            elif block.movement[X] > 0 and rectangle.left < block.right():
                rectangle.left = block.right()+1  # TODO this is a kludge to avoid weird collision on leftward moving blocks
                collision_directions['left'] = True

        # then the Y direction
        hit_list = self.collision_test(rectangle)
        for block in hit_list:
            if block.movement[Y] < 0 and rectangle.bottom > block.top():
                rectangle.bottom = block.top()
                collision_directions['down'] = True
            elif block.movement[Y] > 0 and rectangle.top < block.bottom():
                rectangle.top = block.bottom()
                collision_directions['up'] = True

        # now check if the character's own movement causes a collision
        rectangle.x += movement[X]
        hit_list = self.collision_test(rectangle)
        for block in hit_list:
            if movement[X] > 0 and rectangle.right > block.left():
                rectangle.right = block.left()
                collision_directions['right'] = True
            elif movement[X] < 0 and rectangle.left < block.right():
                rectangle.left = block.right()
                collision_directions['left'] = True

        rectangle.y += movement[Y]
        hit_list = self.collision_test(rectangle)
        for block in hit_list:
            if movement[Y] > 0 and rectangle.bottom > block.top():
                rectangle.bottom = block.top()
                collision_directions['down'] = True
            elif movement[Y] < 0 and rectangle.top < block.bottom():
                rectangle.top = block.bottom()
                collision_directions['up'] = True

        return rectangle, collision_directions

    def set_position(self, grid_position):
        # place the character at the grid coords
        self.location.x = grid_position[X] * BLOCK_SIZE
        self.location.y = ((grid_position[Y] + 1) * BLOCK_SIZE
                           - self.collider.height)
        self.position = [float(self.location.x),
                         float(self.location.y)]

    def nearest_grid_position(self):
        # returns the grid coords, rounded to the nearest integer
        return [round(self.position[X] / BLOCK_SIZE),
                round(self.position[Y] / BLOCK_SIZE),
               ]

    def gridX(self):
        # current location in terms of block coords, rather than pixels
        return round(self.location[X] / BLOCK_SIZE)

    def gridY(self):
        return round(self.location[Y] / BLOCK_SIZE)


class Person(Character):
    """ can only run left and right, and is subject to gravity """
    def __init__(self, world, name, sprite_file, size):
        super().__init__(world, name, sprite_file, size)
        self.subject_to_gravity = True
        self.collidable = True
        self.set_trigger_test(world.blocks.trigger_test)
        self.set_collision_test(world.blocks.collision_test)

class Ghostly(Character):
    """ doesn't interact with blocks or triggers
    This is used for decorative background sprites, like birds or leaves"""
    def __init__(self, world, name, sprite_file, size):
        super().__init__(world, name, sprite_file, size)
        self.subject_to_gravity = False
        self.collidable = False

    def move(self, rectangle, movement):
        """ Move in the x, y, without any collision detection """
        collision_directions = {'up': False,
                                'down': False,
                                'left': False,
                                'right': False,
                                }
        rectangle.x += movement[X]
        rectangle.y += movement[Y]
        return rectangle, collision_directions


class Dog(Character):
    """ Not affected by gravity,
        Has a rocket animation when in the air
        Can display speech bubbles"""
    def __init__(self, world, name, sprite_file, size):
        super().__init__(world, name, sprite_file, size)
        self.collidable = True
        self.set_trigger_test(world.blocks.trigger_test)
        self.set_collision_test(world.blocks.collision_test)
        self.busy = False  # used to block code execution during movement
        self.speaking = False
        self.speech_bubble = None
        #self.speech = None
        #self.speech_bubble_fg = (0, 0, 0)
        #self.speech_bubble_bg = (0, 0, 0)
        #self.speech_bubble_size = [0, 0]
        #self.text = []
        #self.text_size = [0, 0]
        self.jets = []  # the particle streams that appear when flying
        # create 2 jets, 1 for each leg
        # the origin coordinates are just zero,
        # since they will be set each frame
        for j in range(2):
            self.jets.append(Jet(self.world,  # link back to the game world
                                 (0, 0),  # dummy start position
                                 (0, 1),  # initial velocity vector
                                 ))
        self.wobble = []  # random drift when hovering
        rx = 4
        ry = 2
        for i in range(32):
            x = i / 2 - 8  # rx * math.cos(i*2*math.pi/32)
            y = ry * math.sin(i * 2 * math.pi / 32) - ry - 2
            self.wobble.append((x, y))
        for i in range(31, -1, -1):
            x = i / 2 - 8  # rx * math.cos(i*2*math.pi/32)
            y = -ry * math.sin(i * 2 * math.pi / 32) - ry - 2
            self.wobble.append((0, 0))
            # self.wobble.append((x, y))
        self.wobble_counter = 0
        self.take_off_animation = []  # take off animation sequence
        for i in range(32):
            self.take_off_animation.append((0, 0))
            # self.take_off_animation.append((0, -8*i/32))

    def set_position(self, grid_position):
        super().set_position(grid_position)
        self.destination = [grid_position[X], grid_position[Y]]

    def move_right(self, distance):
        self.destination[X] = self.gridX() + distance
#        self.moving_right = True
#        self.moving_left = False

    def move_by_amount(self, distance):
        self.destination[X] = self.gridX() + distance[X]
        self.destination[Y] = self.gridY() + distance[Y]

    def say(self, *t):
        # show the message t in a speak-bubble above the character
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            print(*t, end='')  # TODO use a different way of suppressing ugly chars for carriage returns, that allows the user programs to still use the end= keyword
            speech = f.getvalue()
        self.create_speech_bubble(speech,
                                 self.world.editor.get_fg_color(),
                                 self.world.editor.get_bg_color())

    def error(self, msg, type="Syntax error!"):
        # show the error in a speak-bubble above the character
        self.create_speech_bubble(type + msg,
                                  (0, 0, 0),
                                  (254, 0, 0))  # red, but not 255 because that's the alpha

    def input(self, msg=''):
        # get input from the user in a separate editor window
        self.world.input.activate('input:' + msg)
        while self.world.input.is_active():
            self.world.update(self)
        result = self.world.input.convert_to_lines()[0]
        console_msg("input:" + str(result), 8)
        return result

    def clear_speech_bubble(self):
        if self.speech_bubble != None:
            self.speech_bubble.clear()

    # def old_clear_speech_bubble(self):
    #     self.text = []
    #     self.text_size = [0,0]
    #     self.speaking = False

    def create_speech_bubble(self, text, fg_col, bg_col):
        # show a speak-bubble above the character with the text in it
        self.speech_bubble = TextPanel(text, fg_col, bg_col, self.world.code_font)
        self.speaking = True

    # def old_create_speech_bubble(self, text, fg_col, bg_col):
    #     # show a speak-bubble above the character with the text in it
    #     new_text = str(text)
    #     # make sure speech bubble has at least 1 character width
    #     # non-printing chars or empty strings make the bubble look weird
    #     if (self.world.code_font.size(new_text)[X]
    #         < self.world.code_font.size(" ")[X]):
    #         new_text = new_text + " "
    #     self.text.append(new_text)
    #     self.speech_bubble_size = self.world.code_font.size(new_text)
    #     if self.speech_bubble_size[X] > self.text_size[X]:
    #         self.text_size[X] = self.speech_bubble_size[X]
    #     if len(self.text) <= MAX_BUBBLE_TEXT_LINES:
    #         self.text_size[Y] += self.speech_bubble_size[Y]
    #     self.speech_bubble_fg = fg_col
    #     self.speech_bubble_bg = bg_col
    #     self.speech_expires = pygame.time.get_ticks() + SPEECH_EXPIRY_TIME
    #     self.speaking = True

    def get_speech_bubble(self, surface):
        return self.speech_bubble.rendered(surface)

    def speech_position(self):
        # position the tip of the speak bubble at the middle
        # of the top edge of the sprite box
        # the -8 is a fudge factor to put the speech bubble just above the sprite
        position = [self.location.x, self.location.y - self.speech_bubble.get_height() / SCALING_FACTOR - 8]
        return position

    # def old_draw_speech_bubble(self, surface):
    #     bubble_rect = pygame.Rect((0, 0), (
    #         (self.text_size[X]
    #          + TEXT_MARGIN * 2
    #          + BALLOON_THICKNESS * 2
    #          + BUBBLE_MARGIN),
    #         (self.text_size[Y]
    #          + TEXT_MARGIN * 2
    #          + BALLOON_THICKNESS * 2
    #          + BUBBLE_MARGIN * 2)
    #         ))
    #     self.bubble = pygame.Surface(bubble_rect.size)
    #     # fill with red to use as the transparency key
    #     self.bubble.fill((255, 0, 0))
    #     self.bubble.set_colorkey((255, 0, 0))
    #     # create a rectangle with clipped corners for the speech bubble
    #     # (rounded corners aren't available until pygame 2.0)
    #     bubble_points = (
    #         (BALLOON_THICKNESS, bubble_rect.size[Y] - BALLOON_THICKNESS),  # A
    #         (BUBBLE_MARGIN + BALLOON_THICKNESS,
    #          bubble_rect.size[Y] - BUBBLE_MARGIN*2),                       # B
    #         (BUBBLE_MARGIN + BALLOON_THICKNESS,
    #          BUBBLE_MARGIN),                                               # C
    #         (BUBBLE_MARGIN*2, 0),                                          # D
    #         (bubble_rect.size[X] - BUBBLE_MARGIN, 0),                      # E
    #         (bubble_rect.size[X] - BALLOON_THICKNESS,
    #          BUBBLE_MARGIN),                                               # F
    #         (bubble_rect.size[X] - BALLOON_THICKNESS,
    #          bubble_rect.size[Y] - BUBBLE_MARGIN*3),                       # G
    #         (bubble_rect.size[X] - BUBBLE_MARGIN,
    #          bubble_rect.size[Y] - BUBBLE_MARGIN*2),                       # H
    #         (BUBBLE_MARGIN*3, bubble_rect.size[Y] - BUBBLE_MARGIN*2),      # I
    #     )
    #     pygame.draw.polygon(self.bubble,
    #                         self.speech_bubble_bg,
    #                         bubble_points,
    #                         0)
    #     pygame.draw.polygon(self.bubble,
    #                         self.speech_bubble_fg,
    #                         bubble_points,
    #                         BALLOON_THICKNESS)
    #     # draw the lines of text, working upwards from the most recent,
    #     # until the bubble is full
    #     output_line = len(self.text) - 1
    #     line_y_pos = (bubble_rect.size[Y]
    #                   - BUBBLE_MARGIN * 2
    #                   - TEXT_MARGIN
    #                   - self.speech_bubble_size[Y])
    #     color = self.speech_bubble_fg
    #     while line_y_pos >= TEXT_MARGIN and output_line >= 0:
    #         line = self.world.code_font.render(self.text[output_line],
    #                                            True, color)
    #         line_x_pos = BUBBLE_MARGIN + TEXT_MARGIN + BALLOON_THICKNESS
    #         self.bubble.blit(line, (line_x_pos, line_y_pos))
    #         output_line -= 1
    #         line_y_pos -= self.speech_bubble_size[Y]

    def update_speech_bubble(self):
        pass

    def update(self, surface, scroll):
        if self.destination[X] > self.gridX():
            self.moving_right = True
        elif self.destination[X] < self.gridX():
            self.moving_left = True
        elif self.destination[Y] > self.gridY():
            self.moving_down = True
        elif self.destination[Y] < self.gridY():
            self.moving_up = True
        super().update(surface, scroll)
        if (self.moving_up or
                self.moving_down or
                self.moving_right or
                self.moving_left):
            self.busy = True  # blocks code execution until the move completes
        else:
            self.busy = False
        wobble_factor = [0,0]
        # turn on the jets if there isn't a solid block underneath
        if self.world.blocks.get_block(
                self.world.blocks.midground_blocks,
                self.gridX(), self.gridY()+1) is None:
           self.jets[0].turn_on()
           self.jets[1].turn_on()
        else:
            self.jets[0].turn_off()
            self.jets[1].turn_off()

        if self.jets[0].is_active():
            # the wobble animation for flight/hovering is turned off for now
            # to re-enable it, I need to find a neat way to adjust the
            # position of the sprite just before it is blitted
            # this will probably involve moving the blit operation from
            # Character.update() to a separate method, and then overriding it.
            # wobble_factor= self.wobble[self.wobble_counter]
            self.wobble_counter = (self.wobble_counter +1) % len(self.wobble)
            self.jets[0].nozzle[X] = self.location.left + wobble_factor[X] + 4
            self.jets[0].nozzle[Y] = self.location.bottom + wobble_factor[Y] + 2
            self.jets[0].update(surface, scroll)
            self.jets[1].nozzle[X] = self.location.right + wobble_factor[X] - 4
            self.jets[1].nozzle[Y] = self.location.bottom + wobble_factor[Y] + 2
            self.jets[1].update(surface, scroll)


