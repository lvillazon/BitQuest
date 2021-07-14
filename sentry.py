import pygame

import file_parser
from characters import Robot
from console_messages import console_msg
from constants import *
import io
import contextlib
from utility_functions import screen_to_grid

class Sentry(Robot):
    # robot sentries used to present more complex puzzles
    def __init__(self, world,
                 name,
                 location,
                 programs):
        super().__init__(world,
                         name,
                         ROBOT_SPRITE_FILE,
                         (16, 28),
                         2)
        self.set_position(location)
        # assign the source code for the robots programs
        self.programs = {}
        self.programs = programs
        self.active_program = self.programs['init']  # default to this one
        self.output = []
#        self.standing_left_frame = self.move_left_frames[0]
#        self.standing_right_frame = self.move_left_frames[1]
        self.facing_right = False
        self.testdata = -99
        self.defeated = BYPASS_SENTRIES  # normally set True, but False for testing
        self.blocking = not self.defeated

    def set_puzzle(self, instructions):
        pass

    def run_program(self, program_name):
        if not self.defeated:
            # allows the sentry to switch between several available programs
            self.active_program = self.programs[program_name]
            # force the enabled flag because sentries can run their code
            # at any time, not just once per puzzle attempt
            self.python_interpreter.run_enabled = True
    #        self.clear_speech_bubble()
    #        self.output = []
            super().run_program()
            print(self.output)

    def get_source_code(self):
        # override method from Robot, to allow code to stay as a list of strings
        return self.active_program

    def is_at(self, screen_coords, scroll):
        # returns True if the sentry is located at this position on the screen
        # this is used to detect mouse clicks
        x = (self.location.x - scroll[X]) * SCALING_FACTOR
        y = (self.location.y - scroll[Y]) * SCALING_FACTOR
        w = self.size[X] * SCALING_FACTOR
        h = self.size[Y] * SCALING_FACTOR
        collision_rect = pygame.Rect((x, y), (w, h))
        if collision_rect.collidepoint(screen_coords):
            return True
        else:
            return False

    def is_challenge_complete(self, dog):
        # checks the most recent output from BIT against the results
        # of its own validation program
        if self.programs['validate']:
            self.run_program('validate')
            if len(self.output) != len(dog.output):
                valid = False
            else:
                valid = True
                for i in range(len(self.output)):
                    if self.output[i] != dog.output[i].rstrip():
                        valid = False
            if valid:
                self.say("Correct!")
                self.blocking = False
                self.facing_right = True  # select the frame to show he is standing aside
                self.defeated = True
            else:
                expected = self.output.copy()
                self.say("Incorrect! I expected:")
                for line in expected:
                    self.say(line)

    def say(self, *t):
        # override say so that the validate method can intercept the output
        # and compare to the player's code, before displaying the results
        if not self.defeated:
            if (self.active_program == self.programs['validate'] and
                    self.python_interpreter.running):

                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    print(*t, end='')  # TODO use a different way of suppressing ugly chars for carriage returns, that allows the user programs to still use the end= keyword
                    speech = f.getvalue()
                    self.output.append(speech)
            else:
                super().say(*t)


    def get_data(self):  # TESTING
        return self.testdata

    def set_data(self, value):
        console_msg('setting ' + self.name + ' data to ' + str(value))
        self.testdata = value



def load_sentries(world, level):
    # load all the sentries for a given level from the file

    sentry_data = file_parser.parse_file(SENTRY_FILE)
    print(sentry_data)  # DEBUG

    all_sentries = []
    for data in sentry_data:
        # use default values for any missing fields in data
        if 'name' not in data:
            data['name'] = 'sentry'
        if 'level' not in data:
            data['level'] = -1,
        if 'position' not in data:
            data['position'] = (0, 0)
        data['programs'] = {'init': [], 'display': [], 'validate': []}
        if 'init' in data:
            data['programs']['init'] = data['init']
        if 'display' in data:
            data['programs']['display'] = data['display']
        if 'validate' in data:
            data['programs']['validate'] = data['validate']

        # only create the sentries for this game level
        # or those for whom no level was specified
        if data['level'] == level or data['level'] == -1:
            console_msg("creating sentry...", 7)
            print(data['name'])
            s = Sentry(world,
                       data['name'],
                       data['position'],
                       data['programs'],
                       )
            all_sentries.append(s)
            console_msg('sentry ' + data['name'] + ' created', 7)
    return all_sentries
