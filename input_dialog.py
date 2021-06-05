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
        self.keyboard_input.register_key_press('RETURN', self.return_input)
        self.keyboard_input.register_key_press('BACKSPACE', self.backspace)
        self.keyboard_input.register_key_press('DELETE', self.delete)
        self.keyboard_input.register_key_press('LEFT', self.cursor_left)
        self.keyboard_input.register_key_press('RIGHT', self.cursor_right)
        self.keyboard_input.register_key_press('TAB', self.tab)

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
