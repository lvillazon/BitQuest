import math

import pygame
from constants import *


class SpeechBubble():

    def __init__(self, text):
        self.line_width = 3
        self.border = 8  # gap between the outer edge and the bubble outline
        self.position = (500, 600)
        self.size = [0, 0]
        self.trueSize = [0.0, 0.0]
        self.target_size = [0, 0]
        self.fg_col = (230, 230, 230)  # light grey
        self.bg_col = (0, 155, 255)  # sky blue
        self.alpha_mask = (255, 0, 255)  # use a horrible magenta as the key
        self.resizing = False  # true if the bubble is currently resizing

    def get_outline_points(self, size):
        # returns a list of points to draw the bubble outline
        # the shape is a rectangle with chamfered corners
        # and an elongated spike in the bottom left as the callout
        b = self.border
        b2 = b * 2
        b3 = b * 3
        offset = b * 2 - self.line_width
        w = size[0] - offset
        h = size[1] - offset * 2
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
        steps = 200  # number of frames to animate the oscillation for
        cycle = 540  # number of degrees to oscillate the sine wave for
        wobble_size = 40  # amplitude of the over/undershoot on the bubble size
        self.growSequence = []
        for i in range(steps):
            angle = cycle/steps * i
            sine = math.sin(math.radians(angle))
            amplitude = (1-i/steps)  # progressively damps the wobble
            wobble_factor = wobble_size * sine * amplitude
            sizeStep = [wobble_factor + target[X],
                        wobble_factor + target[Y]
                        ]
            # prepend the new value, so the list can be read as a stack
            self.growSequence.insert(0, sizeStep)
        self.resizing = True

    def draw(self, surface):
        bubble = pygame.Surface((self.size[X] + self.line_width,
                                 self.size[Y] + self.line_width))
        bubble.fill(self.alpha_mask)
        #bubble.set_colorkey(self.alpha_mask)

        # inflate or deflate the bubble until it reaches the target size
        if self.growSequence:  # list is not empty
            inflation = self.growSequence.pop()
            self.size[X] = int(inflation[X])
            self.size[Y] = int(inflation[Y])
        else:
            self.resizing = False

        bubble_points = self.get_outline_points(self.size)
        pygame.draw.polygon(bubble,
                            self.bg_col,
                            bubble_points,
                            0)
        pygame.draw.polygon(bubble,
                            self.fg_col,
                            bubble_points,
                            self.line_width)
        surface.blit(bubble,
                     (self.position[X], self.position[Y] - self.size[Y]))

