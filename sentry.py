from characters import Robot
from console_messages import console_msg
from constants import ROBOT_SPRITE_FILE, SENTRY_FILE, SENTRY_START


class Sentry(Robot):
    # robot sentries used to present more complex puzzles
    def __init__(self, world, location, name='sentry'):
        super().__init__(world,
                         name,
                         ROBOT_SPRITE_FILE,
                         (16, 28),
                         2)
        self.set_position(location)
        # DEBUG convert source to a list of chars,
        # so that it can be handled the same as the editor code
        source = 'print("hi")'
        self.source_code = []
        line = []
        for char in source:
            line.append(char)
        self.source_code.append(line)
        console_msg("robot source loaded",0)

    def set_puzzle(self, instructions):
        pass

def load_sentries(world, level):
    # load all the sentries for a given level from the file
    file_name = SENTRY_FILE
    with open(file_name, 'r') as file:
        lines = file.readlines()  # read the whole file into a string array
    i = 0

    while i < len(lines):
        while i < len(lines) and lines[i][:-1] != SENTRY_START:  # look for the start of a sentry definition
            i += 1
        if i < len(lines):
            all_sentries = []
            name = lines[i+1][:-1]  # strip trailing CRLF
            sentry_level = eval(lines[i+2])
            position = eval(lines[i+3])
            display_program = []
            if sentry_level == level:  # only create the sentries for this game level
                s = Sentry(world, position, name)
                all_sentries.append(s)
            i += 3  # skip on to next sentry
    return all_sentries