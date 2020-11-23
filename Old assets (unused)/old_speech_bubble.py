import pygame

from constants import *

class AllBubbles():
    """ container for all character speech and hint bubbles """

    def __init__(self):
        self.bubbles = []

    def add_bubble(self, b):
        self.bubbles.append(b)

    def draw_bubbles(self, surface, scroll):
        for b in self.bubbles:
            b.draw(surface, scroll)

class SpeechBubble():
    """ Displays dialog and hint text in auto-sizing bubbles
    which can be anchored to a character or fixed in place in the scene"""

    text = []  # list of lines of text to be displayed
    BUBBLE_TEXT_MARGIN = 10  # pixels between the bubble and the text

    def __init__(self, new_text = "", anchor = None, position = [0,0]):
        self.anchor = anchor  # link to the character that is speaking
        self.position = position  # absolute grid pos (if anchor = None)
        if new_text != "":
            self.text.append(new_text)
        # all new bubble start out small and then grow until they
        # are large enough to accommodate their text
        self.width = 5
        self.height = 5

    def draw(self, surface, scroll):
        if self.anchor != None:
            # update bubble position to track the anchored character
            self.position = self.anchor.location

        bubble_rect = pygame.Rect((self.position[X], self.position[Y]),
                                  (self.width, self.height))
        bubble = pygame.Surface((self.width, self.height))
        # fill with red to use as the transparency key
        bubble.fill((255, 0, 0))
        surface.blit(bubble, self.position)

"""        
    def create_speech_bubble(self, text, fg_col, bg_col):
        # show a speak-bubble above the character with the text in it
        new_text = str(text)
        self.text.append(new_text)
        self.speech_bubble_size = self.world.code_font.size(new_text)
        if self.speech_bubble_size[X] > self.text_size[X]:
            self.text_size[X] = self.speech_bubble_size[X]
        if len(self.text) < self.MAX_TEXT_LINES:
            self.text_size[Y] += self.speech_bubble_size[Y]
        self.speech_bubble_fg = fg_col
        self.speech_bubble_bg = bg_col
        self.speaking = True

    def draw_speech_bubble(self, surface):
        bubble_rect = pygame.Rect((0, 0),
                                  (self.text_size[X] + self.BUBBLE_MARGIN * 2,
                                   self.text_size[Y] + self.BUBBLE_MARGIN * 2)
                                  )
        self.bubble = pygame.Surface(bubble_rect.size)
        # fill with red to use as the transparency key
        self.bubble.fill((255, 0, 0))
        self.bubble.set_colorkey((255, 0, 0))
        # create a rectangle with clipped corners for the speech bubble
        # (rounded corners aren't available until pygame 2.0)
        w = bubble_rect.width
        h = bubble_rect.height
        m = self.BUBBLE_MARGIN
        pygame.draw.polygon(self.bubble, self.speech_bubble_bg,
                            ((m , 0)   , (w - m, 0),
                             (w, m)    , (w, h - m),
                             (w - m, h), (m, h),
                             (0, h - m), (0, m)
                            )
                           )
        # draw the lines of text, working upwards from the most recent,
        # until the bubble is full
        output_line = len(self.text) - 1
        line_y_pos = h - m - self.speech_bubble_size[Y]
        color = self.speech_bubble_fg
        while line_y_pos >= m and output_line >= 0:
            line = self.world.code_font.render(self.text[output_line],
                                               True, color)
            self.bubble.blit(line, (m, line_y_pos))
            output_line -= 1
            line_y_pos -= self.speech_bubble_size[Y]

    def update_speech_bubble(self):
        pass
        
"""
