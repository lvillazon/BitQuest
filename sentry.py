import file_parser
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

    def get_source_code(self):
        # override method from Robot, to allow code to stay as a list of strings
        return ['print("ho")']

def load_sentries(world, level):
    # load all the sentries for a given level from the file

    print(file_parser.parse_file(SENTRY_FILE))  # DEBUG


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
