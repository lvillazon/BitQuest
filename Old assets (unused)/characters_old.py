"""
BACKUP taken 15/11/20 when I began refactoring the character class
movement and animation for all the player and npc sprites """
import math
import random
from math import copysign

import pygame
import contextlib
import io
from constants import *
import sprite_sheet
from particles import Jet
from speech_bubble import SpeechBubble


class Character:
    ANIMATION_LENGTH = 8  # number of frames per movement
    STANDING_FRAME = 7  # the run frame used when standing still

    def __init__(self, world, name, sprite_file, size, run_speed=2):
        self.world = world  # link back to the world game state
        self.name = name  # for debugging only, right now
        # load character animation frames
        self.character_sheet = \
            sprite_sheet.SpriteSheet('assets/' + sprite_file)
        self.run_right_frames = self.character_sheet.load_strip(
            pygame.Rect(0, 0, size[X], size[Y]), 8, -1)

        # self.run_right_frames = self.character_sheet.load_block_of_8(0, 0, -1)
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
        self.flying = False
        self.take_off = False
        self.state = STANDING
        self.facing_right = True
        self.momentum = [0.0, 0.0]
        # location is the rectangle used to draw the sprite
        # position is a float version of the x,y pixel coords
        # used to provide smooth movement
        self.position = [0.0, 0.0]
        self.location = pygame.Rect(0, 0, size[X], size[Y])
        # TODO different collider heights for different characters
        self.collider = pygame.Rect(0, 0, size[X], size[Y])
        self.ground_proximity = \
            pygame.Rect(0, 0, size[X], size[Y])
        self.frame_number = 0
        self.frame_count = len(self.run_right_frames)
        self.jumping = False
        self.run_speed = run_speed
        self.speaking = False
        self.speech = None
        self.speech_bubble_fg = (0, 0, 0)
        self.speech_bubble_bg = (0, 0, 0)
        self.speech_bubble_size = [0, 0]
        self.text = []
        self.text_size = [0, 0]
        self.jets = []  # the particle streams that appear when flying
        # create 2 jets, 1 for each leg
        # the origin coordinates are just zero,
        # since they will be set each frame
        for j in range(2):
            self.jets.append(Jet(self.world,  # link back to the game world
                                 (0, 0),      # dummy start position
                                 (0, 1),      # initial velocity vector
                                 ))
        self.wobble = []  # random drift when hovering
        rx = 4
        ry = 2
        for i in range(32):
            x = i/2 - 8 #rx * math.cos(i*2*math.pi/32)
            y = ry * math.sin(i*2*math.pi/32) - ry - 2
            self.wobble.append((x, y))
        for i in range(31,-1,-1):
            x = i/2 - 8 #rx * math.cos(i*2*math.pi/32)
            y = -ry * math.sin(i*2*math.pi/32) - ry - 2
            self.wobble.append((0,0))
            #self.wobble.append((x, y))
        self.wobble_counter = 0
        self.take_off_animation = []  # take off animation sequence
        for i in range(32):
            self.take_off_animation.append((0, 0))
            #self.take_off_animation.append((0, -8*i/32))

    def set_position(self, grid_position):
        # place the character at the grid coords
        self.location.x = grid_position[X] * BLOCK_SIZE
        self.location.y = grid_position[Y] * BLOCK_SIZE
        self.position = [float(self.location.x),
                         float(self.location.y)]

    def nearest_grid_position(self):
        # returns the grid coords, rounded to the nearest integer
        return [round(self.position[X] / BLOCK_SIZE),
                round(self.position[Y] / BLOCK_SIZE),
               ]

    def update(self, surface):
        f = int(self.frame_number) % self.frame_count
        self.frame_number = self.frame_number + .25
        wobble_factor = [0.0, 0.0]
        movement = [0, self.momentum[Y]]
        if self.state == MOVING or self.state == FLYING:  # WAS self.moving:
            if self.momentum[X] != 0:
                # reduce the horizontal momentum by run_speed
                # so that it reaches 0 as we arrive at the correct point
                direction = copysign(self.run_speed, self.momentum[X])
                movement[X] = direction
                self.momentum[X] = self.momentum[X] - direction

            if self.momentum[X] == 0:
                if self.state == MOVING:
                    # we don't check the Y momentum, because the character always has some due to gravity
                    self.state = STANDING
                if self.state == FLYING and self.momentum[Y] == 0:
                    # flying character are exempt from gravity so we can check for hovering using Y momentum
                    self.state = HOVERING
                # WAS self.moving = False

        if self.state == TAKING_OFF:  # WAS self.take_off:
            movement[Y] = 0

        if self.state == FLYING:  # WAS self.flying:
            if self.momentum[Y] != 0:
                # use the direction of the momentum to set the movement
                direction = copysign(
                    int(self.run_speed * self.jets[0].get_power()),
                    self.momentum[Y]
                )
                movement[Y] = direction
                self.momentum[Y] = self.momentum[Y] - direction

        # choose the correct animation frame, based on movement type
        # if self.state == JUMPING: # currently unused -  WAS self.jumping:
        #     if self.facing_right:
        #         frame = self.jump_right_frames[f]
        #     else:
        #         frame = self.jump_left_frames[f]
        #     if self.frame_number == self.ANIMATION_LENGTH:
        #         self.jumping = False
        if self.state == MOVING:  # WAS self.moving:
            if self.facing_right:
                frame = self.run_right_frames[f]
            else:
                frame = self.run_left_frames[f]
        else:  # standing, flying, taking off, landing or hovering
            if self.facing_right:
                # standing still is frame 7 on the animation cycle
                frame = self.run_right_frames[self.STANDING_FRAME]
            else:
                frame = self.run_left_frames[self.STANDING_FRAME]

        # activate any triggers we have collided with or otherwise set off
        self.world.blocks.trigger_test(self.collider, movement)

        # check collisions with the world blocks - pillars etc
        self.collider.centerx = self.location.centerx + movement[X]
        # the collider extends 1 pixel below the character, so that they
        # stand neatly on the ground surface
        self.collider.bottom = self.location.bottom + movement[Y] + 1
        blocked = self.world.blocks.collision_test(self.collider, movement)
        #if blocked['up']:
            # the player cannot move up by themself
            # so being blocked upwards can only happen if a block carries them
            # which should result in a SQUISH
            # the dog can get blocked when flying though
            # so we'll need to check for this eventually
        if blocked['left']:
            movement[X] = blocked['left'].movement[X]
            self.momentum[X] = 0
            print("blocked left at", self.gridX())
        if blocked['right']:
            movement[X] = blocked['right'].movement[X]
            self.momentum[X] = 0
            print("blocked right at", self.gridX())
        if blocked['down']:
            movement[Y] = blocked['down'].movement[Y]
            self.momentum[Y] = blocked['down'].movement[Y]
            #self.location.bottom = blocked['down'].top()
            #self.position[Y] = self.location.y  # resync the float and int versions

        if self.name == "player":
            self.momentum[Y] += GRAVITY  # constant downward pull
        else:
            # BIT is not subject to gravity, since he can fly
            # check for ground underneath so we know when he has landed
            self.ground_proximity.centerx = self.location.centerx + movement[X]
            self.ground_proximity.bottom = (self.location.bottom
                                            + movement[Y]
                                            + BLOCK_SIZE / 2)

            blocked = self.world.blocks.collision_test(self.ground_proximity,
                                                       movement)
            # if there is a tile directly underneath and we aren't moving up
            # turn off the jets
            # if there is no tile underneath, turn on the jets
            #if self.gridX() == 61:
            #    self.flying = True
            #    self.jets[0].turn_on()
            #    self.jets[1].turn_on()

            if blocked['down'] and self.momentum[Y] >= 0:
                if self.state == FLYING or self.state == TAKING_OFF: # WAS self.flying:
                    print("land")
                    # allow movement to finish the current grid square but then stop
