#!/usr/bin/env python
from __future__ import generators

"""
Parts of this tool is software cribbed from the PLY C preprocessor example.
The code is free to use under the terms of the PLY license as long as I include
the following copyright statement:

David Beazley (http://www.dabeaz.com)
Copyright (C) 2007
All rights reserved
"""

"""
HLAKit
Copyright (c) 2010 David Huseby. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY DAVID HUSEBY `AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL DAVID HUSEBY OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of David Huseby.
"""

import copy
import os.path
import re
import sys
import time
import ply.lex as lex

preprocessor = {
    'define':       'PP_DEFINE',
    'undef':        'PP_UNDEF',
    'ifdef':        'PP_IFDEF',
    'ifndef':       'PP_IFNDEF',
    'else':         'PP_ELSE',
    'endif':        'PP_ENDIF',
    'include':      'PP_INCLUDE'
    }

compiler = {
    'incbin':       'CP_INCBIN',
    'todo':         'CP_TODO',
    'warning':      'CP_WARNING',
    'error':        'CP_ERROR',
    'fatal':        'CP_FATAL'
    }

linker = {
    'ram':          'LP_RAM',
    'rom':          'LP_ROM',
    'org':          'LP_ORG',
    'end':          'LP_END',
    'banksize':     'LP_BANKSIZE',
    'bank':         'LP_BANK',
    'setpad':       'LP_SET_PAD',
    'align':        'LP_ALIGN'
    }

reserved = {
    'byte':         'TYPE',
    'char':         'TYPE',
    'bool':         'TYPE',
    'word':         'TYPE',
    'dword':        'TYPE',
    'pointer':      'TYPE',
    'struct':       'STRUCT',
    'typedef':      'TYPEDEF',
    'shared':       'SHARED',
    'noreturn':     'NORETURN',
    'return':       'RETURN',
    'inline':       'INLINE',
    'function':     'FUNCTION',
    'interrupt':    'INTERRUPT',
    'lo':           'LO',
    'hi':           'HI',
    'sizeof':       'SIZEOF',
    'if':           'IF',
    'else':         'ELSE',
    'while':        'WHILE',
    'do':           'DO',
    'forever':      'FOREVER',
    'switch':       'SWITCH',
    'case':         'CASE',
    'default':      'DEFAULT',
    'reg':          'REG',
    'near':         'NEAR',
    'far':          'FAR'
    }

conditionals = {
    'is':           'IS',
    'has':          'HAS',
    'no':           'NO',
    'not':          'NOT',
    'plus' :        'POSITIVE',
    'positive':     'POSITIVE',
    'minus':        'NEGATIVE',
    'negative':     'NEGATIVE',
    'greater':      'GREATER',
    'less':         'LESS',
    'overflow':     'OVERFLOW',
    'carry':        'CARRY',
    'nonzero':      'TRUE',
    'set':          'TRUE',
    'true':         'TRUE',
    '1':            'TRUE',
    'zero':         'FALSE',
    'unset':        'FALSE',
    'false':        'FALSE',
    '0':            'FALSE',
    'clear':        'FALSE',
    'equal':        'EQUAL'
    }

tokens = [  'STRING', 
            'DECIMAL', 
            'KILO', 
            'HEXC', 
            'HEXS', 
            'BINARY', 
            'HASH',
            'DHASH',
            'RSHIFT',
            'LSHIFT',
            'GTE',
            'LTE',
            'NE',
            'EQ',
            'ID',
            'WS',
            'COMMENT' ] \
            + list(set(preprocessor.values())) \
            + list(set(compiler.values())) \
            + list(set(linker.values())) \
            + list(set(reserved.values())) \
            + list(set(conditionals.values()))


literals = '.+-*/~!%><=&^|{}()[]:,'

# pp hash marks
t_HASH = r'\#'
t_DHASH = r'\#\#'

