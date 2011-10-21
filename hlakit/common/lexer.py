"""
HLAKit
Copyright (c) 2010-2011 David Huseby. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this list of
      conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice, this list
      of conditions and the following disclaimer in the documentation and/or other materials
      provided with the distribution.

THIS SOFTWARE IS PROVIDED BY DAVID HUSEBY ``AS IS'' AND ANY EXPRESS OR IMPLIED
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

class Lexer(object):

    # basic preprocessor tokens
    preprocessor = {
        'define':       'PP_DEFINE',
        'undef':        'PP_UNDEF',
        'ifdef':        'PP_IFDEF',
        'ifndef':       'PP_IFNDEF',
        'else':         'PP_ELSE',
        'endif':        'PP_ENDIF',
        'include':      'PP_INCLUDE'
        }

    # compiler specific preprocessor tokens
    compiler = {
        'incbin':       'CP_INCBIN',
        'todo':         'CP_TODO',
        'warning':      'CP_WARNING',
        'error':        'CP_ERROR',
        'fatal':        'CP_FATAL'
        }

    # linker specific preprocessor tokens
    #linker = {
    #    'ram':          'LP_RAM',
    #    'rom':          'LP_ROM',
    #    'org':          'LP_ORG',
    #    'end':          'LP_END',
    #    'banksize':     'LP_BANKSIZE',
    #    'bank':         'LP_BANK',
    #    'setpad':       'LP_SET_PAD',
    #    'align':        'LP_ALIGN'
    #    }

    # hla reserved tokens
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

    # hla conditional tokens 
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

    # the tokens list
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
    def t_WS(self, t):
        r'\s+'
        t.lexer.lineno += t.value.count("\n")
        return t

    # identifier
    def t_ID(self, t):
        r'[a-zA-Z_][\w]*'

        value = t.value.lower()

        t.type = self.preprocessor.get(value, None) # check for preprocessor words
        if t.type != None:
            t.value = value
            return t

        t.type = self.compiler.get(value, None) # check for reserved words
        if t.type != None:
            t.value = value
            return t
            
        #t.type = self.linker.get(value, None) # check for reserved words
        #if t.type != None:
        #    t.value = value
        #    return t

        t.type = self.reserved.get(value, None) # check for reserved words
        if t.type != None:
            t.value = value
            return t

        t.type = self.conditionals.get(value, None) # check for conditionals
        if t.type != None:
            t.value = value
            return t
            
        t.type = 'ID'
        return t

    def t_COMMENT(self, t):
        r'(/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/)|(//.*)'
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_error(self, t):
        t.type = t.value[0]
        t.value = t.value[0]
        t.lexer.skip(1)
        return t

    def __init__(self):
        pass
