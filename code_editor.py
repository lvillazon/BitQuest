import pygame

import button_tray
import interpreter
from console_messages import console_msg
from constants import *
from editor import Editor


class CodeWindow(Editor):
    def __init__(self, screen, height, code_font, p, session):
        super().__init__(screen, height, code_font)
        # increase the margin to allow for the line numbers
        self.left_margin += self.char_width * 3
        self.title = "Code"
        self.python_interpreter = p
        self.session = session
        # define the permitted actions for special keys
        self.key_action = {pygame.K_ESCAPE: self.hide,
                           pygame.K_RETURN: self.carriage_return,
                           pygame.K_BACKSPACE: self.backspace,
                           pygame.K_DELETE: self.delete,
                           pygame.K_UP: self.cursor_up,
                           pygame.K_DOWN: self.cursor_down,
                           pygame.K_LEFT: self.cursor_left,
                           pygame.K_RIGHT: self.cursor_right,
                           pygame.K_PAGEUP: self.page_up,
                           pygame.K_PAGEDOWN: self.page_down,
                           pygame.K_TAB: self.tab,
                           pygame.K_F5: self.run_program,
                           }
        # add an extra 2 shortcut keys that only apply to the code window
        self.ctrl_shortcuts[pygame.K_s] = self.save_program
        self.ctrl_shortcuts[pygame.K_o] = self.load_program

    def draw(self):
        super().draw()
        # draw UI buttons
        self.buttons.draw(self.get_fg_color(), self.get_bg_color())

    def left_click(self):
        # check whether to click a button or reposition the cursor
        mouse_pos = (pygame.mouse.get_pos()[X],
                     pygame.mouse.get_pos()[Y] -
                     self.screen.get_size()[Y] + self.height)
        if self.surface.get_rect().collidepoint(mouse_pos):
            button_result = self.buttons.click(mouse_pos)
            if button_result is None:
                self.cursor_to_mouse_pos()
                # begin marking a selection at the current position
                self.selecting = True
            else:
                # clicking a button should never affect text selection
                self.selecting = False
                if button_result == button_tray.RUN:
                    self.run_program()
                elif button_result == button_tray.STOP:
                    console_msg("Execution halted.", 1)
                    self.python_interpreter.halt()
                elif button_result == button_tray.LOAD:
                    self.load_program()
                elif button_result == button_tray.SAVE:
                    self.save_program()
                elif button_result == button_tray.CHANGE_COLOR:
                    self.color_switch()

    def mouse_up(self):
        super().mouse_up()
        self.buttons.release()  # also unclick any clicked buttons

    def save_program(self):
        """save source code to a default filename"""
        # TODO add save dialogue to change name/folder
        with open(USER_PROGRAM_FILE, 'w') as file:
#            for line in interpreter.convert_to_lines(self.text):
            for line in self.convert_to_lines():
                    file.write(line + '\n')

    def load_program(self):
        """load source code from a default filename"""
        # TODO add open dialogue to change name/folder
        self.save_history()
        with open(USER_PROGRAM_FILE, 'r') as file:
            lines = file.readlines()
            self.text = []
            for file_line in lines:
                line = list(file_line)  # convert string to a list of chars
                if line[-1] == '\n':  # strip carriage return from each line
                    line.pop()
                self.text.append(line)

    # def run_program(self):
    #     """ pass the text in the editor to the interpreter"""
    #     # run_enabled is set false on each run
    #     # and cleared using the reset button
    #     if self.python_interpreter.run_enabled:
    #         p = self.python_interpreter
    #         #p.load(interpreter.convert_to_lines(self.text))
    #         p.load(self.convert_to_lines())
    #         # false because level is not complete yet
    #         result, errors = p.compile()
    #         if result is False:  # check for syntax errors
    #             # TODO display these using in-game dialogs
    #             if p.compile_time_error:
    #                 error_msg = p.compile_time_error['error']
    #                 error_line = p.compile_time_error['line']
    #                 console_msg('BIT found a SYNTAX ERROR:', 5)
    #                 msg = error_msg + " on line " + str(error_line)
    #                 console_msg(msg, 5)
    #         else:
    #             result, errors = p.run()  # set the program going
    #         # save this attempt, regardless of whether it has errors or not
    #         #self.session.save_run(interpreter.convert_to_lines(self.text), errors)
    #         self.session.save_run(self.convert_to_lines(), errors)
    #
