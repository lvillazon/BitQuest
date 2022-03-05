import pygame
from pygame.locals import *

from console_messages import console_msg
from constants import COLOUR_MENU_TEXT, MENU_FONT_FILE, CODE_FONT_FILE, X, COLOUR_MENU_BG, DEBUG


class MenuList:
    def __init__(self, screen, x, y, font, items, spacing=1):
        """
        displays a modal dialog with a vertical list of items
        that can be selected using cursor keys
        TODO: add mouse support
        """
        self.screen = screen
        # this flag prevents certain key actions from automatically repeating
        # it is cleared when any key is released
        self.repeat_lock = True
        self._quit = False
        self._selected = ''
        self.clock = pygame.time.Clock()

        self.font = font
        self.x_pos = x
        self.y_pos = y
        self.width = len(max(items, key=len)) * self.font.size('X')[X] +4  # chars in longest item * char width. The +4 is to allow for the drop shadow
        self.height = self.screen.get_height() - self.y_pos
        self._unfiltered_items = items
        self.items = items
        self.selected_index = 0  # start off with the top item selected
        self.level = 0  # default, invalid level number
        self.spacing = spacing  # >1 inserts blank lines between menu items
        self.filter = []  # used to dynamically filter the menu list as the user types the first few chars of an item
        self._printable = "1234567890-=[]#;',./abcdefghijklmnopqrstuvwxyz " \
                           '!"£$%^&*()_+{}~:@<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ'  # used for keyboard input

    def quit(self):
        return self._quit

#    def play(self):
#        self._return_to_game = True

    def display(self):
        """ draw the list items and wait for a user selection """
        self._selected = ''
        while not self._quit and not self._selected:
            # blank the draw area
            blanking_rect = Rect(self.x_pos, self.y_pos, self.width, self.height)
            pygame.draw.rect(self.screen, COLOUR_MENU_BG, blanking_rect)

            # display the menu items
            y = self.y_pos
            for i in range(len(self.items)):
                if self.selected_index == i:
                    shadow = True
                else:
                    shadow = False

                self.display_text(self.items[i],
                                  self.font,
                                  self.x_pos,
                                  y,
                                  shadow = shadow)
                y += self.font.get_linesize()*self.spacing

            pygame.display.update()  # actually display

            # keyboard input
            pressed = pygame.key.get_pressed()
            if pressed[K_ESCAPE]:
                # TODO add a confirmation dialog
                self._quit = True

            # these actions do not auto repeat when held down
            if not self.repeat_lock:
                self.repeat_lock = True

                if pressed[K_UP]:
                    if self.selected_index > 0:
                        self.selected_index -= 1
                elif pressed[K_DOWN] or pressed[K_TAB]:
                    if self.selected_index < len(self.items)-1:
                        self.selected_index += 1
                elif pressed[K_RETURN]:
                    # selected the current item
                    self._selected = self.items[self.selected_index]

                else:
                    self.repeat_lock = False  # reset, since no key pressed

            # process all other events to clear the queue
            for event in pygame.event.get():
                if event.type == KEYUP:
                    self.repeat_lock = False  # release the lock

                # handle all the printable characters
                if event.type == KEYDOWN:
                    if event.unicode != '' and event.unicode in self._printable:
                        self.filter.append(event.unicode)
                    elif event.key == pygame.K_BACKSPACE and self.filter:
                        self.filter.pop()
                    self.filter_menu_items();
                    if DEBUG:
                        print('menu filter=', self.filter)

                if event.type == QUIT:
                    self._quit = True

            self.clock.tick(60)  # lock the framerate to 60fps

        return self._selected

    def display_text(self, text, font, x, y,
                     colour=COLOUR_MENU_TEXT,
                     shadow=False):
        # render a string on the screen

        if shadow:
            line = font.render(text, True, (0, 0, 0))
            self.screen.blit(line, (x+3, y+3))
            self.screen.blit(line, (x, y))
        line = font.render(text, True, colour)
        self.screen.blit(line, (x, y))

    def filter_menu_items(self):
        # restrict the displayed list to just those that begin with the filter string
        self.items = []
        filter_string = ''.join(self.filter).upper()
        for item in self._unfiltered_items:
            if filter_string in item.upper():
                self.items.append(item)
