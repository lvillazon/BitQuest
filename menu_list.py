import sys

import pygame
from pygame.locals import *
from constants import *


class MenuList:
    def __init__(self, screen, x, y, selected_font, normal_font, items, spacing=1, filterable=True):
        """
        displays a modal dialog with a vertical list of items
        that can be selected using cursor keys or mouse
        """
        self.screen = screen
        self._quit = False
        self._selected = ''
        self.clock = pygame.time.Clock()

        self.selected_font = selected_font
        self.normal_font = normal_font
        self.x_pos = x
        self.y_pos = y
        self.width = len(max(items, key=len)) * self.selected_font.size('X')[X]  # chars in longest item * char width
        self.height = self.screen.get_height() - self.y_pos
        self._unfiltered_items = items
        self.items = items
        self.selected_index = 0  # start off with the top item selected
        self.level = 0  # default, invalid level number
        self.spacing = spacing  # >1 inserts blank lines between menu items
        self.filterable = filterable  # if true, menu items can be filtered as you type
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
        start_index = 0
        end_index = min(13, len(self.items))
        while not self._quit and not self._selected:
            # blank the draw area
            blanking_rect = Rect(self.x_pos, self.y_pos, self.width, self.height)
            pygame.draw.rect(self.screen, COLOUR_MENU_BG, blanking_rect)

            # display the menu items that fit on the screen
            y = self.y_pos
            if self.selected_index > start_index + 10:
                start_index = self.selected_index - 10
                end_index = start_index + 13
                if end_index > len(self.items):
                    end_index = len(self.items)
            elif self.selected_index < end_index - 11:
                end_index = self.selected_index + 11
                if end_index < min(13, len(self.items)):
                    end_index = min(13, len(self.items))
                start_index = end_index - 13
                if start_index < 0:
                    start_index = 0

            for i in range(start_index, end_index):
                if self.selected_index == i:
                    self.display_text(self.items[i],
                                      self.selected_font,
                                      self.x_pos,
                                      y,
                                      colour=COLOUR_MENU_USERNAME)
                else:
                    self.display_text(self.items[i],
                                      self.normal_font,
                                      self.x_pos,
                                      y)
                y += self.selected_font.get_linesize() * self.spacing

            pygame.display.update()  # actually display

            # keyboard input
            pressed = pygame.key.get_pressed()
            if pressed[K_ESCAPE]:
                # TODO add a confirmation dialog
                self._quit = True

            elif pressed[K_UP]:
                pygame.time.delay(100)
                if self.selected_index > 0:
                    self.selected_index -= 1
            elif pressed[K_DOWN] or pressed[K_TAB]:
                pygame.time.delay(100)
                if self.selected_index < len(self.items) - 1:
                    self.selected_index += 1
            elif pressed[K_RETURN]:
                # selected the current item
                pygame.time.delay(100)
                self._selected = self.items[self.selected_index]

            # process all other events
            for event in pygame.event.get():
                if event.type == MOUSEWHEEL:
                    self.selected_index -= event.y
                    if self.selected_index < 0:
                        self.selected_index = 0
                    elif self.selected_index >= len(self.items) - 1:
                        self.selected_index = len(self.items) - 1

                elif event.type == MOUSEBUTTONDOWN and pygame.mouse.get_pressed(3)[0]:  # if left mouse button pressed
                    relative_mouse_coords = (pygame.mouse.get_pos()[X] - self.x_pos,
                                             pygame.mouse.get_pos()[Y] - self.y_pos)
                    if 0 < relative_mouse_coords[X] < self.width:
                        mouse_index = relative_mouse_coords[Y] // (self.selected_font.get_linesize() * self.spacing) \
                                      + start_index
                        self.selected_index = mouse_index
                        self._selected = self.items[mouse_index]
                # handle all the printable characters
                elif event.type == KEYDOWN:
                    if event.unicode != '' and event.unicode in self._printable:
                        self.filter.append(event.unicode)
                        self.filter_menu_items()
                        start_index = 0
                        end_index = min(13, len(self.items))
                    elif event.key == pygame.K_BACKSPACE and self.filter:
                        self.filter.pop()
                        self.filter_menu_items()
                        start_index = 0
                        end_index = min(13, len(self.items))

                elif event.type == QUIT:
                    sys.exit()  # ends the program entirely if you click the close icon on the user login screen

            self.clock.tick(60)  # lock the framerate to 60fps

        return self._selected

    def display_text(self, text, font, x, y,
                     colour=COLOUR_MENU_TEXT,
                     shadow=False):
        # render a string on the screen

        if shadow:
            line = font.render(text, True, (0, 0, 0))
            self.screen.blit(line, (x + 3, y + 3))
            self.screen.blit(line, (x, y))
        line = font.render(text, True, colour)
        self.screen.blit(line, (x, y))

    def filter_menu_items(self):
        if not self.filterable:
            return

        # restrict the displayed list to just those that begin with the filter string
        self.items = []
        filter_string = ''.join(self.filter).upper()
        for item in self._unfiltered_items:
            if filter_string in item.upper():
                self.items.append(item)
        self.selected_index = 0
        if DEBUG:
            print('menu filter=', self.filter)
