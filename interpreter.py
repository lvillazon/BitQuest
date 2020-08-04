import collections
import dis  # built-in python disassembler - used for tokenising
import inspect
import operator
import sys
import types
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
        """ calling a function creates a new frame on the call stack"""
        '''
        this doesn't work, so I've commented it out for now.
        from what I understand, __slots__ is just a performance optimisation
        __slots__ = [
            'func_code', 'func_name', 'func_defaults', 'func_globals',
            'func_locals', 'func_dict', 'func_closure',
            '__name__', '__dict__', '__doc__',
            '_vm', '_func',
        ]
'''

        def __init__(self, name, code, globs, defaults, closure, vm):
            """ opaque stuff copied directly from Allison Kaptur"""
            self._vm = vm
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
            """ constructs and runs the call frame """
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


class VirtualMachineError(Exception):
    pass


class VirtualMachine:
    def __init__(self, world):
        self.world = world  # link back to the state of the game world
        self.BIT = world.dog  # shortcut to the game state of the dog character
        self.source = []  # a list of lines of source code
        self.frames = []  # the call stack of frames
        self.frame = None  # current frame
        self.return_value = None
        self.last_exception = None
        self.compile_time_error = None
        self.run_time_error = None
        self.byte_code = None
        self.stack = []
        self.running = False  # true when a program is executing
        self.overridden_builtins = {
            # functions that replace the standard python functions
            'print': self.BIT.say
        }

    def load(self, source):
        # set the source code to interpret
        self.source = source

    def is_running(self):
        return self.running

    def halt(self):
        """halts execution immediately"""
        self.running = False

    def run(self, global_names=None, local_names=None):
        """ creates an entry point for code execution on the vm"""

        if self.byte_code:
            print('Executing...')
            self.running = True
            frame = self.make_frame(self.byte_code, global_names=global_names,
                                    local_names=local_names)
            result = self.run_frame(frame)
            if result in ('exception', 'quit'):
                return False
            else:
                return True
        else:
            self.running = False  # no bytecode to execute

    def make_frame(self, code, callargs=None,
                   global_names=None, local_names=None):
        if callargs is None:
            callargs = {}
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
        """unwind the values on the data stack
        corresponding to a given block"""
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
        """ parse the bytecode instruction
        if the instruction has no arguments, it is a single byte long
        instructions with arguments are 3 bytes long - argument = 2 bytes """
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
            arg_val = f.code_obj.co_code[f.last_instruction]
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

        f.last_instruction += 1
        return byte_name, argument

    def dispatch(self, byte_name, argument):
        """ the python equivalent of CPython's 1500-line switch statement
        each byte name is assigned to its corresponding method.
        Exceptions are caught and set on the VM"""

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
                    # raise VirtualMachineError(
                    #    "unsupported bytecode type: %s" % byte_name
                    # )
                    print("BIT doesn't recognise the bytecode", byte_name)
                    stack_unwind_reason = 'quit'
            else:
                stack_unwind_reason = bytecode_fn(*argument)
        except:
            # handles run-time errors while executing the code
            self.last_exception = sys.exc_info()[:2] + (None,)
            stack_unwind_reason = 'exception'

        return stack_unwind_reason

    def run_frame(self, frame):
        """ frames run until they return a value or raise an exception"""
        self.push_frame(frame)
        while self.running:
            self.world.update()
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
        elif stack_unwind_reason == 'quit':
            # this option allows us to quit gracefully
            # with a console error that doesn't crash the game
            # It should only be used for errors that just affect the
            # in-game program
            return 'quit'  # propagate the return value up the call stack

        return self.return_value

    def update(self):
        """ continue executing the current program"""

    def jump(self, target):
        """Set bytecode pointer to "target", so this instruction is next"""
        self.frame.last_instruction = target

    ##############################################
    # the functions for the instruction set

    BINARY_OPERATORS = {
        'POWER': pow,
        'MULTIPLY': operator.mul,
        'FLOOR_DIVIDE': operator.floordiv,
        'TRUE_DIVIDE': operator.truediv,
        'MODULO': operator.mod,
        'ADD': operator.add,
        'SUBTRACT': operator.sub,
        'SUBSCR': operator.getitem,
        'LSHIFT': operator.lshift,
        'RSHIFT': operator.rshift,
        'AND': operator.and_,
        'XOR': operator.xor,
        'OR': operator.or_,
    }

    def binaryOperator(self, op):
        # handles all the operations that take the form 'a [op] b', eg 2 + 4
        a, b = self.popn(2)
        self.push(self.BINARY_OPERATORS[op](a, b))

    def byte_CALL_FUNCTION(self, param_count):
        params = self.popn(int(param_count))
        function_name = self.pop()
        if CONSOLE_VERBOSE:
            print("\t trying to call function:", function_name)
            print("\t with parameters:", params)
        self.push(function_name(*params))

    COMPARE_OPERATORS = [
        operator.lt,
        operator.le,
        operator.eq,
        operator.ne,
        operator.gt,
        operator.ge,
        lambda x, y: x in y,
        lambda x, y: x not in y,
        lambda x, y: x is y,
        lambda x, y: x is not y,
        lambda x, y: issubclass(x, Exception) and issubclass(x, y),
    ]

    def byte_COMPARE_OP(self, opnum):
        a, b = self.popn(2)
        self.push(self.COMPARE_OPERATORS[opnum](a, b))

    def byte_JUMP_FORWARD(self, target):
        self.jump(target)

    def byte_JUMP_ABSOLUTE(self, target):
        self.jump(target)

    """
    def byte_LOAD_ATTR(self, attr):
        obj = self.pop()
        val = getattr(obj, attr)
        self.push(val)
    """

    def byte_LOAD_CONST(self, const):
        # add a literal to the stack
        self.push(const)

    def byte_LOAD_FAST(self, name):
        if name in self.frame.local_names:
            val = self.frame.local_names[name]
            self.push(val)
        else:
            print("NAME ERROR:", name, "referenced before assignment.")

    def byte_LOAD_GLOBAL(self, name):
        frame = self.frame
        found = True
        if name in frame.global_names:
            val = frame.global_names[name]
        elif name in self.overridden_builtins:
            val = self.overridden_builtins[name]
        elif name in frame.builtin_names:
            val = frame.builtin_names[name]
        else:
            print("NAME ERROR: global '", name, "' is not defined.", sep='')
            found = False
        if found:
            self.push(val)

    def byte_LOAD_NAME(self, name):
        # the LOAD_ and STORE_NAME functions directly manipulate the
        # live variables of the program
        # this will eventually switch to accessing the variables of the
        # current frame
        frame = self.frame
        found = True
        if name in frame.local_names:
            val = frame.local_names[name]
        elif name in frame.global_names:
            val = frame.globals[name]
        elif name in self.overridden_builtins:
            val = self.overridden_builtins[name]
        elif name in frame.builtin_names:
            val = frame.builtin_names[name]
        else:
            print("NAME ERROR: '", name, "' is not defined.", sep='')
            found = False
        if found:
            self.push(val)

    def byte_POP_JUMP_IF_FALSE(self, target):
        val = self.pop()
        if not val:
            self.jump(target)

    def byte_POP_JUMP_IF_TRUE(self, target):
        val = self.pop()
        if val:
            self.jump(target)

    def byte_POP_TOP(self):
        self.pop()  # discard top item on the stack?

    def byte_RETURN_VALUE(self):
        if CONSOLE_VERBOSE:
            r = self.top()  # look at the top of stack, but don't pop it
            print("\t Returning:", r)
        self.return_value = self.pop()
        return 'return'  # set the value of stack_unwind_reason

    """
    def byte_STORE_ATTR(self, name):
        val, obj = self.popn(2)
        setattr(obj, name, val)
"""

    def byte_STORE_NAME(self, name):
        self.frame.local_names[name] = self.pop()

    def byte_STORE_FAST(self, name):
        self.frame.local_names[name] = self.pop()

    def get_code(self):
        # converts all the source into a single string with carriage returns
        return chr(13).join(self.source)

    def compile(self):
        # built bytecode from the source using compile
        # and display the dissassembled instructions using dis

        print("Lexing...")
        success = True
        token_list = []
        try:
            code_object = compile(self.get_code(), '', 'exec')
            token_list = dis.get_instructions(code_object)
        except Exception as e:
            # handle lexing errors
            error_type = e.args[0]
            error_details = e.args[1]
            error_line = error_details[1]
            # TODO display error message in-game (highlight in the editor?)
            self.compile_time_error = {'error': error_type,
                                       'line': error_line
                                       }
            success = False
            # see https://docs.python.org/3/library/traceback.html
            # for a possible way to have better error handling
            # also https://stackoverflow.com/questions/18176602/printhow-to-get-name-of-exception-that-was-caught-in-python

        if success:
            unrecognised = []
            for instruction in token_list:
                if CONSOLE_VERBOSE:
                    # list bytecode
                    print("\t", instruction.opname, str(instruction.argval))
                # check that the instructions are all defined
                defined = False
                bytecode_fn = getattr(self,
                                      'byte_%s' % instruction.opname, None)
                if bytecode_fn is not None:
                    defined = True
                elif (instruction.opname.startswith('BINARY_') and
                      instruction.opname[7:] in self.BINARY_OPERATORS.keys()):
                    defined = True

                if not defined:
                    unrecognised.append(instruction.opname)
            if unrecognised:
                print("UNDEFINED BYTECODE INSTRUCTIONS:")
                for i in unrecognised:
                    print("\t%s" % i)
                success = False

#                    if byte_name.startswith('UNARY_'):
#                        self.unaryOperator(byte_name[6:])
#                    elif byte_name.startswith('BINARY_'):
#                        self.binaryOperator(byte_name[7:])
#                    else:
                        # raise VirtualMachineError(
                        #    "unsupported bytecode type: %s" % byte_name
                        # )
#                        print("BIT doesn't recognise the bytecode", byte_name)
#                        stack_unwind_reason = 'quit'
#                else:
#                    stack_unwind_reason = bytecode_fn(*argument)

        if success:
            self.byte_code = code_object
            print('Compiling:')  # actually it was compiled earlier, but nvm
            print('\t', end='')
            for c in code_object.co_code:
                print(c, ', ', sep='', end='')
            print()

        return success
