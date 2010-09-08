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

from pyparsing import *
from session import Session
from symbol import Symbol
from type_ import Type
from struct_ import Struct
from name import Name
from numericvalue import NumericValue

class Variable(Symbol):
    """
    Variable parser/handler
    """

    @classmethod
    def parse(klass, pstring, location, tokens):
        pp = Session().preprocessor()

        if pp.ignore():
            return []

        shared = 'shared' in tokens.keys()

        if 'type_' not in tokens.keys():
            raise ParseFatalException('variable missing type')

        if 'variables' not in tokens.keys():
            raise ParseFatalException('invalid variable decl')

        variables = []
        for v in tokens.variables:
            array_ = 'array_' in v.keys()

            if 'name' not in v.keys():
                raise ParseFatalException('variable has no name')

            size = None
            if 'size' in v.keys():
                size = v.size

            address = None
            if 'address' in v.keys():
                address = v.address

            # add the variable to the symbol table
            var = klass(v.name, tokens.type_, shared, array_, size, address)

            variables.append(var)

        return variables

    @classmethod
    def exprs(klass):
        ops = Session().opcodes()
        kwds = Session().keywords()
        conds = Session().conditions()
        lbracket = Suppress('[')
        rbracket = Suppress(']')
        colon = Suppress(':')
        size = NumericValue.exprs()
        address = NumericValue.exprs()

        # build the proper expression for detecting types
        type_expr = None
        if ops:
            type_expr = ~ops
        if kwds:
            if type_expr:
                type_expr += ~kwds
            else:
                type_expr = ~kwds
        if conds:
            if type_expr:
                type_expr += ~conds
            else:
                type_expr = ~conds
        if type_expr:
            type_expr += Type.exprs()
        else:
            type_expr = Type.exprs()

        expr = Optional(Keyword('shared').setResultsName('shared')) + \
               Or([Struct.exprs(), type_expr]).setResultsName('type_') + \
               ~LineEnd() + \
               delimitedList(Group(Name.exprs().setResultsName('name') + \
                                   Optional(lbracket + \
                                            Optional(size.setResultsName('size')) + \
                                            rbracket).setResultsName('array_') + \
                                    Optional(colon + address.setResultsName('address'))),
                             delim=',').setResultsName('variables')
        expr.setParseAction(klass.parse)
        
        return expr

    def __init__(self, name, type_, shared=False, array_=False, size=None, address=None):
        super(Variable, self).__init__(name, type_)
        self._shared = shared
        self._array = array_
        self._size = size
        self._address = address

    def is_shared(self):
        return self._shared

    def is_array(self):
        return self._array

    def get_array_size(self):
        if self._size != None:
            return int(self._size)
        return None

    def get_address(self):
        return self._address

    def __str__(self):
        s = ''
        if self._shared:
            s += 'shared '
        s += '%s ' % self.get_type().get_name()
        s += '%s' % self.get_name()
        if self.is_array():
            s += '['
            if self.get_array_size():
                s += '%s' % self.get_array_size()
            s += ']'
        if self.get_address():
            s += ' :%s' % self.get_address()
        return s

    __repr__ = __str__

