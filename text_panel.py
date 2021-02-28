import pygame

from constants import *


class TextPanel:

    def __init__(self, text, fg_color, bg_color, font):
        # text is stored as a list with one string per line
        self.text = [str(text) + " "]  # make sure each line is at least one space wide to avoid weirdness
        self.font = font
        self.font_size = font.size(self.text[0])  # width and height, in pixels
        self.fg_color = fg_color
        self.bg_color = bg_color

    def get_width(self):
        # return width of the longest line
        max = 0
        for line in self.text:
            width = self.font_size[X]
            if width > max:
                max = width
        return max

    def get_height(self):
        # height of all lines or max height, whichever is less
        if len(self.text) <= MAX_BUBBLE_TEXT_LINES:
            return len(self.text) * self.font_size[Y]
        else:
            return MAX_BUBBLE_TEXT_LINES * self.font_size[Y]

    def clear(self):
        self.text = []
        self.font_size = [0, 0]

    def rendered(self, surface):
        rect = pygame.Rect((0, 0), (
            (self.get_width()
             + TEXT_MARGIN * 2
             + BALLOON_THICKNESS * 2
             + BUBBLE_MARGIN),
            (self.get_height()
             + TEXT_MARGIN * 2
             + BALLOON_THICKNESS * 2
             + BUBBLE_MARGIN * 2)
        ))
        bubble = pygame.Surface(rect.size)
        # fill with red to use as the transparency key
        bubble.fill((255, 0, 0))
        bubble.set_colorkey((255, 0, 0))
        # create a rectangle with clipped corners for the speech bubble
        # (rounded corners aren't available until pygame 2.0)
        bubble_points = (
            (BALLOON_THICKNESS, rect.size[Y] - BALLOON_THICKNESS),  # A
            (BUBBLE_MARGIN + BALLOON_THICKNESS,
             rect.size[Y] - BUBBLE_MARGIN * 2),  # B
            (BUBBLE_MARGIN + BALLOON_THICKNESS,
             BUBBLE_MARGIN),  # C
            (BUBBLE_MARGIN * 2, 0),  # D
            (rect.size[X] - BUBBLE_MARGIN, 0),  # E
            (rect.size[X] - BALLOON_THICKNESS,
             BUBBLE_MARGIN),  # F
            (rect.size[X] - BALLOON_THICKNESS,
             rect.size[Y] - BUBBLE_MARGIN * 3),  # G
            (rect.size[X] - BUBBLE_MARGIN,
             rect.size[Y] - BUBBLE_MARGIN * 2),  # H
            (BUBBLE_MARGIN * 3, rect.size[Y] - BUBBLE_MARGIN * 2),  # I
        )
        pygame.draw.polygon(bubble,
                            self.bg_color,
                            bubble_points,
                            0)
        pygame.draw.polygon(bubble,
                            self.fg_color,
                            bubble_points,
                            BALLOON_THICKNESS)
        # draw the lines of text, working upwards from the most recent,
        # until the bubble is full
        output_line = len(self.text) - 1
        line_y_pos = (rect.size[Y]
                      - BUBBLE_MARGIN * 2
                      - TEXT_MARGIN
                      - self.get_height())
        color = self.fg_color
        while line_y_pos >= TEXT_MARGIN and output_line >= 0:
            line = self.font.render(self.text[output_line], True, color)
            line_x_pos = BUBBLE_MARGIN + TEXT_MARGIN + BALLOON_THICKNESS
            bubble.blit(line, (line_x_pos, line_y_pos))
            output_line -= 1
            line_y_pos -= self.get_height()
        return bubble
