'''
Language parser for Ada.
'''

import re
from .code_reader import CodeStateMachine, CodeReader


class AdaReader(CodeReader):
    '''This is the reader for Ada.'''

    ext = ['adb', 'ads']
    language_names = ['ada']

    _conditions = { 'if', 'elsif', 'else', 'for', 'while', 'select', 'and', 'or', 'xor', 'case', 'when' }

    _keywords = {
        'abort', 'abs', 'abstract', 'accept', 'access', 'aliased', 'all', 'and', 'array', 'at', 'begin', 'body', 'case', 'constant',
        'declare', 'delay', 'delta', 'digits', 'do', 'else', 'elsif', 'end', 'entry', 'exception', 'exit', 'for', 'function',
        'generic', 'goto', 'if', 'in', 'interface', 'is', 'limited', 'loop', 'mod', 'new', 'not', 'null', 'of', 'or', 'others',
        'out', 'overriding', 'package', 'pragma', 'private', 'procedure', 'protected', 'raise', 'range', 'record', 'rem', 'renames',
        'requeue', 'return', 'reverse', 'select', 'separate', 'subtype', 'synchronized', 'tagged', 'task', 'terminate', 'then',
        'type', 'until', 'use', 'when', 'while', 'with', 'xor'
    }

    def __init__(self, context):
        super().__init__(context)
        self.macro_disabled = False
        self.parallel_states = [AdaStates(context, self)]

    @staticmethod
    def generate_tokens(source_code, addition='', token_class=None):
        _until_end = r'(?:\\\n|[^\n])*'
        # block_endings = '|'.join(r'END\s*{0}'.format(_) for _ in AdaReader._blocks)
        # Include all patterns and the (?i) flag in addition
        addition = (
            r'|--' + _until_end + r'|'
            r'package\s+body'
            # + addition
            # + block_endings
            + addition
        )
        print(addition)
        return CodeReader.generate_tokens(
            source_code, addition=addition, token_class=token_class)
    
    def preprocess(self, tokens):
        for token in tokens:
            if token.isspace() and token != '\n':
                continue
            if token.lower() in self._keywords:
                yield token.lower()
            else:
                yield token


    def get_comment_from_token(self, token):
        if token.startswith("--"):
            return token


class AdaStates(CodeStateMachine):
    _ends = re.compile(
        '|'.join(r'END\s*{0}'.format(_) for _ in []), re.I)

    SUBPROGRAM_TOKENS = { 'function', 'procedure' }
    NESTING_KEYWORDS = { 'then', 'do', 'loop' }
    PACKAGE_TOKENS = { 'package', 'package body' }
    ELSE_KEYWORDS = { 'elsif', 'else' }
    TRIVIAL_END_KEYWORDS = { 'if', 'loop', 'case' }

    def __init__(self, context, reader):
        super().__init__(context)
        self.reader = reader
        self.last_token = None
        self._nested_functions = 0

    def __call__(self, token, reader=None):
        if self.reader.macro_disabled:
            return
        if self._state(token):
            self.next(self.saved_state)
            if self.callback:
                self.callback()
        self.last_token = token
        if self.to_exit:
            return True

    # todo: tasks
    def _state_global(self, token):
        token_lower = token.lower()
        if token_lower in self.SUBPROGRAM_TOKENS:
            self._state = self._subprogram
        elif token_lower in self.NESTING_KEYWORDS:
            self._state = self._then
        elif token_lower == 'end':
            self._state = self._end
        elif token_lower in self.PACKAGE_TOKENS:
            self._state = self._package
        elif token_lower == 'begin':
            self._state = self._begin
        elif token_lower in self.ELSE_KEYWORDS:
            self.next(self._else, token)
        elif token_lower == 'task':
            self._state = self._task
        elif token_lower == ';':
            self.reset_state()

    def _subprogram(self, token):
        self.next(self._subprogram_name, token)

    def _subprogram_name(self, token):
        self.context.push_new_function(token)
        self._state = self._expect_subprogram_params


    def _expect_subprogram_params(self, token):
        if token == '(':
            self.next(self._subprogram_params, token)
        else:
            self.next(self._subprogram_defn, token)

    def _subprogram_defn(self, token):
        if token in [ 'with', 'return' ]:
            pass
        elif token == 'is':
            self.next(self._subprogram_decl, token)
        elif token == ';':
            self.context.end_of_function()
            self.reset_state(token)

    def _subprogram_decl(self, token):
        if token == 'begin':
            self.next(self._begin_subprogram, token)
        elif token == 'end':
            self.next(self._end, token)
        elif token in self.SUBPROGRAM_TOKENS:
            self._nested_functions += 1
            self._state = self._subprogram

    @CodeStateMachine.read_inside_brackets_then('()', '_subprogram_defn')
    def _subprogram_params(self, token):
        self.context.parameter(token)

    def reset_state(self, token=None):
        self._state = self._state_global
        self._fun_name = None
        if token is not None:
            self._state_global(token)

    def _ignore_next(self, token):
        self.reset_state()

    def _begin_subprogram(self, token):
        self.reset_state()

    def _begin(self, token):
        self.context.add_bare_nesting()
        self.reset_state()

    def _else(self, token):
        if token == 'elsif':
            self._pop_bare_nesting()
        self.reset_state()

    def _then(self, token):
        self.context.add_bare_nesting()
        self.reset_state()

    def _package(self, token):
        if token == 'body':
            pass
        elif token == 'is':
            # Packages also have 'end' and their nesting needs to be tracked
            self.context.add_bare_nesting()
            self.reset_state()
        else:
            self.context.add_namespace(token)

    def _task_name(self, token):
        self.context.push_new_function(token)
        self.next(self._task_body, token)

    def _task_body(self, token):
        if token == 'body':
            self._state = self._task_name
        elif token == 'begin':
            self.next(self._begin_subprogram, token)
        else:
            # Ignoring everything else
            pass

    def _task(self, token):
        if token == 'body':
            self.next(self._task_body, token)
        else:
            self.reset_state()

    def _end(self, token):
        if token in self.TRIVIAL_END_KEYWORDS:
            self._pop_bare_nesting()
        else:
            self._pop_function_if_exists()

    def _pop_bare_nesting(self):
        if self.context.nesting_stack:
            self.context.nesting_stack.pop()

        self.reset_state()        
        
    def _pop_function_if_exists(self):
        if self.context.current_nesting_level == 0:
            self.context.end_of_function()
            if self._nested_functions > 0:
                self._nested_functions -= 1
                self._state = self._subprogram_decl
                return
        else:
            self.context.nesting_stack.pop()

        self.reset_state()
