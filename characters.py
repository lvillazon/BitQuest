""" movement and animation for all the player and npc sprites """
import math
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

    def __init__(self, world, name, sprite_file, run_speed=2):
        self.world = world  # link back to the world game state
        self.name = name  # for debugging only, right now
        # load character animation frames
        self.character_sheet = \
            sprite_sheet.SpriteSheet('assets/' + sprite_file)
        self.run_right_frames = self.character_sheet.load_strip(
            pygame.Rect(0, 0, CHARACTER_WIDTH, CHARACTER_HEIGHT), 8, -1)

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
        self.facing_right = True
        self.momentum = [0, 0]
        self.location = pygame.Rect(0, 0, CHARACTER_WIDTH, CHARACTER_HEIGHT)
        # TODO different collider heights for different characters
        self.collider = pygame.Rect(0, 0, COLLIDER_WIDTH, COLLIDER_HEIGHT)
        self.ground_proximity = \
            pygame.Rect(0, 0, COLLIDER_WIDTH, COLLIDER_HEIGHT)
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

    def update(self, surface, scroll):
        f = int(self.frame_number) % self.frame_count
        self.frame_number = self.frame_number + .25
        movement = [0, 0]
        movement[Y] += self.momentum[Y]
        if self.moving:
            if self.momentum[X] != 0:
                # use the direction of the momentum to set the movement
                direction = copysign(self.run_speed, self.momentum[X])
                movement[X] = direction
                self.momentum[X] = self.momentum[X] - direction

            if self.momentum[X] == 0:  # [0, 0]:
                self.moving = False

        if self.flying:
            if self.momentum[Y] != 0:
                # use the direction of the momentum to set the movement
                direction = copysign(
                    int(self.run_speed * self.jets[0].get_power()),
                    self.momentum[Y]
                )
                movement[Y] = direction
                self.momentum[Y] = self.momentum[Y] - direction
                if self.momentum[Y] == 0:
                    self.reason = "line 88"

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

        # check collisions with the world blocks - pillars etc
        self.collider.centerx = self.location.centerx + movement[X]
        self.collider.bottom = self.location.bottom + movement[Y]
        blocked = self.world.blocks.collision_test(self.collider,
                                                   movement, scroll)

        if blocked['up']:
            movement[Y] = 0.0
            self.momentum[Y] = 0.0
        if blocked['down'] and movement[Y] >0.0:
            movement[Y] = 0.0
            self.momentum[Y] = 0.0
        if blocked['left'] or blocked['right']:
            movement[X] = 0
            self.momentum[X] = 0

        self.location.x += movement[X]
        if self.location.x < 0:  # can't move past start of the world
            self.location.x = 0
        self.location.y += movement[Y]

        if not self.flying:
            self.momentum[Y] += GRAVITY  # constant downward pull
        else:
            # check for ground underneath
            self.ground_proximity.centerx = self.location.centerx + movement[X]
            self.ground_proximity.bottom = self.location.bottom + movement[Y] + BLOCK_SIZE / 2

            blocked = self.world.blocks.collision_test(self.ground_proximity,
                                                       movement, scroll)
            if blocked['down']:
                self.flying = False
                self.jets[0].turn_off()
                self.jets[1].turn_off()

        # draw the sprite at the new location
        surface.blit(frame, (self.location.x - scroll[X],
                             self.location.y - scroll[Y]))
        # update the jets if they are running
        if self.jets[0].is_active():
            self.jets[0].nozzle[X] = self.location.left + 4
            self.jets[0].nozzle[Y] = self.location.bottom + 2
            self.jets[0].update(surface, scroll)
        if self.jets[1].is_active():
            self.jets[1].nozzle[X] = self.location.right - 4
            self.jets[1].nozzle[Y] = self.location.bottom + 2
            self.jets[1].update(surface, scroll)

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
        return int(self.location[X] / BLOCK_SIZE)

    def gridY(self):
        return int(self.location[Y] / BLOCK_SIZE)

    def move_left(self, distance=1):
        # move a whole number of blocks to the left
        if self.momentum[X] == 0:  # wait until any previous move is complete
            self.facing_right = False
            self.momentum[X] = -distance * BLOCK_SIZE
            self.moving = True

    def move_right(self, distance=1):
        # move a whole number of blocks to the right
        if self.momentum[X] == 0:  # wait until any previous move is complete
            self.facing_right = True
            self.momentum[X] = distance * BLOCK_SIZE
            self.moving = True

    def move_up(self, distance=1):
        # move a whole number of blocks upwards
        if not self.flying:  # take off 1st
            self.flying = True
            self.jets[0].turn_on()
            self.jets[1].turn_on()
        if abs(self.momentum[Y]) < 1:  # wait until any previous move is complete
            self.momentum[Y] = distance * BLOCK_SIZE
            self.moving = True

    def move_down(self, distance=1):
        # move a whole number of blocks downwards
        if abs(self.momentum[Y]) < 1:  # wait until any previous move is complete
            self.momentum[Y] = distance * BLOCK_SIZE
            self.moving = True

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

    def error(self, msg):
        # show the error in a speak-bubble above the character
        self.create_speech_bubble("Syntax error!" + msg,
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
             + BALLOON_THICKNESS * 2
             + BUBBLE_MARGIN),
            (self.text_size[Y]
             + TEXT_MARGIN * 2
             + BALLOON_THICKNESS * 2
             + BUBBLE_MARGIN * 2)
            ))
        self.bubble = pygame.Surface(bubble_rect.size)
        # fill with red to use as the transparency key
        self.bubble.fill((255, 0, 0))
        self.bubble.set_colorkey((255, 0, 0))
        # create a rectangle with clipped corners for the speech bubble
        # (rounded corners aren't available until pygame 2.0)
        bubble_points = (
            (BALLOON_THICKNESS, bubble_rect.size[Y] - BALLOON_THICKNESS),  # A
            (BUBBLE_MARGIN + BALLOON_THICKNESS,
             bubble_rect.size[Y] - BUBBLE_MARGIN*2),                       # B
            (BUBBLE_MARGIN + BALLOON_THICKNESS,
             BUBBLE_MARGIN),                                               # C
            (BUBBLE_MARGIN*2, 0),                                          # D
            (bubble_rect.size[X] - BUBBLE_MARGIN, 0),                      # E
            (bubble_rect.size[X] - BALLOON_THICKNESS,
             BUBBLE_MARGIN),                                               # F
            (bubble_rect.size[X] - BALLOON_THICKNESS,
             bubble_rect.size[Y] - BUBBLE_MARGIN*3),                       # G
            (bubble_rect.size[X] - BUBBLE_MARGIN,
             bubble_rect.size[Y] - BUBBLE_MARGIN*2),                       # H
            (BUBBLE_MARGIN*3, bubble_rect.size[Y] - BUBBLE_MARGIN*2),      # I
        )
        pygame.draw.polygon(self.bubble,
                            self.speech_bubble_bg,
                            bubble_points,
                            0)
        pygame.draw.polygon(self.bubble,
                            self.speech_bubble_fg,
                            bubble_points,
                            BALLOON_THICKNESS)
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
            line_x_pos = BUBBLE_MARGIN + TEXT_MARGIN + BALLOON_THICKNESS
            self.bubble.blit(line, (line_x_pos, line_y_pos))
            output_line -= 1
            line_y_pos -= self.speech_bubble_size[Y]

    def update_speech_bubble(self):
        pass


