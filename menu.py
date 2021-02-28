import pygame
from pygame.locals import *
import input_dialog
from console_messages import console_msg
from constants import *
from session import Session


class Menu:
    def __init__(self, screen, bypass = False):
        """ displays the main menu and ensures that the user is logged in
        before proceeding. If bypass==True the menu creates a dummy
        session, used for testing."""
        console_msg('Main menu', 0)
        self.screen = screen
        # this flag prevents certain key actions from automatically repeating
        # it is cleared when any key is released
        self.repeat_lock = False
        self._quit = False
        self._return_to_game = False
        self.clock = pygame.time.Clock()

        self.title_y_pos = 100
        self.title_size = 28
        self.items_y_pos = 370
        self.title = "Main Menu"
        self.items = ["Play", "Options", "Quit:"]
        self.selected_item = -1  # start off with nothing selected
        self.session = None

        if bypass:
            self.session = Session("dummy_user", "dummy_class")
            self._return_to_game = True
        else:
            # load the fonts
            if pygame.font.get_init() is False:
                pygame.font.init()
                console_msg("Font system initialised", 2)
            # we explicitly load all required fonts
            # so that the TTF files can be bundled to run on other PCs
            self.menu_title_font = pygame.font.Font(MENU_FONT_FILE, 48)
            self.menu_title_bg_font = pygame.font.Font(MENU_FONT_FILE, 50)
            self.menu_font = pygame.font.Font(MENU_FONT_FILE, 32)
            self.menu_input_font = pygame.font.Font(CODE_FONT_FILE, 32)
            console_msg("Menu font loaded", 3)
            self.input_dialog = MenuInputDialog(self.screen,
                                "Input",
                                self.menu_input_font)

    def quit(self):
        return self._quit

    def play(self):
        self._return_to_game = True

    def options(self):
        pass

    def display(self):
        """ draw the menu and handle input """

        while not self._quit and not self._return_to_game:
            # render the background
            self.screen.fill(COLOUR_MENU_BG)

            # display the title
            self.display_text(self.title,
                              self.menu_title_font,
                              self.title_y_pos,
                              COLOUR_MENU_TITLE,
                              shadow=True
                              )

            # display the menu items
            y_pos = self.items_y_pos
            for i in range(len(self.items)):
                if self.selected_item == i:
                    shadow = True
                else:
                    shadow = False
                self.display_text(self.items[i],
                                  self.menu_font,
                                  y_pos,
                                  shadow = shadow)
                y_pos += self.menu_font.get_linesize()*2

            # force user to log in, in order to proceed
            # whitespace names are not allowed
            if self.session is None:
                self.session = Session(*self.login())
                self.selected_item = 0
            else:
                # display name and class
                y_pos = self.items_y_pos - self.menu_font.get_linesize()*5
                self.display_text(self.session.get_user_name(),
                                  self.menu_input_font,
                                  y_pos,
                                  COLOUR_MENU_TITLE,
                                  shadow=False
                                  )
                y_pos += self.menu_input_font.get_linesize()
                self.display_text(self.session.get_class_name(),
                                  self.menu_input_font,
                                  y_pos,
                                  COLOUR_MENU_TITLE,
                                  shadow=False
                                  )
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
                    if self.selected_item > 0:
                        self.selected_item -= 1
                elif pressed[K_DOWN] or pressed[K_TAB]:
                    if self.selected_item < len(self.items)-1:
                        self.selected_item += 1
                elif pressed[K_RETURN]:
                    # activate the selected option
                    if self.selected_item == 0:
                        self.play()
                    elif self.selected_item == 1:
                        self.options()
                    elif self.selected_item == 2:
                        self._quit = True
                else:
                    self.repeat_lock = False  # reset, since no key pressed

            # process all other events to clear the queue
            for event in pygame.event.get():
                if event.type == KEYUP:
                    self.repeat_lock = False  # release the lock
                if event.type == QUIT:
                    self._quit = True

            self.clock.tick(60)  # lock the framerate to 60fps

    def display_text(self, text, font, y,
                     colour=COLOUR_MENU_TEXT,
                     shadow=False):
        # render a string on the screen, centred horizontally

        # work out the x position to centre-justify the text
        x = (self.screen.get_width() - font.size(text)[X]) / 2

        if shadow:
            line = font.render(text, True, (0, 0, 0))
            self.screen.blit(line, (x+3, y+3))
            self.screen.blit(line, (x, y))
        line = font.render(text, True, colour)
        self.screen.blit(line, (x, y))

    def login(self):
        """ enter username and class
        eventually this could use text files to validate against known names"""
        username = self.get_input("What is your name?")
        class_name = self.get_input("What class are you in?")

        # remove whitespace from both fields
        return username.strip(), class_name.strip()

    def get_input(self, prompt):
        self.input_dialog.title = prompt
        self.input_dialog.active = True
        self.input_dialog.reset()
        while self.input_dialog.is_active():
            self.input_dialog.update()
            self.input_dialog.draw()
            dialog_pos = (
                (self.screen.get_width() - self.input_dialog.width) / 2,
                self.items_y_pos - self.input_dialog.height - 50
            )
            dialog_area = pygame.Rect(
                0, 0,
                self.input_dialog.width, self.input_dialog.height
            )
            self.screen.blit(self.input_dialog.surface, dialog_pos, dialog_area)
            pygame.display.update()  # actually display
            self.clock.tick(60)  # lock the framerate to 60fps

        # wait for the Enter key to be released before returning
        # otherwise it immediately selects the first item in the menu
        finished = False
        while not finished:
            for event in pygame.event.get():
                if event.type == KEYUP:
                    finished = True
        return self.input_dialog.convert_to_lines()[0]

class MenuInputDialog(input_dialog.InputDialog):
    """ used for entering text options in menus"""

    def __init__(self, screen, prompt, font):
        super().__init__(screen, 120, font)

        # Override some settings FROM INPUT_DIALOG
        self.title = prompt
        self.centre_title = True
        self.color_modes[0] = (COLOUR_MENU_TEXT, COLOUR_MENU_BG)
        # define the permitted actions for special keys
        # self.key_action = {pygame.K_RETURN: self.return_input,
        #                    pygame.K_BACKSPACE: self.backspace,
        #                    pygame.K_DELETE: self.delete,
        #                    pygame.K_LEFT: self.cursor_left,
        #                    pygame.K_RIGHT: self.cursor_right,
        #                    pygame.K_TAB: self.tab,
        #                    }

        # Override some settings FROM EDITOR
        self.width = 500 # screen.get_size()[X]
        self.left_margin = self.char_width
        # calculate the number of characters that fit on a line
        self.row_width = int((self.width - self.left_margin - self.side_gutter)
                             / self.char_width)
        self.active = True