# compilter values and operators
t_STRING    = r'\"(\\.|[^\"])*\"'
t_DECIMAL   = r'(0|[1-9][0-9]*)'
t_KILO      = r'(0|[1-9][0-9]*)[kK]'
t_HEXC      = r'0x[0-9a-fA-F]+'
t_HEXS      = r'\$[0-9a-fA-F]+'
t_BINARY    = r'%[01]+'
t_RSHIFT    = r'>>'
t_LSHIFT    = r'<<'
t_GTE       = r'>='
t_LTE       = r'<='
t_NE        = r'!='
t_EQ        = r'=='

# whitespace handler
def t_WS(t):
    r'\s+'
    t.lexer.lineno += t.value.count("\n")
    return t

# identifier
def t_ID(t):
    r'[a-zA-Z_][\w]*'
    t.type = preprocessor.get(t.value.lower(), None) # check for preprocessor words
    if t.type != None:
        t.value = t.value.lower()
    else:
        t.type = compiler.get(t.value.lower(), None) # check for reserved words
        if t.type != None:
            t.value = t.value.lower()
        else:
            t.type = linker.get(t.value.lower(), None) # check for reserved words
            if t.type != None:
                t.value = t.value.lower()
            else:
                t.type = reserved.get(t.value.lower(), None) # check for reserved words
                if t.type != None:
                    t.value = t.value.lower()
                else:
                    t.type = conditionals.get(t.value.lower(), None) # check for conditionals
                    if t.type != None:
                        t.value = t.value.lower()
                    else:
                        t.type = 'ID'
    return t

def t_COMMENT(t):
    r'(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)|(//.*)'
    t.lexer.lineno += t.value.count("\n")
    return t

def t_error(t):
    t.type = t.value[0]
    t.value = t.value[0]
    t.lexer.skip(1)
    return t

# ------------------------------------------------------------------
# Scope object
#
# This object holds a stack of contexts containing k/v pairs
# ------------------------------------------------------------------

class Scope(object):
    def __init__(self, name, initial={}):
        self._ctxs = [ initial ]
        self._names = [ name ]

    def push(self, name, initial={}):
        self._ctxs.append( initial )
        self._names.append( name )

    def pop(self):
        self._ctxs.pop()
        self._names.pop()

    def name(self):
        return self._names[-1]

    def names(self):
        return self._names

    def scope(self):
        return ' => '.join(self._names)

    def __getitem__(self, key):
        return self._ctxs[-1].__getitem__(key)

    def __setitem__(self, key, value):
        return self._ctxs[-1].__setitem__(key, value)
    
    def __delitem__(self, key):
        return self._ctxs[-1].__delitem__(key)

    def keys(self):
        return self._ctxs[-1].keys()


# ------------------------------------------------------------------
# Macro object
#
# This object holds information about preprocessor macros
#
#    .name      - Macro name (string)
#    .value     - Macro value (a list of tokens)
#    .arglist   - List of argument names
#    .variadic  - Boolean indicating whether or not variadic macro
#    .vararg    - Name of the variadic parameter
#
# When a macro is created, the macro replacement token sequence is
# pre-scanned and used to create patch lists that are later used
# during macro expansion
# ------------------------------------------------------------------

class Macro(object):
    def __init__(self,name,value,arglist=None,variadic=False):
        self.name = name
        self.value = value
        self.arglist = arglist
        self.variadic = variadic
        if variadic:
            self.vararg = arglist[-1]
        self.source = None

# ------------------------------------------------------------------
# FrontEnd object
#
# Object representing a compiler.  Contains macro definitions,
# include directories, and other information and handles lexing and
# parsing.
# ------------------------------------------------------------------

