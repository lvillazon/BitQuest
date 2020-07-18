import pygame
from sprite_sheet import SpriteSheet

X = 0
Y = 1

DOWN = 'down'
UP = 'up'
RUN = 1
STOP = 2
SAVE = 3
LOAD = 4
CHANGE_COLOR = 5


class Button:
    """ handles the up/down state of the buttons, as well as the
    different color schemes
    """


class ButtonTray:
    """ a strip of icon buttons anchored to the corner of the editor window """

    def __init__(self, sprite_filename, surface):
        self.button_names = (RUN, STOP, SAVE, LOAD, CHANGE_COLOR)
        self.surface = surface
        self.button_count = 5
        self.button_size = 16
        self.button_margin = 2
        width = ((self.button_size * self.button_count) +
                 (self.button_margin * (self.button_count + 1)))
        height = self.button_size + self.button_margin * 2
        self.tray_size = (width, height)
        self.top_left = [(surface.get_size()[X] - width - 3),
                         (surface.get_size()[Y] - height) - 3]
        self.tray = pygame.Rect(self.top_left, self.tray_size)

        self.sprites = SpriteSheet('assets/' + sprite_filename)
        # the icons don't use alpha transparency - bg color is fixed
        #self.up_buttons = self.sprites.load_strip(
        #    pygame.Rect(0, 0, self.button_size, self.button_size),
        #    self.button_count)
        #self.down_buttons = self.sprites.load_strip(
        #    pygame.Rect(self.button_size * self.button_count, 0,
        #                self.button_size, self.button_size),
        #    self.button_count)
        self.buttons = {}
        up_pos = [0, 0]
        down_pos = [self.button_size * self.button_count, 0]
        size = (self.button_size, self.button_size)
        self.buttons = {}
        for name in self.button_names:
            self.buttons[name] = \
                     {UP: self.sprites.image_at(pygame.Rect(up_pos, size)),
                      DOWN: self.sprites.image_at(pygame.Rect(down_pos, size))}
            up_pos[X] += self.button_size
            down_pos[X] += self.button_size

        self.button_state = {RUN: UP,
                             SAVE: UP,
                             STOP: UP,
                             LOAD: UP,
                             CHANGE_COLOR: UP}

    def click(self, pos):
        # returns the button constant corresponding to the pos (x,y) coords
        # or None if pos lies outside the tray
        if self.tray.collidepoint(pos):
            # convert x coord to the button number
            button = int((pos[X] - self.top_left[X]) /
                         (self.button_size + self.button_margin)) + 1
            if button in self.button_names:
                self.button_state[button] = DOWN
                return button
        return None

    def release(self):
        # revert all the buttons to their up state
        for button in self.button_names:
            self.button_state[button] = UP

    def draw(self, fg_color, bg_color):
        pygame.draw.rect(self.surface, fg_color, self.tray)

        pos = [self.top_left[X] + self.button_margin,
               self.top_left[Y] + self.button_margin]
        for b in self.button_names:
            button_image = self.buttons[b][self.button_state[b]]
            self.surface.blit(button_image, pos)
            pos[X] += self.button_size + self.button_margin