#                    self.momentum[Y] = 0
                    self.state = MOVING  # WAS self.flying = False
                    self.jets[0].turn_off()
                    self.jets[1].turn_off()
            elif not blocked['down'] or self.momentum[Y] < 0:
                if self.state == STANDING or self.state == MOVING: # WAS not self.flying and not self.take_off:
                    print("take off")
                    self.state = FLYING
                    # self.state = TAKING_OFF  # WAS self.flying = True
                    self.jets[0].turn_on()
                    self.jets[1].turn_on()

            # PROOF OF CONCEPT - this should be integrated with the hover wobble and landing animations
            if self.state == TAKING_OFF:  # WAS self.take_off:
                wobble_factor= self.take_off_animation[self.wobble_counter]
                self.wobble_counter = self.wobble_counter + 1
                if self.wobble_counter >= len(self.take_off_animation):
                    self.wobble_counter = 0
                    self.state = FLYING
                    # WAS self.take_off = False
                    # WAS self.flying = True

            # when hovering, add some random wobble to the position
            # to make the flying look more convincing
            # TODO move this to the other if FLYING block to set/unset the HOVERING state
            if self.flying and self.momentum == [0,0]:
                wobble_factor= self.wobble[self.wobble_counter]
                self.wobble_counter = (self.wobble_counter + 1) % len(self.wobble)

        self.position[X] += movement[X]
        self.location.x = self.position[X]
        if self.location.x < 0:  # can't move past start of the world
            self.location.x = 0

        # position keeps track of the decimal portion
        # so we don't get weird int conversion glitches
        self.position[Y] += movement[Y]
        self.location.y = self.position[Y]

        # draw the sprite at the new location
        surface.blit(frame, (self.location.x
                             + wobble_factor[X] - self.world.scroll[X],
                             self.location.y
                             + wobble_factor[Y] - self.world.scroll[Y]))
        # update the jets if they are running
        if self.jets[0].is_active():
            self.jets[0].nozzle[X] = self.location.left + wobble_factor[X] + 4
            self.jets[0].nozzle[Y] = self.location.bottom + wobble_factor[Y] + 2
            self.jets[0].update(surface, self.world.scroll)
        if self.jets[1].is_active():
            self.jets[1].nozzle[X] = self.location.right + wobble_factor[X] - 4
            self.jets[1].nozzle[Y] = self.location.bottom + wobble_factor[Y] + 2
            self.jets[1].update(surface, self.world.scroll)

        # remove text from the speech bubble if it has been there for too long
        if self.speaking and self.speech_expires < pygame.time.get_ticks():
            if len(self.text) > 1:
                self.text.pop(0)
                if len(self.text) < MAX_BUBBLE_TEXT_LINES:
                    self.speech_expires = (pygame.time.get_ticks()
                                            + SPEECH_EXPIRY_RATE)
                    self.text_size[Y] -= self.speech_bubble_size[Y]
            else:
                self.speaking = False

    def gridX(self):
        # current location in terms of block coords, rather than pixels
        return round(self.location[X] / BLOCK_SIZE)

    def gridY(self):
        return round(self.location[Y] / BLOCK_SIZE)

    def move_left(self, distance=1):
        # move a whole number of blocks to the left
        if self.momentum[X] == 0:  # wait until any previous move is complete
            self.facing_right = False
            self.momentum[X] = -distance * BLOCK_SIZE
            self.state = MOVING  # WAS self.moving = True

    def move_right(self, distance=1):
        # move a whole number of blocks to the right
        if self.momentum[X] == 0:  # wait until any previous move is complete
            self.facing_right = True
            self.momentum[X] = distance * BLOCK_SIZE
            self.state = MOVING  # WAS self.moving = True

    def move_up(self, distance=1):
        # move a whole number of blocks upwards
        if self.state != FLYING and self.state != HOVERING:  # take off 1st
            print("take off 2")
            self.state = TAKING_OFF  # WAS self.take_off = True
            self.wobble_counter = 0
