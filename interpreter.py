import collections
import dis  # built-in python disassembler - used for tokenising
import inspect
import sys
import traceback
import types

from io import StringIO

from constants import CONSOLE_VERBOSE

def is_a_number(p):
    # check for numeric parameters
    try:
        float(p)
        return True
    except ValueError:
        return False

class Frame(object):
    # data structure to represent the call frames
    def __init__(self, code_obj, global_names, local_names, prev_frame):
        self.code_obj = code_obj
        self.global_names = global_names
        self.local_names = local_names
        self.prev_frame = prev_frame
        self.stack = []
        if prev_frame:
            self.builtin_names = prev_frame.builtin_names
        else:
            self.builtin_names = local_names['__builtins__']
            if hasattr(self.builtin_names, '__dict__'):
                self.builtin_names = self.builtin_names.__dict__

        self.last_instruction = 0
        self.block_stack = []

    class Function(object):
        ''' calling a function creates a new frame on the call stack'''
        '''
        __slots__ = [
            'func_code', 'func_name', 'func_defaults', 'func_globals',
            'func_locals', 'func_dict', 'func_closure',
            '__name__', '__dict__', '__doc__',
            '_vm', '_func',
        ]
'''

        def __init__(self, name, code, globs, defaults, closure, vm):
            ''' opaque stuff copied directly from Allison Kaptur'''
            self.vm = vm
            self.func_code = code
            self.func_name = self.__name__ = name or code.co_name
            self.func_defaults = tuple(defaults)
            self.func_globals = globs
            self.func_locals = self._vm.frame.f_locals
            self.__dict__ = {}
            self.func_closure = closure
            self.__doc__ = code.co_consts[0] if code.co_consts else None

            # sometimes we need a 'real' Python function. This is for that
            kw = {
                'argdefs': self.func_defaults,
            }
            if closure:
                kw['closure'] = tuple(make_cell(0) for _ in closure)
            self._func = types.FunctionType(code, globs, **kw)

        def __call__(self, *args, **kwargs):
            ''' constructs and runs the call frame '''
            callargs = inspect.getcallargs(self._func, *args, **kwargs)
            # callargs provides a mapping of arguments to pass into the frame
            frame = self._vm.make_frame(
                self.func_code, callargs, self.func_globals, {}
            )
            return self._vm.run_frame(frame)

def make_cell(value):
    """Create a real Python closure and grab a cell."""
    # I have no idea what is going on here and neither does AK!
    # Thanks to Alex Gaynor for help with this bit of twistiness.
    fn = (lambda x: lambda: x)(value)
    return fn.__closure__[0]

# data structure to handle loop and exception blocks
Block = collections.namedtuple('Block', ['type', 'handler', 'stack_height'])


