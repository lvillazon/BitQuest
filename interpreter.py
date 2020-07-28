import dis  # built-in python disassembler - used for tokenising
import sys
import traceback

from io import StringIO

from constants import CONSOLE_VERBOSE

def is_a_number(p):
    # check for numeric parameters
    try:
        float(p)
        return True
    except ValueError:
        return False

class Interpreter:
    def __init__(self, dog):
        self.BIT = dog  # a link back to the game state of the dog character
        self.source = []  # a list of lines of source code
        self.byte_code = []
        self.stack = []
        self.executable = {'instructions': [], 'values': []}
        self.f_locals = {}
        self.f_builtins = {'abs': abs,
                           'all': all,
                           'any': any,
                           'ascii': ascii,
                           'bin': bin,
                           'bool': bool,
                           # breakpoint skipped (not implementing a debugged yet!)
                           'bytearray': bytearray,
                           'bytes': bytes,
                           'callable': callable,
                           'chr': chr,
                           'classmethod': classmethod,
                           # compile skipped (inception!)
                           'complex': complex,
                           'delattr': delattr,
                           'dict': dict,
                           # dir skipped
                           'divmod': divmod,
                           

                          
                           
                           'print': self.BIT.say}

    def load(self, source):
        # set the source code to interpret
        self.source = source

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

    ##############################################
    # the functions for the instruction set

    def byte_BINARY_ADD(self):
        # add 2 values
        b = self.pop()
        a = self.pop()
        result = a + b
        self.push(result)

    def byte_BINARY_SUBTRACT(self):
        # subtract 2 values
        b = self.pop()
        a = self.pop()
        result = a - b
        self.push(result)

    def byte_BINARY_MULTIPLY(self):
        # multiply 2 values
        b = self.pop()
        a = self.pop()
        result = a * b
        self.push(result)

    def byte_BINARY_TRUE_DIVIDE(self):
        # divide 2 values
        b = self.pop()
        a = self.pop()
        result = a / b
        self.push(result)

    def byte_CALL_FUNCTION(self, param_count):
        params = self.popn(int(param_count))
        function_name = self.pop()
        if CONSOLE_VERBOSE:
            print("\t trying to call function:", function_name)
            print("\t with parameters:", params)
        self.push(function_name(*params))

    def byte_COMPARE_OP(self, operator):
        b = self.pop()
        a = self.pop()
        result = eval('a' + operator + 'b')
        self.push(result)

    def byte_LOAD_CONST(self, const):
        # add a literal to the stack
        self.push(const)

    def byte_POP_TOP(self):
        self.pop()  # discard top item on the stack?

    def byte_LOAD_NAME(self, name):
        # the LOAD_ and STORE_NAME functions directly manipulate the live variables of the program
        # this will eventually switch to accessing the variables of the current frame
        found = True
        if name in self.f_locals:
            val = self.f_locals[name]
        elif name in self.f_builtins:
            val = self.f_builtins[name]
        else:
            print("NAME ERROR:", name, "is not defined.")
            found = False
        if found:
            self.push(val)

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
        if CONSOLE_VERBOSE:
            r = self.pop()
            print("\t Returning:", r)

    def lex(self):
        # tokenise the source using the standard dis module
        print("Lexing...")
        success = True
        token_list = []
        try:
            # first redirect sys.stdout to our own StringIO object
            # this avoids the need for a temporary file to capture the dis
            # output
            token_output = StringIO()
            sys.stdout = token_output
            # dis will output to sys.stdout, which is now redirected
#            dis.dis(self.get_code())
            token_list = dis.Bytecode(self.get_code())
        except Exception as e:
            # restore the original stdout
            sys.stdout = sys.__stdout__

            # Lexing errors
            error_type = e.args[0]
            error_details = e.args[1]
            error_line = error_details[1]
            # TODO display error message in-game (highlight in the editor?)
            print("BIT found a", end='')
            if error_type[0] in 'aeiouAEIOU':
                print("n", end='')  # correctly deal with a/an situation
            print(" ", error_type, " on line ", error_line, sep='')
            success = False
            # see https://docs.python.org/3/library/traceback.html
            # for a possible way to have better error handling
            # also https://stackoverflow.com/questions/18176602/printhow-to-get-name-of-exception-that-was-caught-in-python
        finally:
            # restore the original stdout
            sys.stdout = sys.__stdout__

        for instruction in token_list:
            if CONSOLE_VERBOSE:
                # list bytecode
                print("\t", instruction.opname, str(instruction.argval))
            self.byte_code.append((instruction.opname, instruction.argval))
        return success

    def run(self):
        # parse and execute the byte code
        success = True
        # parse byte code into separate lists of instructions and operands
        print("Parsing...")
        operand_counter = 0
        for op_code in self.byte_code:
            # for now this adds every operand to the operand list
            # TODO check if it is already there and reference it, if so
            instruction = (op_code[0], operand_counter)
            self.executable['instructions'].append(instruction)
            if len(op_code) > 1:
                self.executable['values'].append(op_code[1])
                operand_counter += 1

        if CONSOLE_VERBOSE:
            # display op-code/operand tuples
            print("Executable:")
            print("\t", self.executable)

        # execute instructions
        print("Executing...")
        instructions = self.executable['instructions']  # namespace shorthand
        values = self.executable['values']
        for each_step in instructions:
            instruction, argument = each_step
            params = values[argument]
            if CONSOLE_VERBOSE:
                print("\t", instruction, values[argument],
                      "Stack =", self.stack)
            '''
            if instruction == 'AAAA':
                # dummy clause to allow all ture instructions to be elifs
                pass
            elif instruction == 'BINARY_ADD':
                self.byte_BINARY_ADD()
            elif instruction == 'BINARY_SUBTRACT':
                self.byte_BINARY_ADD()
            elif instruction == 'BINARY_MULTIPLY':
                self.byte_BINARY_ADD()
            elif instruction == 'BINARY_TRUE_DIVIDE':
                self.byte_BINARY_ADD()
            elif instruction == 'CALL_FUNCTION':
                self.byte_CALL_FUNCTION(params)
            elif instruction == 'LOAD_CONST':
                self.byte_LOAD_CONST(params)
            elif instruction == 'LOAD_NAME':
                self.byte_LOAD_NAME(params)
            elif instruction == 'POP_TOP':
                self.byte_POP_TOP()
            elif instruction == 'STORE_NAME':
                self.byte_STORE_NAME(params)
            elif instruction == 'RETURN_VALUE':
                self.byte_RETURN_VALUE()

            else:
                print("UNRECOGNISED INSTRUCTION:", instruction)
            '''
            parameterless_ops = ('BINARY_ADD',
                                 'BINARY_SUBTRACT',
                                 'BINARY_MULTIPLY',
                                 'BINARY_TRUE_DIVIDE',
                                 'POP_TOP',
                                 'RETURN_VALUE')
            if instruction in parameterless_ops:
                function = 'self.byte_' + instruction + '()'
            else:
                if params is None:
                    # pass None-type parameter explicitly
                    function = 'self.byte_' + instruction + '(None)'
                elif is_a_number(params):
                    # cast numeric parameters to strings
                    function = 'self.byte_' + instruction + '(' + str(params) + ')'
                else:
                    # enclose all other parameters in quotes
                    function = 'self.byte_' + instruction + '("' + params + '")'
            try:
                exec(function)
            except AttributeError:
                print("Undefined byte code:", instruction,
                      "expecting params", params)
                success = False
            if not success:
                return False  # quit execution immediately on undefined op
        return success


