import dis  # built-in python disassembler - used for tokenising
import sys

from io import StringIO


class Interpreter:
    def __init__(self, source):
        self.source = source  # a list of lines of source code
        self.byte_code = []
        self.stack = []
        self.executable = {'instructions': [], 'values': []}
        self.f_locals = {}

    # Data stack manipulation
    def top(self):
        return self.stack[-1]

    def pop(self):
        return self.stack.pop()

    def push(self, *vals):
        self.stack.extend(vals)

    def popn(self, n):
        """Pop a number of values from the value stack.
        A list of `n` values is returned, the deepest value first.
        """
        if n:
            ret = self.stack[-n:]
            self.stack[-n:] = []
            return ret
        else:
            return []

    def add_code(self, line):
        # add a single line of code to the interpreter's source
        self.source.append(line)

    def get_code(self):
        # converts all the source into a single string with carriage returns
        return chr(13).join(self.source)

    # the functions for the instruction set
    def byte_LOAD_CONST(self, const):
        # add a literal to the stack
        self.push(const)

    def byte_POP_TOP(self):
        self.pop()  # discard top item on the stack?

    def byte_LOAD_NAME(self, name):
        # the LOAD_ and STORE_NAME functions directly manipulate the live variables of the program
        # this will eventually switch to accessing the vaiables of the current frame
        if name in self.f_locals:
            val = self.f_locals[name]
            self.push(val)
        else:
            print("NAME ERROR:", name, "is not defined.")

    def byte_STORE_NAME(self, name):
        self.f_locals[name] = self.pop()

    def byte_LOAD_FAST(self, name):
        if name in self.f_locals:
            val = self.f_locals[name]
            self.push(val)
        else:
            print("NAME ERROR:", name, "referenced before assignment.")

    def byte_STORE_FAST(self, name):
        self.f_locals[name] = self.pop()

    def byte_RETURN_VALUE(self):
        print("Returning", self.pop())

#### legacy op codes for the much simpler proof-of-concept
    def ADD(self):
        # pop the top 2 values, add them and push the result
        first_num = self.stack.pop()
        second_num = self.stack.pop()
        self.stack.append(int(first_num) + int(second_num))

    def PRINT(self):
        # pop a value and output to console
        print(self.stack.pop())

    def write_program(self):
        # allow simple instructions to be typed in directly
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
        print("Lexing:")
        try:
            # first redirect sys.stdout to our own StringIO object
            # this avoids the need for a temporary file to capture the dis
            # output
            token_output = StringIO()
            sys.stdout = token_output
            # dis will output to sys.stdout, which is now redirected
#            dis.dis(self.get_code())
            token_list = dis.Bytecode(self.get_code())
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

        # DEBUG output the bytecode instructions
        for instruction in token_list:
            print(instruction.opname, instruction.argval)

        #print("Parsing:")
        # parse bytecode into separate lists of instructions and operands
        #for instruction in bytecode:
        #    self.executable['instructions'].append(instruction.opname)
        #    self.executable['values'].append(instruction.argval)
        #print(self.executable)  # DEBUG
        print("Building opcode strings:")
        for instruction in token_list:
            self.byte_code.append(instruction.opname + " " + str(instruction.argval))
        print(self.byte_code)

    def run(self):
        # parse source code into separate lists of instructions and operands
        print("Parsing:")
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
        print("Executable:")
        print(self.executable)

        # execute instructions
        print("Executing:")
        instructions = self.executable['instructions']  # used as shorthand
        values = self.executable['values']
        for each_step in instructions:
            instruction, argument = each_step
            print("Step:", instruction, argument)
            if instruction == "LOAD_CONST":
                number = values[argument]
                self.byte_LOAD_CONST(number)
            elif instruction == "STORE_NAME":
                name = values[argument]
                self.byte_STORE_NAME(name)
            elif instruction == "RETURN_VALUE":
                self.byte_RETURN_VALUE()
            else:
                print("UNRECOGNISED INSTRUCTION:", instruction)