class FrontEnd(object):
    def __init__(self,lexer=None):
        if lexer is None:
            lexer = lex.lexer
        self.lexer = lexer
        self.macros = { }
        self.path = []
        self.temp_path = []

        # Probe the lexer for selected tokens
        self.lexprobe()

        tm = time.localtime()
        self.define("__DATE__ \"%s\"" % time.strftime("%b %d %Y",tm))
        self.define("__TIME__ \"%s\"" % time.strftime("%H:%M:%S",tm))
        self.parser = None

    # -----------------------------------------------------------------------------
    # tokenize()
    #
    # Utility function. Given a string of text, tokenize into a list of tokens
    # -----------------------------------------------------------------------------

    def tokenize(self,text):
        tokens = []
        self.lexer.input(text)
        while True:
            tok = self.lexer.token()
            if not tok: break
            tokens.append(tok)
        return tokens

    # ---------------------------------------------------------------------
    # error()
    #
    # Report a preprocessor error/warning of some kind
    # ----------------------------------------------------------------------

    def error(self,file,line,msg):
        print("%s:%d %s" % (file,line,msg))

    # ----------------------------------------------------------------------
    # lexprobe()
    #
    # This method probes the preprocessor lexer object to discover
    # the token types of symbols that are important to the preprocessor.
    # If this works right, the preprocessor will simply "work"
    # with any suitable lexer regardless of how tokens have been named.
    # ----------------------------------------------------------------------

    def lexprobe(self):

        # Determine the token type for identifiers
        self.lexer.input("identifier")
        tok = self.lexer.token()
        if not tok or tok.value != "identifier":
            print("Couldn't determine identifier type")
        else:
            self.t_ID = tok.type

        # Determine the token type for integers
        self.lexer.input("12345")
        tok = self.lexer.token()
        if not tok or int(tok.value) != 12345:
            print("Couldn't determine integer type")
        else:
            self.t_INTEGER = tok.type
            self.t_INTEGER_TYPE = type(tok.value)

        # Determine the token type for strings enclosed in double quotes
        self.lexer.input("\"filename\"")
        tok = self.lexer.token()
        if not tok or tok.value != "\"filename\"":
            print("Couldn't determine string type")
        else:
            self.t_STRING = tok.type

        # Determine the token type for whitespace--if any
        self.lexer.input("  ")
        tok = self.lexer.token()
        if not tok or tok.value != "  ":
            self.t_SPACE = None
        else:
            self.t_SPACE = tok.type

        # Determine the token type for newlines
        self.lexer.input("\n")
        tok = self.lexer.token()
        if not tok or tok.value != "\n":
            self.t_NEWLINE = None
            print("Couldn't determine token for newlines")
        else:
            self.t_NEWLINE = tok.type

        self.t_WS = (self.t_SPACE, self.t_NEWLINE)

        # Check for other characters used by the preprocessor
        chars = [ '<','>','#','##','\\','(',')',',','.']
        for c in chars:
            self.lexer.input(c)
            tok = self.lexer.token()
            if not tok or tok.value != c:
                print("Unable to lex '%s' required for preprocessor" % c)

    # ----------------------------------------------------------------------
    # add_path()
    #
    # Adds a search path to the preprocessor.  
    # ----------------------------------------------------------------------

    def add_path(self,path):
        self.path.append(path)

    # ----------------------------------------------------------------------
    # group_lines()
    #
    # Given an input string, this function splits it into lines.  Trailing whitespace
    # is removed.   Any line ending with \ is grouped with the next line.  This
    # function forms the lowest level of the preprocessor---grouping into text into
    # a line-by-line format.
    # ----------------------------------------------------------------------

    def group_lines(self,input):
        lex = self.lexer.clone()
        lines = [x.rstrip() for x in input.splitlines()]
        for i in xrange(len(lines)):
            j = i+1
            while lines[i].endswith('\\') and (j < len(lines)):
                lines[i] = lines[i][:-1]+lines[j]
                lines[j] = ""
                j += 1

        input = "\n".join(lines)
        lex.input(input)
        lex.lineno = 1

        current_line = []
        current_line_pos = 0;
        while True:
            tok = lex.token()
            if not tok:
                break
            tok.linepos = current_line_pos
            current_line_pos += len(tok.value)
            current_line.append(tok)
            if tok.type in self.t_WS and '\n' in tok.value:
                yield current_line
                current_line = []
                current_line_pos = 0

        if current_line:
            yield current_line

    # ----------------------------------------------------------------------
    # tokenstrip()
    # 
    # Remove leading/trailing whitespace tokens from a token list
    # ----------------------------------------------------------------------

    def tokenstrip(self,tokens):
        i = 0
        while i < len(tokens) and tokens[i].type in self.t_WS:
            i += 1
        del tokens[:i]
        i = len(tokens)-1
        while i >= 0 and tokens[i].type in self.t_WS:
            i -= 1
        del tokens[i+1:]
        return tokens


    # ----------------------------------------------------------------------
    # collect_args()
    #
    # Collects comma separated arguments from a list of tokens.   The arguments
    # must be enclosed in parenthesis.  Returns a tuple (tokencount,args,positions)
    # where tokencount is the number of tokens consumed, args is a list of arguments,
    # and positions is a list of integers containing the starting index of each
    # argument.  Each argument is represented by a list of tokens.
    #
    # When collecting arguments, leading and trailing whitespace is removed
    # from each argument.  
    #
    # This function properly handles nested parenthesis and commas---these do not
    # define new arguments.
    # ----------------------------------------------------------------------

    def collect_args(self,tokenlist):
        args = []
        positions = []
        current_arg = []
        nesting = 1
        tokenlen = len(tokenlist)
    
        # Search for the opening '('.
        i = 0
        while (i < tokenlen) and (tokenlist[i].type in self.t_WS):
            i += 1

        if (i < tokenlen) and (tokenlist[i].value == '('):
            positions.append(i+1)
        else:
            self.error(self.source,tokenlist[0].lineno,"Missing '(' in macro arguments")
            return 0, [], []

        i += 1

        while i < tokenlen:
            t = tokenlist[i]
            if t.value == '(':
                current_arg.append(t)
                nesting += 1
            elif t.value == ')':
                nesting -= 1
                if nesting == 0:
                    if current_arg:
                        args.append(self.tokenstrip(current_arg))
                        positions.append(i)
                    return i+1,args,positions
                current_arg.append(t)
            elif t.value == ',' and nesting == 1:
                args.append(self.tokenstrip(current_arg))
                positions.append(i+1)
                current_arg = []
            else:
                current_arg.append(t)
            i += 1
    
        # Missing end argument
        self.error(self.source,tokenlist[-1].lineno,"Missing ')' in macro arguments")
        return 0, [],[]

    # ----------------------------------------------------------------------
    # macro_prescan()
    #
    # Examine the macro value (token sequence) and identify patch points
    # This is used to speed up macro expansion later on---we'll know
    # right away where to apply patches to the value to form the expansion
    # ----------------------------------------------------------------------
    
    def macro_prescan(self,macro):
        macro.patch     = []             # Standard macro arguments 
        macro.str_patch = []             # String conversion expansion
        macro.var_comma_patch = []       # Variadic macro comma patch
        i = 0
        while i < len(macro.value):
            if macro.value[i].type == self.t_ID and macro.value[i].value in macro.arglist:
                argnum = macro.arglist.index(macro.value[i].value)
                # Conversion of argument to a string
                if i > 0 and macro.value[i-1].value == '#':
                    macro.value[i] = copy.copy(macro.value[i])
                    macro.value[i].type = self.t_STRING
                    del macro.value[i-1]
                    macro.str_patch.append((argnum,i-1))
                    if (i > 1) and macro.value[i-2].value == '##':
                        i -= 1;  # backup one so that the concatenation happens too
                    continue
                # Concatenation
                elif (i > 0 and macro.value[i-1].value == '##'):
                    macro.patch.append(('c',argnum,i-1))
                    del macro.value[i-1]
                    continue
                elif ((i+1) < len(macro.value) and macro.value[i+1].value == '##'):
                    macro.patch.append(('c',argnum,i))
                    i += 1
                    continue
                # Standard expansion
                else:
                    macro.patch.append(('e',argnum,i))
            elif macro.value[i].value == '##':
                if macro.variadic and (i > 0) and (macro.value[i-1].value == ',') and \
                        ((i+1) < len(macro.value)) and (macro.value[i+1].type == self.t_ID) and \
                        (macro.value[i+1].value == macro.vararg):
                    macro.var_comma_patch.append(i-1)
                elif (i > 0):
                    macro.patch.append(('c',0,i-1))
                    del macro.value[i]
                    continue
            i += 1
        macro.patch.sort(key=lambda x: x[2],reverse=True)

    # ----------------------------------------------------------------------
    # macro_expand_args()
    #
    # Given a Macro and list of arguments (each a token list), this method
    # returns an expanded version of a macro.  The return value is a token sequence
    # representing the replacement macro tokens
    # ----------------------------------------------------------------------

    def macro_expand_args(self,macro,args):
        # Make a copy of the macro token sequence
        rep = [copy.copy(_x) for _x in macro.value]

        # Make string expansion patches.  These do not alter the length of the replacement sequence
        str_expansion = {}
        for argnum, i in macro.str_patch:
            if argnum not in str_expansion:
                str_expansion[argnum] = ('"%s"' % "".join([x.value for x in args[argnum]])).replace("\\","\\\\")
            rep[i] = copy.copy(rep[i])
            rep[i].value = str_expansion[argnum]

        # Make the variadic macro comma patch.  If the variadic macro argument is empty, we get rid
        comma_patch = False
        if macro.variadic and not args[-1]:
            for i in macro.var_comma_patch:
                rep[i] = None
                comma_patch = True

        # Make all other patches.   The order of these matters.  It is assumed that the patch list
        # has been sorted in reverse order of patch location since replacements will cause the
        # size of the replacement sequence to expand from the patch point.
        
        expanded = { }
        for ptype, argnum, i in macro.patch:
            # Concatenation.   Argument is left unexpanded
            if ptype == 'c':
                left = rep[i].value
                if left[-1] == '"':
                    left = left[:-1]
                right = rep[i+1].value
                if right[0] == '"':
                    right = right[1:]
                rep[i].value = left + right
                del rep[i+1]
            # Normal expansion.  Argument is macro expanded first
            elif ptype == 'e':
                if argnum not in expanded:
                    expanded[argnum] = self.expand_macros(args[argnum])
                rep[i:i+1] = expanded[argnum]

        # Get rid of removed comma if necessary
        if comma_patch:
            rep = [_i for _i in rep if _i]

        return rep


    # ----------------------------------------------------------------------
    # expand_macros()
    #
    # Given a list of tokens, this function performs macro expansion.
    # The expanded argument is a dictionary that contains macros already
    # expanded.  This is used to prevent infinite recursion.
    # ----------------------------------------------------------------------

    def expand_macros(self,tokens,expanded=None):
        if expanded is None:
            expanded = {}
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.type == self.t_ID:
                if t.value in self.macros and t.value not in expanded:
                    # Yes, we found a macro match
                    expanded[t.value] = True
                    
                    m = self.macros[t.value]
                    if not m.arglist:
                        # A simple macro
                        ex = self.expand_macros([copy.copy(_x) for _x in m.value],expanded)
                        for e in ex:
                            e.lineno = t.lineno
                            e.linepos = t.linepos
                        tokens[i:i+1] = ex
                        i += len(ex)
                    else:
                        # A macro with arguments
                        j = i + 1
                        while j < len(tokens) and tokens[j].type in self.t_WS:
                            j += 1
                        if tokens[j].value == '(':
                            tokcount,args,positions = self.collect_args(tokens[j:])
                            if not m.variadic and len(args) !=  len(m.arglist):
                                self.error(self.source,t.lineno,"Macro %s requires %d arguments" % (t.value,len(m.arglist)))
                                i = j + tokcount
                            elif m.variadic and len(args) < len(m.arglist)-1:
                                if len(m.arglist) > 2:
                                    self.error(self.source,t.lineno,"Macro %s must have at least %d arguments" % (t.value, len(m.arglist)-1))
                                else:
                                    self.error(self.source,t.lineno,"Macro %s must have at least %d argument" % (t.value, len(m.arglist)-1))
                                i = j + tokcount
                            else:
                                if m.variadic:
                                    if len(args) == len(m.arglist)-1:
                                        args.append([])
                                    else:
                                        args[len(m.arglist)-1] = tokens[j+positions[len(m.arglist)-1]:j+tokcount-1]
                                        del args[len(m.arglist):]
                                        
                                # Get macro replacement text
                                rep = self.macro_expand_args(m,args)
                                rep = self.expand_macros(rep,expanded)
                                for r in rep:
                                    r.lineno = t.lineno
                                tokens[i:j+tokcount] = rep
                                i += len(rep)
                    del expanded[t.value]
                    continue
                elif t.value == '__LINE__':
                    t.type = self.t_INTEGER
                    t.value = self.t_INTEGER_TYPE(t.lineno)
                
            i += 1

        # fix up line positions
        i = 0
        cur_line_pos = 0
        while i < len(tokens):
            tokens[i].linepos = cur_line_pos
            cur_line_pos += len(tokens[i].value)
            i += 1

        return tokens

    # ----------------------------------------------------------------------    
    # evalexpr()
    # 
    # Evaluate an expression token sequence for the purposes of evaluating
    # integral expressions.
    # ----------------------------------------------------------------------

    def evalexpr(self,tokens):
        # tokens = tokenize(line)
        # Search for defined macros
        i = 0
        while i < len(tokens):
            if tokens[i].type == self.t_ID and tokens[i].value == 'defined':
                j = i + 1
                needparen = False
                result = "0L"
                while j < len(tokens):
                    if tokens[j].type in self.t_WS:
                        j += 1
                        continue
                    elif tokens[j].type == self.t_ID:
                        if tokens[j].value in self.macros:
                            result = "1L"
                        else:
                            result = "0L"
                        if not needparen: break
                    elif tokens[j].value == '(':
                        needparen = True
                    elif tokens[j].value == ')':
                        break
                    else:
                        self.error(self.source,tokens[i].lineno,"Malformed defined()")
                    j += 1
                tokens[i].type = self.t_INTEGER
                tokens[i].value = self.t_INTEGER_TYPE(result)
                del tokens[i+1:j+1]
            i += 1
        tokens = self.expand_macros(tokens)
        for i,t in enumerate(tokens):
            if t.type == self.t_ID:
                tokens[i] = copy.copy(t)
                tokens[i].type = self.t_INTEGER
                tokens[i].value = self.t_INTEGER_TYPE("0L")
            elif t.type == self.t_INTEGER:
                tokens[i] = copy.copy(t)
                # Strip off any trailing suffixes
                tokens[i].value = str(tokens[i].value)
                while tokens[i].value[-1] not in "0123456789abcdefABCDEF":
                    tokens[i].value = tokens[i].value[:-1]
        
        expr = "".join([str(x.value) for x in tokens])
        expr = expr.replace("&&"," and ")
        expr = expr.replace("||"," or ")
        expr = expr.replace("!"," not ")
        try:
            result = eval(expr)
        except StandardError:
            self.error(self.source,tokens[0].lineno,"Couldn't evaluate expression")
            result = 0
        return result

    # ----------------------------------------------------------------------
    # parsegen()
    #
    # Parse an input string/
    # ----------------------------------------------------------------------
    def parsegen(self,input,source=None):

        # group lines together
        lines = self.group_lines(input)

        if not source:
            source = ""
            
        self.define("__FILE__ \"%s\"" % source)

        self.source = source
        chunk = []
        enable = True
        iftrigger = False
        ifstack = []

        for x in lines:
            for i,tok in enumerate(x):
                if tok.type not in self.t_WS: break
            if tok.value == '#':
                # Preprocessor directive

                for tok in x:
                    if tok in self.t_WS and '\n' in tok.value:
                        chunk.append(tok)
                
                dirtokens = self.tokenstrip(x[i+1:])
                if dirtokens:
                    name = dirtokens[0].value
                    args = self.tokenstrip(dirtokens[1:])
                else:
                    name = ""
                    args = []
                
                # TODO: make this configurable and easily expandable so that
                # all of the funky preprocessor directives supported by HLAKit
                if name == 'define':
                    if enable:
                        for tok in self.expand_macros(chunk):
                            yield tok
                        chunk = []
                        self.define(args)
                elif name == 'include':
                    if enable:
                        for tok in self.expand_macros(chunk):
                            yield tok
                        chunk = []
                        oldfile = self.macros['__FILE__']
                        for tok in self.include(args):
                            yield tok
                        self.macros['__FILE__'] = oldfile
                        self.source = source
                elif name == 'undef':
                    if enable:
                        for tok in self.expand_macros(chunk):
                            yield tok
                        chunk = []
                        self.undef(args)
                elif name == 'ifdef':
                    ifstack.append((enable,iftrigger))
                    if enable:
                        if not args[0].value in self.macros:
                            enable = False
                            iftrigger = False
                        else:
                            iftrigger = True
                elif name == 'ifndef':
                    ifstack.append((enable,iftrigger))
                    if enable:
                        if args[0].value in self.macros:
                            enable = False
                            iftrigger = False
                        else:
                            iftrigger = True
                elif name == 'if':
                    ifstack.append((enable,iftrigger))
                    if enable:
                        result = self.evalexpr(args)
                        if not result:
                            enable = False
                            iftrigger = False
                        else:
                            iftrigger = True
                elif name == 'elif':
                    if ifstack:
                        if ifstack[-1][0]:     # We only pay attention if outer "if" allows this
                            if enable:         # If already true, we flip enable False
                                enable = False
                            elif not iftrigger:   # If False, but not triggered yet, we'll check expression
                                result = self.evalexpr(args)
                                if result:
                                    enable  = True
                                    iftrigger = True
                    else:
                        self.error(self.source,dirtokens[0].lineno,"Misplaced #elif")
                        
                elif name == 'else':
                    if ifstack:
                        if ifstack[-1][0]:
                            if enable:
                                enable = False
                            elif not iftrigger:
                                enable = True
                                iftrigger = True
                    else:
                        self.error(self.source,dirtokens[0].lineno,"Misplaced #else")

                elif name == 'endif':
                    if ifstack:
                        enable,iftrigger = ifstack.pop()
                    else:
                        self.error(self.source,dirtokens[0].lineno,"Misplaced #endif")
                
                # messages
                elif name in ('todo', 'warning', 'error', 'fatal'):
                    if enable:
                        if len(args):
                            print "%s: %s" % (name.upper(), args[0].value)
                        else:
                            print "%s: %s" % name.upper()
                else:
                    # Unknown preprocessor directive, pass it along
                    if enable:
                        chunk.extend(x)

            else:
                # Normal text
                if enable:
                    chunk.extend(x)

        for tok in self.expand_macros(chunk):
            yield tok
        chunk = []

    # ----------------------------------------------------------------------
    # include()
    #
    # Implementation of file-inclusion
    # ----------------------------------------------------------------------

    def include(self,tokens):
        # Try to extract the filename and then process an include file
        if not tokens:
            return
        if tokens:
            if tokens[0].value != '<' and tokens[0].type != self.t_STRING:
                tokens = self.expand_macros(tokens)

            if tokens[0].value == '<':
                # Include <...>
                i = 1
                while i < len(tokens):
                    if tokens[i].value == '>':
                        break
                    i += 1
                else:
                    print("Malformed #include <...>")
                    return
                filename = "".join([x.value for x in tokens[1:i]])
                path = self.path + [""] + self.temp_path
            elif tokens[0].type == self.t_STRING:
                filename = tokens[0].value[1:-1]
                path = self.temp_path + [""] + self.path
            else:
                print("Malformed #include statement")
                return
        for p in path:
            iname = os.path.join(p,filename)
            try:
                data = open(iname,"r").read()
                dname = os.path.dirname(iname)
                if dname:
                    self.temp_path.insert(0,dname)
                for tok in self.parsegen(data,filename):
                    yield tok
                if dname:
                    del self.temp_path[0]
                break
            except IOError:
                pass
        else:
            print("Couldn't find '%s'" % filename)

    # ----------------------------------------------------------------------
    # define()
    #
    # Define a new macro
    # ----------------------------------------------------------------------

    def define(self,tokens):
        if isinstance(tokens,(str,unicode)):
            tokens = self.tokenize(tokens)

        linetok = tokens
        try:
            name = linetok[0]
            if len(linetok) > 1:
                mtype = linetok[1]
            else:
                mtype = None
            if not mtype:
                m = Macro(name.value,[])
                self.macros[name.value] = m
            elif mtype.type in self.t_WS:
                # A normal macro
                m = Macro(name.value,self.tokenstrip(linetok[2:]))
                self.macros[name.value] = m
            elif mtype.value == '(':
                # A macro with arguments
                tokcount, args, positions = self.collect_args(linetok[1:])
                variadic = False
                for a in args:
                    if variadic:
                        print("No more arguments may follow a variadic argument")
                        break
                    astr = "".join([str(_i.value) for _i in a])
                    if astr == "...":
                        variadic = True
                        a[0].type = self.t_ID
                        a[0].value = '__VA_ARGS__'
                        variadic = True
                        del a[1:]
                        continue
                    elif astr[-3:] == "..." and a[0].type == self.t_ID:
                        variadic = True
                        del a[1:]
                        # If, for some reason, "." is part of the identifier, strip off the name for the purposes
                        # of macro expansion
                        if a[0].value[-3:] == '...':
                            a[0].value = a[0].value[:-3]
                        continue
                    if len(a) > 1 or a[0].type != self.t_ID:
                        print("Invalid macro argument")
                        break
                else:
                    mvalue = self.tokenstrip(linetok[1+tokcount:])
                    i = 0
                    while i < len(mvalue):
                        if i+1 < len(mvalue):
                            if mvalue[i].type in self.t_WS and mvalue[i+1].value == '##':
                                del mvalue[i]
                                continue
                            elif mvalue[i].value == '##' and mvalue[i+1].type in self.t_WS:
                                del mvalue[i+1]
                        i += 1
                    m = Macro(name.value,mvalue,[x[0].value for x in args],variadic)
                    self.macro_prescan(m)
                    self.macros[name.value] = m
            else:
                print("Bad macro definition")
        except LookupError:
            print("Bad macro definition")

    # ----------------------------------------------------------------------
    # undef()
    #
    # Undefine a macro
    # ----------------------------------------------------------------------

    def undef(self,tokens):
        id = tokens[0].value
        try:
            del self.macros[id]
        except LookupError:
            pass

    # ----------------------------------------------------------------------
    # parse()
    #
    # Parse input text.
    # ----------------------------------------------------------------------
    def parse(self,input,source=None,ignore={}):
        self.ignore = ignore
        self.parser = self.parsegen(input,source)
        
    # ----------------------------------------------------------------------
    # token()
    #
    # Method to return individual tokens
    # ----------------------------------------------------------------------
    def token(self):
        try:
            while True:
                tok = next(self.parser)
                if tok.type not in self.ignore: return tok
        except StopIteration:
            self.parser = None
            return None


if __name__ == '__main__':
    # create the lexer
    lexer = lex.lex()

    # Run a preprocessor
    fin = open(sys.argv[1])
    input = fin.read()
    fout = open(sys.argv[1] + ".pp", "w+")

    p = FrontEnd(lexer)
    p.parse(input,sys.argv[1])
    while True:
        tok = p.token()
        if not tok: break

        print "%s:%s:%s:%s:%s" % (p.source, tok.lineno, tok.linepos, tok.type, repr(tok.value))

    fin.close()
    fout.close()
