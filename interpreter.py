import dis  # built-in python disassembler - used for tokenising
import sys

from io import StringIO


class Interpreter:
    def __init__(self):
        self.source = []
        self.byte_code = []
        self.stack = []
        self.executable = {'instructions': [], 'values': []}

    def add_code(self, line):
        # add a single line of code to the interpreter's source
        self.source.append(line)

    def get_code(self):
        # converts all the source into a single string with carriage returns
        return chr(13).join(self.source)

    # the functions for the instruction set
    def LOAD(self, number):
        # add an operand to the stack
        self.stack.append(number)

    def ADD(self):
        # pop the top 2 values, add them and push the result
        first_num = self.stack.pop()
        second_num = self.stack.pop()
        self.stack.append(int(first_num) + int(second_num))

    def PRINT(self):
        # pop a value and output to console
        print(self.stack.pop())

    def write_program(self):
        print("Enter instructions:")
        line = input(">").upper()
        while line != "END":
            self.byte_code.append(line)
            line = input(">").upper()

        print("Code:")
        for line in self.byte_code:
            print(line)

        action = input("(R) to run, hit Enter to return to the game").upper()
        if action == 'R':
            print("Executing program...")
            self.run()

    def dump_code(self):
        print("Code:")
        for line in self.source:
            print(line)

    def lex(self):
        # tokenise the source using the standard dis module

        try:
            # first redirect sys.stdout to our own StringIO object
            # this avoids the need for a temporary file to capture the dis
            # output
            token_output = StringIO()
            sys.stdout = token_output
            # dis will output to sys.stdout, which is now redirected
#            dis.dis(self.get_code())
            bytecode = dis.Bytecode(self.get_code())
        except:
            # restore the original stdout
            sys.stdout = sys.__stdout__
            print("BIT found an error in your code!")
            # see https://docs.python.org/3/library/traceback.html
            # for a possible way to have better error handling
            # also https://stackoverflow.com/questions/18176602/printhow-to-get-name-of-exception-that-was-caught-in-python
        finally:
            # restore the original stdout
            sys.stdout = sys.__stdout__

        # output tokens
        print(">>>")
        #print(token_output.getvalue())
        #self.write_program()  # allow simple instructions to be typed in directly
        for instruction in bytecode:
            print(instruction.opname, instruction.argval)

    def run(self):
        # parse source code into executable instructions
        operand_counter = 0
        for line in self.byte_code:
            fragments = line.split()
            # for now this adds every operand to the operand list
            # TODO check if it is already there and reference it, if so
            instruction = (fragments[0], operand_counter)
            self.executable['instructions'].append(instruction)
            if len(fragments) > 1:
                self.executable['values'].append(fragments[1])
                operand_counter += 1
        print(self.executable)  # DEBUG

        # execute instructions
        instructions = self.executable['instructions']  # used as shorthand
        values = self.executable['values']
        for each_step in instructions:
            instruction, argument = each_step
            print("Step:", instruction, argument)
            if instruction == "LOAD":
                number = values[argument]
                self.LOAD(number)
            elif instruction == "ADD":
                self.ADD()
            elif instruction == "PRINT":
                self.PRINT()
