# 2-digit-level: (name, instructions, data, solution)
# <PUZZLE>
# 1
# test
# (10, 10)
# print the numbers 0 to {data[0]} inclusive, each on a separate line
# [(5, 20)]
# <SOLUTION>
# for i in range({data[0]}+1:
#     print(i)
# </SOLUTION>
# </PUZZLE>

import random

import interpreter
from console_messages import console_msg
from constants import PUZZLE_FILE

PUZZLE_START = '<PUZZLE>\n'
PUZZLE_END = '</PUZZLE>\n'
SOLUTION_START = '<SOLUTION>\n'
SOLUTION_END = '</SOLUTION>\n'

class Puzzle():
    # a programming task that must be solved to proceed
    # this is different from the simple puzzles where pressing a trigger
    # removes the obstacle. These ones include an explanation, data
    # the required output and success/fail/hint messages.
    # puzzles are loaded from a text file and referenced by a simple title.

    def __init__(self, hosted_on, puzzle_name = ""):
        self.robot = hosted_on  # the Robot object that will execute the code for this puzzle
        self.name = puzzle_name  # simple string
        self.instructions = None  # f-string explaining the puzzle
        self.data = None  # list of expressions, evaluated to give the parameters
        self.solution = None  # list of python lines, executed to compare with the player solution

def load_puzzles(level, world):
    # load all the puzzles for a given level from the file
    file_name = PUZZLE_FILE
    with open(file_name, 'r') as file:
        lines = file.readlines()
        i = 0
        # look for the start of a puzzle
        while i < len(lines) and lines[i] != PUZZLE_START:
            i += 1
        if i < len(lines):
            # get level number
            i += 1
            level = eval(lines[i])
            # get puzzle name
            i += 1
            name = lines[i][:-1]  # strip the trailing CR+LF
            i += 1
            # get location of the sentry that will host the puzzle
            sentry_position = eval(lines[i])
            sentry = Sentry(sentry_position)

            # get the instructions for the puzzle
            i += 1
            instructions = convert_to_f_string(lines[i][:-1])

            # get the puzzle data (parameters for the puzzle)
            i += 1
            data = []
            # data is stored as tuples representing the range of possible values
            # for each item. If there are exactly 2 numeric values in the tuple,
            # it is interpreted as the lower and upper bounds for randint()
            # otherwise it is treated as a list for choice()
            data_strings = eval(lines[i])  # the list of tuples for all the parameters
            for item in data_strings:
                if len(item) == 2 and isinstance(item[0], int) and isinstance(item[1], int):
                    data.append(random.randint(int(item[0]), int(item[1])))
                else:
                    data.append(random.choice(item))
            print(eval(instructions))  # DEBUG will this pick up the f string param?

            # get the source code for the exemplar solution
            i += 1
            print(data)
            if lines[i] == SOLUTION_START:
                i += 1
                solution_source = []
                while lines[i] != SOLUTION_END and i < len(lines):
                    solution_source.append(eval(convert_to_f_string(lines[i][:-1])))
                    i += 1
                print(solution_source)
                self.run_program(solution_source)
                if i >= len(lines):
                    console_msg("Error: missing end_of_solution in puzzle file!", 0)
            else:
                console_msg("Error: missing start_of_solution in puzzle file!", 0)
        else:
            # ran off the end of the file
            console_msg('Error parsing puzzle file!', 0)

    def run_program(self, source):
        """ pass the text in the puzzle solution to the interpreter"""
        p = interpreter.VirtualMachine(self.robot)
        p.load(source)
        result, errors = p.compile()
        if result is False:  # check for syntax errors
            # TODO display these using in-game dialogs
            if p.compile_time_error:
                error_msg = p.compile_time_error['error']
                error_line = p.compile_time_error['line']
                console_msg('BIT found a SYNTAX ERROR:', 5)
                msg = error_msg + " on line " + str(error_line)
                console_msg(msg, 5)
        else:
            result, errors = p.run()  # set the program going


def convert_to_f_string(text):
    # add the f'' to allow this to be processed as an f-string
    return "f'" + text + "'"

