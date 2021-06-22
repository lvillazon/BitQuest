import pygame
from constants import *
from editor import Editor


class InputDialog(Editor):
    def __init__(self, screen, height, code_font):
        super().__init__(screen, height, code_font)
        # hitting Enter returns the value,
        # so you can only have one input line anyway
        self.max_lines = 1
        self.title = "Input"
        self.color_modes[0] = (BLACK, SKY_BLUE)
        # define the permitted actions for special keys
        self.key_action = {pygame.K_RETURN: self.return_input,
                           pygame.K_BACKSPACE: self.backspace,
                           pygame.K_DELETE: self.delete,
                           pygame.K_LEFT: self.cursor_left,
                           pygame.K_RIGHT: self.cursor_right,
                           pygame.K_TAB: self.tab,
                           }

    def print_line_number(self, n, row):
        # override to suppress line numbers
        # hella ugly - TODO move the line number code from Editor to CodeEditor
        pass

    def activate(self, prompt):
        self.reset()
        self.title = prompt
        self.active = True

    def return_input(self):
        self.active = False
        # print(self.convert_to_lines())
