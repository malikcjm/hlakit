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
from label import Label
from immediate import Immediate
from name import Name
from opcode import Opcode
from operand import Operand

class InstructionLine(object):
    """
    This encapsulates a single line of assembly code
    """

    @classmethod
    def new(klass, opcode, **kwargs):
        # this function is a helper function for creating instruction lines
        # from scratch in the resolve pass where functions and conditional
        # blocks are converted into Label and InstructionLine tokens.
        il = klass(Opcode.new(opcode), Operand.new(**kwargs))
        if 'fn' in kwargs.keys():
            il.set_fn(kwargs['fn'])
        return il

    @classmethod
    def parse(klass, pstring, location, tokens):
        pp = Session().preprocessor()

        if pp.ignore():
            return []
        
        opcode = None
        if 'opcode' in tokens.keys():
            opcode = tokens.opcode
        else:
            raise ParseFatalException('instruction line missing opcode')

        # get the operand if it exists
        operand = None
        if 'operand' in tokens.keys():
            operand = tokens.operand

        return klass(opcode, operand)

    @classmethod
    def exprs(klass):
        # the cpu/platform specific version of this function must return a
        # parser expr that matches any valid assembly instruction line.
        raise ParseFatalException('must overload this in a cpu/platform specific class')

    def __init__(self, opcode, operand):
        self._opcode = opcode
        self._operand = operand
        self._fn = None

    def get_opcode(self):
        return self._opcode

    def get_operand(self):
        return self._operand

    def set_fn(self, fn=None):
        self._fn = fn

    def get_fn(self):
        return self._fn

    def set_scope(self, scope):
        self._operand.set_scope(scope)

    def get_scope(self):
        return self._operand.get_scope()

    def is_resolved(self):
        return self._operand.is_resolved()

    def resolve(self):
        return self._operand.resolve()

    def __str__(self):
        s = str(self._opcode)
        if self._operand:
            try:
                str(self._operand)
            except TypeError, e:
                import pdb; pdb.set_trace()
                self._operand.resolve()
            if len(str(self._operand)):
                s += ' %s' % self._operand
        return s

    __repr__ = __str__