class VirtualMachine:
    def __init__(self, dog):
        self.BIT = dog  # a link back to the game state of the dog character
        self.source = []  # a list of lines of source code
        self.frames = []  # the call stack of frames
        self.frame = None  # current frame
        self.return_value = None
        self.last_exception = None
        # do we need the stuff below? or has it been moved to frames etc
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

    def run(self, global_names=None, local_names=None):
        ''' creates an entry point for code execution on the vm'''
        frame = self.make_frame(self.source, global_names=global_names,
                                local_names=local_names)
        self.run_frame(frame)

    def make_frame(self, code, callargs={},
                   global_names=None, local_names=None):
        if global_names is not None and local_names is not None:
            local_names = global_names
        elif self.frames:
            global_names = self.frame.global_names
            local_names = {}
        else:
            global_names = local_names = {
                '__builtins__': __builtins__,
                '__name__': '__main__',
                '__doc__': None,
                '__package__': None,
            }
        local_names.update(callargs)
        frame = Frame(code, global_names, local_names, self.frame)
        return frame

    def push_frame(self, frame):
        self.frames.append(frame)
        self.frame = frame

    def pop_frame(self):
        self.frames.pop()
        if self.frames:
            self.frame = self.frames[-1]
        else:
            self.frame = None

    def run_frame(self):
        pass

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

    # Block stack manipulation
    def push_block(self, b_type, handler=None):
        stack_height = len(self.frame.stack)
        self.frame.block_stack.append(Block(b_type, handler, stack_height))

    def pop_block(self):
        return self.frame.block_stack.pop()

    def unwind_block(self, block):
        '''unwid the values on the data stack corresponding to a given block'''
        if block.type == 'except-handler':
            # the exception type, value and traceback are already on the stack
            offset = 3
        else:
            offset = 0

        while len(self.frame.stack) > block.level + offset:
            self.pop()

        if block.type == 'except-handler':
            traceback, value, exctype = self.popn(3)
            self.last_exception = exctype, value, traceback

        def manage_block_stack(self, stack_unwind_reason):
            frame = self.frame
            block = frame.block_stack[-1]
            if block.type == 'loop' and stack_unwind_reason == 'continue':
                self.jump(self.return_value)
                stack_unwind_reason = None
                return stack_unwind_reason

            self.pop_block()
            self.unwind_block(block)

            if block.type == 'loop' and stack_unwind_reason == 'break':
                stack_unwind_reason = None
                self.jump(block.handler)
                return stack_unwind_reason

            if (block.type in ['setup-except', 'finally'] and
                stack_unwind_reason == 'exception'):
                exctype, value, tb = self.last_exception
                self.push(tb, value, exctype)
                self.push(tb, value, exctype)  # needs to be twice (but why??)
                stack_unwind_reason = None
                self.jump(block.handler)
                return stack_unwind_reason
            elif block.type == 'finally':
                if stack_unwind_reason in ('return', 'continue'):
                    self.push(self.return_value)

                self.push(stack_unwind_reason)
                stack_unwind_reason = None
                self.jump(block.handler)
                return stack_unwind_reason
            return stack_unwind_reason

    def parse_byte_and_args(self):
        ''' parse the bytecode instruction
        if the instruction has no arguments, it is a single byte long
        instructions with arguments are 3 bytes long - argument = 2 bytes '''
        f = self.frame  # for brevity
        op_offset = f.last_instruction
        byte_code = f.code_obj.co_code[op_offset]
        f.last_instruction += 1
        byte_name = dis.opname[byte_code]

        # this uses the lists included in the dis module to check the meaning
        # of the arguments for each instruction. There are only a few
        # different possibilities and this approach is much more concise
        # than exhaustively testing for each individual instruction
        if byte_code >= dis.HAVE_ARGUMENT:
            # index into the byte code
            arg = f.code_obj.co_code[f.last_instruction:f.last_instruction+2]
            f.last_instruction += 2  # advance instruction pointer
            arg_val = arg[0] + (arg[1] * 256)
            if byte_code in dis.hasconst:  # look up a constant
                arg = f.code_obj.co_consts[arg_val]
            elif byte_code in dis.hasname:  # look up a name
                arg = f.code_obj.co_names[arg_val]
            elif byte_code in dis.haslocal:  # look up a local name
                arg = f.code_obj.co_var_names[arg_val]
            elif byte_code in dis.hasjrel:  # calculate relative jump
                arg = f.last_instruction + arg_val
            else:
                arg = arg_val
            argument = [arg]
        else:
            argument = []

        return byte_name, argument

    def dispatch(self, byte_name, argument):
        ''' the python equivalent of CPython's 1500-line switch statement
        each byte name is assigned to its corresponding method.
        Exceptions are caught and set on the VM'''

        # this state variable keeps track of what the interpreter was doing
        # when the operation completes - this is important to maintain the
        # integrity of the data and block stacks.
        # the possible values are None, continue, break, return and exception
        stack_unwind_reason = None  # the normal case
        try:
            bytecode_fn = getattr(self, 'byte_%s' % byte_name, None)
            if bytecode_fn is None:
                if byte_name.startswith('UNARY_'):
                    self.unaryOperator(byte_name[6:])
                elif byte_name.startswith('BINARY_'):
                    self.binaryOperator(byte_name[7:])
                else:
                    self.VirtualMachineError(
                        "unsupported bytecode type: %s" % byte_name
                    )
            else:
                stack_unwind_reason = bytecode_fn(*argument)
        except:
            # handles run-time errors while executing the code
            self.last_exception = sys.exec_info()[:2] + (None,)
            stack_unwind_reason = 'exception'

        return stack_unwind_reason

    def run_frame(self, frame):
        ''' frames run until they return a value or raise an exception'''
        self.push_frame(frame)
        while True:
            byte_name, arguments = self.parse_byte_and_args()
            stack_unwind_reason = self.dispatch(byte_name, arguments)

            # block management
            while stack_unwind_reason and frame.block_stack:
                stack_unwind_reason = \
                    self.manage_block_stack(stack_unwind_reason)
                if stack_unwind_reason:
                    break

            self.pop_frame()

            if stack_unwind_reason == 'exception':
                exc, val, tb = self.last_exception
                e = exc(val)
                e.__traceback__ = tb
                raise e

            return self.return_value


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
            # the LOAD_ and STORE_NAME functions directly manipulate the
            # live variables of the program
            # this will eventually switch to accessing the variables of the
            # current frame
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



#    def add_code(self, line):
#        # add a single line of code to the interpreter's source
#        self.source.append(line)

    def get_code(self):
        # converts all the source into a single string with carriage returns
        return chr(13).join(self.source)


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

    def old_run(self):
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


