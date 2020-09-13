import pygame
import button_tray

# used to index into (x,y) tuples
from console_messages import console_msg

X = 0
Y = 1

# return values from cursor move functions
CURSOR_FAIL = 0
CURSOR_OK = 1
CURSOR_LINE_WRAP = 2


class Editor:
    # on-screen editor for writing programs
    def __init__(self, screen, height, code_font, program):
        self.program = program
        self.code_font = code_font
        self.screen = screen
        self.width = screen.get_size()[X]
        self.height = height
        self.v_scroll = 0  # line offset to allow text to be scrolled
        self.surface = pygame.Surface((self.width, self.height))
        self.top_margin = 8
        self.side_gutter = 8  # pixel gap from the edge of the surface
        sky_blue = (0, 155, 255)
        light_grey = (230, 230, 230)
        black = (0, 0, 0)
        yellow = (255, 229, 153)
        green = (113, 201, 168)
        self.color_modes = {0: (light_grey, sky_blue),
                            1: (black, yellow),
                            2: (black, green)}
        self.palette = 0
        self.active = False
        self.line_height = self.code_font.get_linesize()
        # maximum number of lines that will fit in the editor window
        self.max_lines = int(self.height / self.line_height)
        # width of a single character
        # (monospaced font, so they're all the same)
        self.char_width = self.code_font.size(" ")[X]
        # the margin allows space for the line numbers
        self.left_margin = self.side_gutter + self.char_width * 3
        # calculate the number of characters that fit on a line
        self.row_width = int((self.width - self.left_margin - self.side_gutter)
                             / self.char_width)
        # the text is represented as a list of logical lines
        # each line is a list of characters
        # there are no line terminator characters or padding characters
        # we initialise with a single row
        self.text = [[]]
        self.history = []  # undo history is a list where each element is a copy of self.text
        # absolute line number of the cursor
        self.cursor_line = 0
        # character position of the cursor within the current line
        self.cursor_col = 0
        self.selecting = False  # True when currently marking a block of text
        self.selection_start = (0, 0)  # cursor coords of the start and end of the marked block
        self.selection_end = (0, 0)
        self.deleting_block = False
        self.buttons = button_tray.ButtonTray('editor icons.png', self.surface)

        console_msg("Editor row width =" + str(self.row_width), 8)

    def show(self):
        pygame.key.set_repeat(500, 50)
        self.active = True

    def hide(self):
        pygame.key.set_repeat()  # disable autorepeat
        self.active = False

    def is_active(self):
        return self.active

    def add_keystroke(self, char, undo=True):
        # insert char at the current cursor pos
        # and update the cursor
        if undo:
            self.save_history()  # preserve undo history
        self.delete_selected_text()  # typing always replaces any selected block
        if self.cursor_col < self.row_width:  # don't allow typing past the end of the line
            self.text[self.cursor_line].insert(self.cursor_col, char)
            self.cursor_col += 1

    def backspace(self, undo=True):
        """ back up the cursor and remove the character at that pos """

        if undo:
            self.save_history()
        # if there is no selection or we are in the middle of deleting one, then just delete a single character
        if self.deleting_block or self.selection_start == self.selection_end:
            # if there are 4 spaces to the left of the cursor,
            # remove them in one go, since we treat this as a tab
            if self.text[self.cursor_line][self.cursor_col-4: self.cursor_col] == [' ', ' ', ' ', ' ']:
                for i in range(4):
                    self.cursor_left()
                    del self.text[self.cursor_line][self.cursor_col]
            else:  # otherwise just delete one char
                move = self.cursor_left()
                if move == CURSOR_OK:
                    del self.text[self.cursor_line][self.cursor_col]
                if move == CURSOR_LINE_WRAP:
                    # if we backspace at the start of a line,
                    # merge this line with the one above
                    self.text[self.cursor_line].extend(self.text[self.cursor_line + 1])
                    # delete empty line
                    del self.text[self.cursor_line + 1]
        else:
            # delete the selected text (if any)
            self.delete_selected_text()

    def delete(self):
        # if there is no selection, then just delete a single character
        # the delete_selected_text function never calls delete(), so we don't need to check
        # if we are in the middle of deleting a block, like we do for backspace()
        self.save_history()
        if self.selection_start == self.selection_end:
            # suck up text at the cursor
            if self.cursor_col < len(self.text[self.cursor_line]):
                del self.text[self.cursor_line][self.cursor_col]
            # suck up the line below if there is nothing to suck on this line
            elif self.cursor_line < len(self.text) - 1:
                # merge this line with the one above
                self.text[self.cursor_line].extend(self.text[self.cursor_line + 1])
                # delete empty line
                del self.text[self.cursor_line + 1]
        else:
            self.delete_selected_text()

    def delete_selected_text(self):
        if self.selection_start != self.selection_end:
            console_msg("Deleting selection", 8, line_end='')
            self.save_history()
            self.deleting_block = True  # used to prevent backspace() also trying to delete the block
            # make sure the cursor is positioned at the end of the selection
            self.cursor_col, self.cursor_line = self.selection_end
            # backspace all the way to the first char in the selection
            while (self.cursor_col, self.cursor_line) != self.selection_start:
                self.backspace(undo=False)  # turn off undo for the individual deletions, since we have alsready saved
                print(".", end='')
            # cancel this selection
            self.selection_start = (0, 0)
            self.selection_end = (0, 0)
            self.deleting_block = False
            print(" done.")

    def carriage_return(self, undo=True):
        """break the line at the cursor"""
        if undo:
            self.save_history()
        self.delete_selected_text()  # typing always replaces any selected block

        # we want to match the indentation of the current line
        # so we must check for spaces at the start of the current line
        # which we do by comparing the length of the line with the length
        # of the lstripped string version of the line
        indent = (len(self.text[self.cursor_line]) -
                  len(''.join(self.text[self.cursor_line]).lstrip()))

        # if the previous line ends in a :, we increase the indent by 4 spaces
        if self.text[self.cursor_line][self.cursor_col-1] == ':':
            indent += 4

        # at the cursor, split the line into two
        # beginning with indentation spaces as required
        new_line = [' '] * indent
        new_line.extend(self.text[self.cursor_line][self.cursor_col:])
        self.text.insert(self.cursor_line + 1, new_line)
        del self.text[self.cursor_line][self.cursor_col:]
        # then put the cursor at the (indented) start of the new line
        self.cursor_col = indent
        self.cursor_line += 1
        # scroll if necessary
        if self.get_cursor_xy()[Y] > self.max_lines - 2:
            self.v_scroll += 1

    def cursor_left(self):
        # moves cursor with line wrap
        # returns true if the cursor successfully moved

        # check if SHIFT is held, to see if we should be starting a new selection
        if (pygame.key.get_mods() & pygame.KMOD_SHIFT) and not self.selecting:
                self.start_selecting()

        if self.cursor_col > 0:
            self.cursor_col -= 1
            if self.selecting:  # extend selection
                self.selection_end = (self.cursor_col, self.cursor_line)
            return CURSOR_OK
        elif self.cursor_line > 0:
            self.cursor_line -= 1
            self.cursor_col = len(self.text[self.cursor_line])
            if self.selecting:  # extend selection
                self.selection_end = (self.cursor_col, self.cursor_line)
            return CURSOR_LINE_WRAP
        else:
            return CURSOR_FAIL

    def cursor_right(self):
        # moves cursor with line wrap
        # returns true if the cursor successfully moved

        # check if SHIFT is held, to see if we should be starting a new selection
        if (pygame.key.get_mods() & pygame.KMOD_SHIFT) and not self.selecting:
                self.start_selecting()

        if self.cursor_col < len(self.text[self.cursor_line]):
            self.cursor_col += 1
            if self.selecting:  # extend selection
                self.selection_end = (self.cursor_col, self.cursor_line)
            return CURSOR_OK
        elif self.cursor_line < len(self.text) - 1:
            self.cursor_line += 1
            self.cursor_col = 0
            if self.selecting:  # extend selection
                self.selection_end = (self.cursor_col, self.cursor_line)
            return CURSOR_LINE_WRAP
        else:
            return CURSOR_FAIL

    def cursor_up(self):
        # moves cursor, snapping to the end of the line if necessary
        # returns true if the cursor successfully moved

        # check if SHIFT is held, to see if we should be starting a new selection
        if (pygame.key.get_mods() & pygame.KMOD_SHIFT) and not self.selecting:
                self.start_selecting()

        if self.cursor_line > 0:
            self.cursor_line -= 1
            # scroll if necessary
            if self.get_cursor_xy()[Y] < 1 and self.v_scroll > 0:
                self.v_scroll -= 1
            # snap to end of line
            if self.cursor_col > len(self.text[self.cursor_line]):
                self.cursor_col = len(self.text[self.cursor_line])
            if self.selecting:  # extend selection
                self.selection_end = (self.cursor_col, self.cursor_line)
            return CURSOR_OK
        else:
            return CURSOR_FAIL

    def cursor_down(self):
        # moves cursor, snapping to the end of the line if necessary
        # returns true if the cursor successfully moved

        # check if SHIFT is held, to see if we should be starting a new selection
        if (pygame.key.get_mods() & pygame.KMOD_SHIFT) and not self.selecting:
                self.start_selecting()

        if self.cursor_line < len(self.text) - 1:
            self.cursor_line += 1
            # scroll if necessary
            if self.get_cursor_xy()[Y] > self.max_lines - 2:
                self.v_scroll += 1
            # snap to end of line
            if self.cursor_col > len(self.text[self.cursor_line]):
                self.cursor_col = len(self.text[self.cursor_line])
            if self.selecting:  # extend selection
                self.selection_end = (self.cursor_col, self.cursor_line)
            return CURSOR_OK
        else:
            return CURSOR_FAIL

    def cursor_to_mouse_pos(self):
        # if the mouse is within the text area
        # snap the cursor to the nearest character position
        mouse_pos = (pygame.mouse.get_pos()[X],
                     pygame.mouse.get_pos()[Y] -
                     self.screen.get_size()[Y] + self.height)
        if self.surface.get_rect().collidepoint(mouse_pos):
            # convert mouse coords to char coords
            char_x = int((mouse_pos[X] - self.left_margin) / self.char_width)
            char_y = (int((mouse_pos[Y] - self.top_margin) / self.line_height)
                      + self.v_scroll)
            # now snap to the nearest actual char in the text
            if char_y < len(self.text):
                self.cursor_line = char_y
            else:
                self.cursor_line = len(self.text) - 1
            if char_x < len(self.text[self.cursor_line]):
                self.cursor_col = char_x
            else:
                self.cursor_col = len(self.text[self.cursor_line])

            # update the currently selected block, or start a new block
            if self.selecting:
                self.selection_end = (self.cursor_col, self.cursor_line)
            else:
                self.selection_start = (self.cursor_col, self.cursor_line)

    def page_up(self):
        # page up by calling cursor_up multiple times
        for i in range(self.max_lines):
            if not self.cursor_up():
                break

    def page_down(self):
        # page down by calling cursor_down multiple times
        for i in range(self.max_lines):
            if not self.cursor_down():
                break

    def tab(self):
        # insert 4 spaces
        self.save_history()
        TAB = '    '
        for i in TAB:
            self.add_keystroke(i, undo=False)  # turn off undo for the individual spaces, since we already saved

    def clipboard_cut(self):
        console_msg("CUT", 8)
        self.save_history()

    def clipboard_copy(self):
        console_msg("COPY", 8)

    def clipboard_paste(self):
        console_msg("PASTE", 8)
        self.save_history()
        clipboard_text = pygame.scrap.get(pygame.SCRAP_TEXT) \
            .decode("utf-8").replace('\0', '')  # strip trailing nulls

        for char in clipboard_text:
            # paste the chars in the keyboard, 1 at a time
            if char is chr(13):
                self.carriage_return(undo=False)
            elif char >= chr(32) and char <= chr(126):  # only allow ASCII
                self.add_keystroke(char, undo=False)

    def start_selecting(self):
        self.selecting = True
        self.selection_start = (self.cursor_col, self.cursor_line)
        console_msg("Begin selection", 8)

    def stop_selecting(self):
        self.selecting = False
        console_msg("End selection", 8)

    def select_all(self):
        # mark all the text in the editor
        self.selection_start = (0, 0)
        last_line = len(self.text) - 1
        last_col = len(self.text[last_line])
        self.selection_end = (last_col, last_line)
        self.cursor_line = last_line
        self.cursor_col = last_col

    def save_history(self):
        # preserve a snapshot of the current code
        # to do this, we need to make a deep copy of the current self.text data structure
        snapshot = []
        for line in self.text:
            snapshot_line = line.copy()
            snapshot.append(snapshot_line)
        # save this snapshot, together with the current cursor position
        self.history.append((snapshot, self.cursor_col, self.cursor_line))

    def undo(self):
        # roll back the editor text to the last snapshot saved in the undo history
        print(self.history)
        if len(self.history) > 0:
            snapshot = self.history.pop()
            self.text = snapshot[0]
            self.cursor_col = snapshot[1]  # also restore the save position of the cursor
            self.cursor_line = snapshot[2]

    def get_cursor_xy(self):
        # return the (x,y) character coords represented by
        # cursor_line and cursor_col, taking into account the v_scroll
        return self.cursor_col, self.cursor_line - self.v_scroll

    def left_click(self):
        # check whether to click a button or reposition the cursor
        mouse_pos = (pygame.mouse.get_pos()[X],
                     pygame.mouse.get_pos()[Y] -
                     self.screen.get_size()[Y] + self.height)
        if self.surface.get_rect().collidepoint(mouse_pos):
            button_result = self.buttons.click(mouse_pos)
            if button_result is None:
                self.cursor_to_mouse_pos()
                self.selecting = True  # begin marking a selection at the current position
            elif button_result == button_tray.RUN:
                self.run_program()
            elif button_result == button_tray.STOP:
                console_msg("Execution halted.", 1)
                self.program.halt()
            elif button_result == button_tray.LOAD:
                self.load_program()
            elif button_result == button_tray.SAVE:
                self.save_program()
            elif button_result == button_tray.CHANGE_COLOR:
                self.color_switch()

    def color_switch(self):
        # cycle the editor colors through the different modes
        self.palette = (self.palette + 1) % 3

    def get_fg_color(self):
        return self.color_modes[self.palette][0]

    def get_bg_color(self):
        return self.color_modes[self.palette][1]

    def update(self):
        # process all the keystrokes in the event queue

        key_action = {pygame.K_ESCAPE: self.hide,
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
        printable = "1234567890-=[]#;',./abcdefghijklmnopqrstuvwxyz " \
                    '!"£$%^&*()_+{}~:@<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key in key_action:
                    # handle all the special keys
                    key_action[event.key]()
                elif pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # handle the keyboard shortcuts
                    shortcuts = {pygame.K_x: self.clipboard_cut,
                                 pygame.K_c: self.clipboard_copy,
                                 pygame.K_v: self.clipboard_paste,
                                 pygame.K_s: self.save_program,
                                 pygame.K_o: self.load_program,
                                 pygame.K_a: self.select_all,
                                 pygame.K_z: self.undo,
                                 }
                    if event.key in shortcuts:
                        shortcuts[event.key]()
                else:
                    # handle all the printable characters
                    if event.unicode != '' and event.unicode in printable:
                        self.add_keystroke(event.unicode)

            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.stop_selecting()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_button = {1: self.left_click,
                                # 2: middle button
                                # 3: right button
                                4: self.cursor_up,  # scroll up
                                5: self.cursor_down,  # scroll down
                                }
                if event.button in mouse_button:
                    mouse_button[event.button]()
            elif event.type == pygame.MOUSEBUTTONUP:
                self.cursor_to_mouse_pos()
                self.selecting = False  # any button release cancels selection
                self.buttons.release()  # also unclick any clicked buttons

            # we also have to handle the quit event, since the main loop
            # isn't watching events while the editor is open
            # we don't actually want to quit the game though
            # TODO prompt user to save code
            elif event.type == pygame.QUIT:
                console_msg("WARNING: Save code before quitting?", 2)

        if self.selecting:
            # use the mouse to update the selected block, provided SHIFT is not held down
            # this keeps mouse and keyboard selections from interfering with each other
            if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                self.cursor_to_mouse_pos()

    def in_marked_block(self, x, y):
        char_pos = y * self.row_width + x
        start_pos = self.selection_start[Y] * self.row_width + self.selection_start[X]
        end_pos = self.selection_end[Y] * self.row_width + self.selection_end[X]
        if start_pos > end_pos:
            # swap them over so that start is always early in the text than end
            temp = start_pos
            start_pos = end_pos
            end_pos = temp
        if (char_pos >= start_pos) and (char_pos < end_pos):
            return True
        else:
            return False

    def print(self, s, pos, transparent = False):
        # renders a string s onto the editor surface at [x, y] position p
        if s != '':
            column = pos[X]
            for char in s:
                if self.in_marked_block(column, pos[Y]):
                    # draw the characters using inverse colours
                    if transparent:
                        rendered_char = self.code_font.render(char, True, self.get_bg_color())  # omit bg col
                    else:
                        rendered_char = self.code_font.render(char, True, self.get_bg_color(), self.get_fg_color())
                else:
                    # unselected text always uses a transparent background
                    rendered_char = self.code_font.render(char, True, self.get_fg_color())
                position = (self.left_margin + column * self.char_width,
                            self.top_margin + pos[Y] * self.line_height)
                column += 1
                self.surface.blit(rendered_char, position)

    def print_line_number(self, n, row):
        # print the line number n, padded correctly at the specified row
        # the line numbers are printed into the left margin
        # which is not accessible to the normal print method
        line_text = "{0:2d} ".format(n)
        rendered_text = self.code_font.render(
            line_text, True, self.get_fg_color())
        position = (self.side_gutter,
                    self.top_margin + row * self.line_height)
        self.surface.blit(rendered_text, position)

    def draw(self):
        # display editor UI and current program, if any

        # fill background and draw border
        self.surface.fill(self.get_bg_color())
        border = pygame.Rect(4, 4, self.width - 8, self.height - 8)
        pygame.draw.rect(self.surface, self.get_fg_color(), border, 2)

        # render each line of text from the current v_scroll position
        # to the bottom of the window
        for line in range(self.max_lines):
            line_number = self.v_scroll + line
            # don't render lines that don't exist, obviously
            if line_number < len(self.text):
                self.print_line_number(line_number + 1, line)
                self.print(''.join(self.text[line_number]), (0, line))

        # draw the cursor
        self.print("_", self.get_cursor_xy(), transparent=True)

        # draw UI buttons
        self.buttons.draw(self.get_fg_color(), self.get_bg_color())

    def convert_to_lines(self):
        """ convert the raw editor characters into lines of source code
         so that they can be saved/parsed etc conveniently"""
        source = []
        for line in self.text:
            source.append(''.join(line))
        return source

    def save_program(self):
        """save source code to a default filename"""
        # TODO add save dialogue to change name/folder
        with open('BitQuest_user_program.py', 'w') as file:
            for line in self.convert_to_lines():
                file.write(line + '\n')

    def load_program(self):
        """load source code from a default filename"""
        # TODO add open dialogue to change name/folder
        self.save_history()
        with open('BitQuest_user_program.py', 'r') as file:
            lines = file.readlines()
            self.text = []
            for file_line in lines:
                line = list(file_line)  # convert string to a list of chars
                if line[-1] == '\n':  # strip carriage return from each line
                    line.pop()
                self.text.append(line)

    def run_program(self):
        """ pass the text in the editor to the interpreter"""
        p = self.program
        p.load(self.convert_to_lines())
        result = p.compile()
        if result is False:  # check for syntax errors
            # TODO display these using in-game dialogs
            if p.compile_time_error:
                error_msg = p.compile_time_error['error']
                error_line = p.compile_time_error['line']
                console_msg('BIT found a SYNTAX ERROR:', 5)
                msg = error_msg + " on line " + str(error_line)
                console_msg(msg, 5)
        else:
            p.run()  # set the program going
