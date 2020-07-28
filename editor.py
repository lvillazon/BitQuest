import pygame
import button_tray
import interpreter

# used to index into (x,y) tuples
X = 0
Y = 1

# return values from cursor move functions
CURSOR_FAIL = 0
CURSOR_OK = 1
CURSOR_LINE_WRAP = 2


class Editor:
    # on-screen editor for writing programs
    def __init__(self, screen, height, code_font, dog):
        self.code_font = code_font
        self.screen = screen
        self.width = screen.get_size()[X]
        self.height = height
        self.dog = dog  # a link tot he dog character, to allow programs to access the game state
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
        # absolute line number of the cursor
        self.cursor_line = 0
        # character position of the cursor within the current line
        self.cursor_col = 0
        self.buttons = button_tray.ButtonTray('editor icons.png', self.surface)

        print("row width =", self.row_width)

    def show(self):
        pygame.key.set_repeat(500, 50)
        self.active = True

    def hide(self):
        pygame.key.set_repeat()  # disable autorepeat
        self.active = False

    def is_active(self):
        return self.active

    def add_keystroke(self, char):
        # insert char at the current cursor pos
        # and update the cursor
        # don't allow typing past the end of the line
        if self.cursor_col < self.row_width:
            self.text[self.cursor_line].insert(self.cursor_col, char)
            self.cursor_col += 1

    def backspace(self):
        # back up the cursor and remove the character at that pos
        move = self.cursor_left()
        if move == CURSOR_OK:
            del self.text[self.cursor_line][self.cursor_col]
        if move == CURSOR_LINE_WRAP:
            # if we backspace at the start of a line,
            # merge this line with the one above
            self.text[self.cursor_line].extend(self.text[self.cursor_line + 1])
            # delete empty line
            del self.text[self.cursor_line + 1]

    def delete(self):
        # suck up text at the cursor
        if self.cursor_col < len(self.text[self.cursor_line]):
            del self.text[self.cursor_line][self.cursor_col]
        # suck up the line below if there is nothing to suck on this line
        elif self.cursor_line < len(self.text) - 1:
            # merge this line with the one above
            self.text[self.cursor_line].extend(self.text[self.cursor_line + 1])
            # delete empty line
            del self.text[self.cursor_line + 1]

    def carriage_return(self):
        # at the cursor, split the line into two
        # then put the cursor at the start of the new line
        new_line = self.text[self.cursor_line][self.cursor_col:]
        self.text.insert(self.cursor_line + 1, new_line)
        del self.text[self.cursor_line][self.cursor_col:]
        self.cursor_col = 0
        self.cursor_line += 1
        # scroll if necessary
        if self.get_cursor_xy()[Y] > self.max_lines - 2:
            self.v_scroll += 1

    def cursor_left(self):
        # moves cursor with line wrap
        # returns true if the cursor successfully moved
        if self.cursor_col > 0:
            self.cursor_col -= 1
            return CURSOR_OK
        elif self.cursor_line > 0:
            self.cursor_line -= 1
            self.cursor_col = len(self.text[self.cursor_line])
            return CURSOR_LINE_WRAP
        else:
            return CURSOR_FAIL

    def cursor_right(self):
        # moves cursor with line wrap
        # returns true if the cursor successfully moved
        if self.cursor_col < len(self.text[self.cursor_line]):
            self.cursor_col += 1
            return CURSOR_OK
        elif self.cursor_line < len(self.text) - 1:
            self.cursor_line += 1
            self.cursor_col = 0
            return CURSOR_LINE_WRAP
        else:
            return CURSOR_FAIL

    def cursor_up(self):
        # moves cursor, snapping to the end of the line if necessary
        # returns true if the cursor successfully moved
        if self.cursor_line > 0:
            self.cursor_line -= 1
            # scroll if necessary
            if self.get_cursor_xy()[Y] < 1 and self.v_scroll > 0:
                self.v_scroll -= 1
            # snap to end of line
            if self.cursor_col > len(self.text[self.cursor_line]):
                self.cursor_col = len(self.text[self.cursor_line])
            return CURSOR_OK
        else:
            return CURSOR_FAIL

    def cursor_down(self):
        # moves cursor, snapping to the end of the line if necessary
        # returns true if the cursor successfully moved
        if self.cursor_line < len(self.text) - 1:
            self.cursor_line += 1
            # scroll if necessary
            if self.get_cursor_xy()[Y] > self.max_lines - 2:
                self.v_scroll += 1
            # snap to end of line
            if self.cursor_col > len(self.text[self.cursor_line]):
                self.cursor_col = len(self.text[self.cursor_line])
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

    def clipboard_cut(self):
        print("CUT")

    def clipboard_copy(self):
        print("COPY")

    def clipboard_paste(self):
        print("PASTE")
        clipboard_text = pygame.scrap.get(pygame.SCRAP_TEXT) \
            .decode("utf-8").replace('\0', '')  # strip trailing nulls

        for char in clipboard_text:
            # paste the chars in the keyboard, 1 at a time
            if char is chr(13):
                self.carriage_return()
            elif char >= chr(32) and char <= chr(126):  # only allow ASCII
                self.add_keystroke(char)

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
            elif button_result == button_tray.RUN:
                self.run_program()
            elif button_result == button_tray.STOP:
                print("Stop")
            elif button_result == button_tray.LOAD:
                print("Load")
            elif button_result == button_tray.SAVE:
                print("Save")
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
                      pygame.K_F5: self.run_program,
                      }
        shifted = {lower: upper for lower, upper in
                   zip("1234567890-=[]#;',./abcdefghijklmnopqrstuvwxyz ",
                       '!"£$%^&*()_+{}~:@<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ ')}
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
                                 }
                    if event.key in shortcuts:
                        shortcuts[event.key]()
                else:
                    # handle all the printable characters
                    if chr(event.key) in shifted:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            char = shifted[chr(event.key)]
                        else:
                            char = chr(event.key)
                        self.add_keystroke(char)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_button = {1: self.left_click,
                                # 3: self.start_selection,
                                4: self.cursor_up,  # scroll up
                                5: self.cursor_down,  # scroll down
                                }
                # middle button is 2, right button is 3
                if event.button in mouse_button:
                    mouse_button[event.button]()
            elif event.type == pygame.MOUSEBUTTONUP:
            #    self.stop_selection()  # any button release cancels selection
                self.buttons.release() # also unclick any clicked buttons

            # we also have to handle the quit event, since the main loop
            # isn't watching events while the editor is open
            # we don't actually want to quit the game though
            # TODO prompt user to save code
            elif event.type == pygame.QUIT:
                print("WARNING: Save code before quitting?")

    def print(self, s, pos):
        # renders a string s onto the editor surface at [x, y] position p
        if s != '':
            rendered_text = self.code_font.render(s, True, self.get_fg_color())
            position = (self.left_margin + pos[X] * self.char_width,
                        self.top_margin + pos[Y] * self.line_height)
            self.surface.blit(rendered_text, position)

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
        self.print("_", self.get_cursor_xy())

        # draw UI buttons
        self.buttons.draw(self.get_fg_color(), self.get_bg_color())

    def run_program(self):
        # convert the raw editor characters into lines of source code for the interpreter
        source = []
        for line in self.text:
            source.append(''.join(line))
        i = interpreter.Interpreter(self.dog)
        i.load(source)
        i.lex()
        i.run()