#            self.flying = True
            self.jets[0].turn_on()
            self.jets[1].turn_on()
        else:
            self.state = FLYING  # to make sure we don't leave the state on hover
        if abs(self.momentum[Y]) < 1:  # wait until any previous move is complete
            self.momentum[Y] = distance * BLOCK_SIZE
            # WAS self.moving = True

    def move_down(self, distance=1):
        # move a whole number of blocks downwards
        if abs(self.momentum[Y]) < 1:  # wait until any previous move is complete
            self.momentum[Y] = distance * BLOCK_SIZE
            self.state = FLYING
            # WAS self.moving = True

    def jump(self):
        self.jumping = True
        self.frame_number = 2  # reset frame counter for the jump animation

    def stop_moving(self):
        self.moving = False

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

    def input(self, msg):
        # get input from the user in a separate editor window
        self.world.input.activate(msg)
        while self.world.input.is_active():
            self.world.update()
        result = self.world.input.convert_to_lines()[0]
        print("input:", result)
        return result

    def create_speech_bubble(self, text, fg_col, bg_col):
        # show a speak-bubble above the character with the text in it
        new_text = str(text)
        # make sure speech bubble has at least 1 character width
        # non-printing chars or empty strings make the bubble look weird
        if (self.world.code_font.size(new_text)[X]
            < self.world.code_font.size(" ")[X]):
            new_text = new_text + " "
        self.text.append(new_text)
        self.speech_bubble_size = self.world.code_font.size(new_text)
        if self.speech_bubble_size[X] > self.text_size[X]:
            self.text_size[X] = self.speech_bubble_size[X]
        if len(self.text) <= MAX_BUBBLE_TEXT_LINES:
            self.text_size[Y] += self.speech_bubble_size[Y]
        self.speech_bubble_fg = fg_col
        self.speech_bubble_bg = bg_col
        self.speech_expires = pygame.time.get_ticks() + SPEECH_EXPIRY_TIME
        self.speaking = True

    def draw_speech_bubble(self, surface):
        bubble_rect = pygame.Rect((0, 0), (
            (self.text_size[X]
             + TEXT_MARGIN * 2
             + BORDER_THICKNESS * 2
             + BUBBLE_MARGIN),
            (self.text_size[Y]
             + TEXT_MARGIN * 2
             + BORDER_THICKNESS * 2
             + BUBBLE_MARGIN * 2)
            ))
        self.bubble = pygame.Surface(bubble_rect.size)
        # fill with red to use as the transparency key
        self.bubble.fill((255, 0, 0))
        self.bubble.set_colorkey((255, 0, 0))
        # create a rectangle with clipped corners for the speech bubble
        # (rounded corners aren't available until pygame 2.0)
        bubble_points = (
            (BORDER_THICKNESS, bubble_rect.size[Y] - BORDER_THICKNESS),  # A
            (BUBBLE_MARGIN + BORDER_THICKNESS,
             bubble_rect.size[Y] - BUBBLE_MARGIN * 2),  # B
            (BUBBLE_MARGIN + BORDER_THICKNESS,
             BUBBLE_MARGIN),  # C
            (BUBBLE_MARGIN*2, 0),  # D
            (bubble_rect.size[X] - BUBBLE_MARGIN, 0),  # E
            (bubble_rect.size[X] - BORDER_THICKNESS,
             BUBBLE_MARGIN),  # F
            (bubble_rect.size[X] - BORDER_THICKNESS,
             bubble_rect.size[Y] - BUBBLE_MARGIN * 3),  # G
            (bubble_rect.size[X] - BUBBLE_MARGIN,
             bubble_rect.size[Y] - BUBBLE_MARGIN*2),  # H
            (BUBBLE_MARGIN*3, bubble_rect.size[Y] - BUBBLE_MARGIN*2),      # I
        )
        pygame.draw.polygon(self.bubble,
                            self.speech_bubble_bg,
                            bubble_points,
                            0)
        pygame.draw.polygon(self.bubble,
                            self.speech_bubble_fg,
                            bubble_points,
                            BORDER_THICKNESS)
        # draw the lines of text, working upwards from the most recent,
        # until the bubble is full
        output_line = len(self.text) - 1
        line_y_pos = (bubble_rect.size[Y]
                      - BUBBLE_MARGIN * 2
                      - TEXT_MARGIN
                      - self.speech_bubble_size[Y])
        color = self.speech_bubble_fg
        while line_y_pos >= TEXT_MARGIN and output_line >= 0:
            line = self.world.code_font.render(self.text[output_line],
                                               True, color)
            line_x_pos = BUBBLE_MARGIN + TEXT_MARGIN + BORDER_THICKNESS
            self.bubble.blit(line, (line_x_pos, line_y_pos))
            output_line -= 1
            line_y_pos -= self.speech_bubble_size[Y]

    def update_speech_bubble(self):
        pass


