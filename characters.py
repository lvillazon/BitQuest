""" movement and animation for all the player and npc sprites """

import pygame
import contextlib
import io
from constants import *
import sprite_sheet

class Character:
    ANIMATION_LENGTH = 8  # number of frames per movement
    STANDING_FRAME = 7  # the run frame used when standing still
    BUBBLE_MARGIN = 10  # 10-pixel border around text in the speech bubble
    MAX_TEXT_LINES = 10  # 10 lines maximum in a speech bubble

    def __init__(self, world, name, sprite_file, run_speed=2):
        self.world = world  # link back to the world game state
        self.name = name  # for debugging only, right now
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
        self.momentum = [0,0]
        self.location = pygame.Rect(0, 0, CHARACTER_SIZE, CHARACTER_SIZE)
        self.collider = pygame.Rect(0,0, 24, 20)
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
        movement = [0,0]
        movement[Y] += self.momentum[Y]
        if self.moving:
            if self.facing_right:
                    movement[X] = self.run_speed
                    self.momentum[X] -= self.run_speed
                    if self.momentum[X] < 0:
                        self.momentum[X] = 0;
            else:
                if self.location.x > 0:  # can't move past start of the world
                    movement[X] = -self.run_speed
                    self.momentum[X] += self.run_speed
                    if self.momentum[X] > 0:
                        self.momentum[X] = 0;
            if self.momentum == [0, 0]:
                self.moving = False

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
        self.collider.centerx = self.location.centerx - scroll['x']
        self.collider.centery = self.location.centery - scroll['y'] + 7
        collisions, direction = self.world.blocks.collision_test(self.collider,
                                   movement, scroll)
        if collisions == []:  # no collisions, so free to move
            self.location.x += movement[X]
            self.location.y += movement[Y]
            self.momentum[Y] += GRAVITY  # constant downward pull
        else:
            if self.name == 'player':
                print(direction, len(collisions), self.momentum)
            if direction == 'vertical':
                # this is an experiment to try and avoid the character overlapping the
                # block and getting stuck when falling.
                # it doesn't work because, you just pogo on the block
                AARGH!
                self.location.y -= movement[Y]
                self.momentum[Y] = 0

        # draw the sprite at the new location
        surface.blit(frame, (self.location.x - scroll['x'],
                             self.location.y - scroll['y']))

    def move_left(self, distance = 1):
        # move a whole number of blocks to the left
        self.facing_right = False
        self.momentum[X] = distance * BLOCK_SIZE
        self.moving = True

    def move_right(self, distance = 1):
        self.facing_right = True
        self.momentum[X] = distance * BLOCK_SIZE
        self.moving = True

    def move_up(self, distance = 1):
        # move a whole number of blocks up
        # this is effectively a jump
        self.momentum[Y] = distance * BLOCK_SIZE
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
