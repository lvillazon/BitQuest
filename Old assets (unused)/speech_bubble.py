import math

import pygame
from constants import *


class SpeechBubble():

    def __init__(self, text, owner, world):
        self.line_thickness = 3
        self.border = 8  # gap between the outer edge and the bubble outline
        self.position = (200, 200)
        self.size = [0, 0]  # size of the bubble in pixels
        self.trueSize = [0.0, 0.0]  # float version of size
        self.target_size = [0, 0]  # desired size, when resizing
        self.text_size = [0, 0]  # size required for text, in pixels
        self.growSequence = []
        self.fg_col = (230, 230, 230)  # light grey
        self.bg_col = (0, 155, 255)  # sky blue
        self.alpha_mask = (255, 0, 255)  # use a horrible magenta as the key
        self.resizing = False  # true if the bubble is currently resizing
        self.bubble = None
        self.owner = owner
        self.text = []
        self.font = world.code_font
        self.fg_col = world.editor.get_fg_color()
        self.bg_col = world.editor.get_bg_color()
        new_text = str(text)  # force any integers into string format
        self.text.append(new_text)
        # determine the initial dimensions for the bubble
        new_text_size = self.font.size(new_text)
        self.line_height = new_text_size[Y]
        self.set_target_size(new_text_size)
        # if new_text_size[X] > self.text_size[X]:
        #     self.text_size[X] = new_text_size[X]
        # if len(self.text) < MAX_BUBBLE_TEXT_LINES:
        #     self.text_size[Y] += self.speech_bubble_size[Y]

    def add(self, new_text):
        self.text.append(new_text)
        # determine the new dimensions for the bubble
        target_size = self.size.copy()
        new_text_size = self.font.size(new_text)
        if new_text_size[X] > self.size[X]:
            target_size[X] = new_text_size[X]
        if len(self.text) <= MAX_BUBBLE_TEXT_LINES:
            target_size[Y] = len(self.text) * self.line_height
        else:
            target_size[Y] = MAX_BUBBLE_TEXT_LINES * self.line_height
        self.set_target_size(target_size)
        print("current=", self.size,
              "new_text=", new_text_size,
              "target=", target_size)


    def get_outline_points(self, size):
        # returns a list of points to draw the bubble outline
        # the shape is a rectangle with chamfered corners
        # and an elongated spike in the bottom left as the callout
        b = self.border
        b2 = b * 2
        b3 = b * 3
        offset = b * 2 - self.line_thickness
        w = size[X] + BUBBLE_MARGIN * 2 - offset
        h = size[Y] + BUBBLE_MARGIN * 2 - offset * 2
        points = (
            (b, b2),
            (b2, b),
            (w - b, b),
            (w, b2),
            (w, h - b),
            (w - b, h),
            (b3, h),  # callout spike for the speech bubble
            (0, h + b2),
            (b, h)
        )
        return points

    def set_target_size(self, target):
        # creates a stack of width,height tuples to animate the bubble growth
        # uses a damped sine wave to give a nice wobble effect
        # actual bubble is larger than the text, so we add on the margin
        target_x = target[X] #+ BUBBLE_MARGIN * 2
        target_y = target[Y] #+ BUBBLE_MARGIN * 2
        steps = 45  # number of frames to animate the oscillation for
        cycle = 540  # number of degrees to oscillate the sine wave for
        wobble_size = 30  # amplitude of the over/undershoot on the bubble size
        self.growSequence = []
        for i in range(steps):
            angle = cycle/steps * i
            sine = math.sin(math.radians(angle))
            amplitude = (1-i/steps)  # progressively damps the wobble
            wobble_factor = wobble_size * sine * amplitude
            sizeStep = [wobble_factor + target_x,
                        wobble_factor + target_y
                        ]
            # prepend the new value, so the list can be read as a stack
            self.growSequence.insert(0, sizeStep)
        self.resizing = True
        print("target=", target, "final=", self.growSequence[-1])

    def draw(self, surface, scroll):
        if self.bubble:
            # erase the previous bubble
            self.bubble.fill(self.alpha_mask)
            self.bubble.set_colorkey(self.alpha_mask)

        # create a new one for the current frame
        self.bubble = pygame.Surface(
            (self.size[X] + self.line_thickness * 2,
             self.size[Y] + self.line_thickness * 2))
        self.bubble.fill(self.alpha_mask)
        self.bubble.set_colorkey(self.alpha_mask)

        # inflate or deflate the bubble until it reaches the target size
        if self.growSequence:  # list is not empty
            inflation = self.growSequence.pop()
            self.size[X] = int(inflation[X])
            self.size[Y] = int(inflation[Y])
            print(inflation)
        else:
            self.resizing = False

        bubble_points = self.get_outline_points(self.size)
        pygame.draw.polygon(self.bubble,
                            self.bg_col,
                            bubble_points,
                            0)
        pygame.draw.polygon(self.bubble,
                            self.fg_col,
                            bubble_points,
                            self.line_thickness)

        # draw the lines of text, working upwards from the most recent,
        # until the bubble is full
        output_line = len(self.text) - 1
        line_pos = [self.border * 2,
                    self.size[Y] - self.line_height - self.border * 4]
        while line_pos[Y] >= 0 and output_line >= 0:
            line = self.font.render(self.text[output_line],
                                    True, self.fg_col)

            self.bubble.blit(line, line_pos)
            output_line -= 1
            line_pos[Y] -= self.line_height

        # copy final bubble image to the screen
        surface.blit(self.bubble,
                     (self.position[X], self.position[Y]
                      - self.size[Y]))

