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

    def clear(self):
        self.text = []

    def get_rendered_text_width(self):
        # return width of the longest line
        max = 0
        for line in self.text:
            width = self.font.size(line)[X]
            if width > max:
                max = width
        return max

    def get_rendered_text_height(self):
        # height of all lines or max height, whichever is less
        if len(self.text) <= MAX_BUBBLE_TEXT_LINES:
            return len(self.text) * self.font_size[Y]
        else:
            return MAX_BUBBLE_TEXT_LINES * self.font_size[Y]

    # def clear(self):
    #     self.text = []
    #     self.font_size = [0, 0]

    def append(self, new_text):
        self.text.append(new_text + " ")  # padding space to avoid rendering weirdness

    def get_outline_rect(self):
        # returns a bounding rect for the whole panel
        # coords are panel-relative, so top left is always 0,0
        return pygame.Rect((0, 0), (
            (self.get_rendered_text_width()
             + TEXT_MARGIN * 2
             + BORDER_THICKNESS * 2
             + BUBBLE_MARGIN),
            (self.get_rendered_text_height()
             + TEXT_MARGIN * 2
             + BORDER_THICKNESS * 2
             + BUBBLE_MARGIN)
        ))

    def get_surface(self):
        rect = self.get_outline_rect()
        s = pygame.Surface((rect.width, rect.height + BUBBLE_MARGIN*2))
        # fill with red to use as the transparency key
        s.fill((255, 0, 0))
        s.set_colorkey((255, 0, 0))
        return s

    def draw_panel(self, fg_color, bg_color):
        s = self.get_surface()
        outline = self.get_outline_rect()
        pygame.draw.rect(s, bg_color, outline, 0)
        pygame.draw.rect(s, fg_color, outline, BORDER_THICKNESS)
        return s

    def rendered(self):
        if self.text:
            panel = self.draw_panel(self.fg_color, self.bg_color)

            # draw the lines of text, working upwards from the most recent,
            # until the bubble is full
            outline = self.get_outline_rect()
            output_line = len(self.text) - 1
            line_y_pos = (outline.size[Y]
                          - BUBBLE_MARGIN
                          - TEXT_MARGIN
                          - self.font_size[Y])  # self.get_rendered_text_height())
            color = self.fg_color
            while line_y_pos >= TEXT_MARGIN and output_line >= 0:
                line = self.font.render(self.text[output_line], True, color)
                line_x_pos = BUBBLE_MARGIN + TEXT_MARGIN + BORDER_THICKNESS
                panel.blit(line, (line_x_pos, line_y_pos))
                output_line -= 1
                line_y_pos -= self.font_size[Y]  #self.get_rendered_text_height()
            return panel
        else:
            return None


class SpeechBubble(TextPanel):
    # adds the callout spike

    def draw_panel(self, fg_color, bg_color):
        s = self.get_surface()
        outline = self.get_outline_rect()
        pygame.draw.rect(s, bg_color, outline, 0, BALLOON_CORNER_RADIUS)
        pygame.draw.rect(s, fg_color, outline, BORDER_THICKNESS, BALLOON_CORNER_RADIUS)

        # add the callout triangle
        bottom_edge = s.get_height() - BUBBLE_MARGIN * 2
        # see Dev Log Oct 10, for diagram explaining A, B and I
        A = (BORDER_THICKNESS, bottom_edge + BUBBLE_MARGIN * 2 - BORDER_THICKNESS)
        B = (BUBBLE_MARGIN + BORDER_THICKNESS, bottom_edge - BORDER_THICKNESS)
        I = (BUBBLE_MARGIN * 3, bottom_edge - BORDER_THICKNESS)

        callout_points = (B, A, I)
        pygame.draw.polygon(s, self.bg_color, callout_points)
        pygame.draw.lines(s, self.fg_color, False, callout_points, BORDER_THICKNESS)

        return s

        self.speech_bubble_size = self.world.code_font.size(new_text)
        if self.speech_bubble_size[X] > self.text_size[X]:
            self.text_size[X] = self.speech_bubble_size[X]
        if len(self.text) <= MAX_BUBBLE_TEXT_LINES:
            self.text_size[Y] += self.speech_bubble_size[Y]



class InfoPanel(TextPanel):
    def __init__(self, title, text, fg_color, bg_color, font):
        super().__init__('', fg_color, bg_color, font)
        for line in text:
            super().append(line)
        self.title = title

    def get_rendered_text_width(self):
        # return width of the longest line or the title, whichever is largest
        return max(super().get_rendered_text_width(), self.font.size(self.title)[X] + self.font_size[Y])

    def draw_panel(self, fg_color, bg_color):
        s = self.get_surface()
        panel_size = self.get_outline_rect()
        outline = pygame.Rect((0,0), (panel_size.width - DROP_SHADOW, panel_size.height - DROP_SHADOW))
        # black drop shadow for contrast
        drop_shadow = pygame.Rect((DROP_SHADOW, DROP_SHADOW), outline.size)
        pygame.draw.rect(s, BLACK, drop_shadow, 0)

        pygame.draw.rect(s, bg_color, outline, 0)
        pygame.draw.rect(s, fg_color, outline, BORDER_THICKNESS)

        # add the title bar
        title = self.font.render(self.title, True, bg_color)
        title_bar = pygame.Rect((0,0), (outline.width, self.font_size[Y]))
        pygame.draw.rect(s, self.fg_color, title_bar)
        s.blit(title, (BUBBLE_MARGIN,0))

        # add the close button to the right-hand edge of the title bar
        # the button is a square, with side equal to the height of the title bar
        top = BORDER_THICKNESS
        bottom = title_bar.bottom - BORDER_THICKNESS
        left = outline.width - bottom
        right = left + bottom - BORDER_THICKNESS
        self.button_rect = pygame.Rect((left, top), (right-left, bottom-top))
        pygame.draw.rect(s, fg_color, self.button_rect)
        pygame.draw.line(s, bg_color, (left, top), (right, bottom), CROSS_THICKNESS)
        pygame.draw.line(s, bg_color, (left, bottom), (right, top), CROSS_THICKNESS)

        return s

    def get_close_button_rect(self):
        # returns a bounding rect for the close button
        # coords are panel-relative
        return self.button_rect
