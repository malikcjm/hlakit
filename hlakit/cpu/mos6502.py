"""
HLAKit
Copyright (C) David Huseby <dave@linuxprogrammer.org>

This software is licensed under the Creative Commons Attribution-NonCommercial-
ShareAlike 3.0 License.  You may read the full text of the license in the 
included LICENSE file or by visiting here: 
<http://creativecommons.org/licenses/by-nc-sa/3.0/legalcode>
"""

import os
from pyparsing import *
from cpu import CPU
from tokens import *
from hlakit.values import *
from hlakit.types import *
from hlakit.symbols import *
from hlakit.tokens import *

class PointerType(Type):
    """
    6502 specific pointer type
    """
    def __init__(self):
        super(PointerType, self).__init__('pointer', 2)

    def __str__(self):
        return 'pointer size: 2'

    __repr__ = __str__

    @classmethod
    def register(klass):
        TypeRegistry.instance()['pointer'] = klass()


class MOS6502(CPU):

    def __init__(self, options = None, logger = None):

        # init the base class 
        super(MOS6502, self).__init__()

        # store the options object
        self._options = options

        # store the logger
        self._logger = logger

        # initialize the preprocessor expressions lists
        self._preprocessor_exprs = []

        # initialize the compiler expressions list
        self._compiler_exprs = []

        # CPU specific values for binary generation
        self._start_symbol = None
        self._nmi_symbol = None
        self._irq_symbol = None

        # build the preprocessor expressions
        self._init_preprocessor_exprs()

        # build the compiler expressions
        self._init_compiler_exprs()
        
    def get_preprocessor_exprs(self):
        return self._preprocessor_exprs

    def get_compiler_exprs(self):
        return self._compiler_exprs

    def get_file_writer(self):
        # the file writer is the cpu specific binary creator.  
        # in this case it handles converting the 6502 mnemonics
        # into 6502 opcode binary data.
        return None

    def init_compiler_types(self):
        # register 6502 specific pointer type
        PointerType.register()

    def _init_preprocessor_exprs(self):
        # 6502 specific preprocessor directives
        start = Keyword('#interrupt.start')
        nmi = Keyword('#interrupt.nmi')
        irq = Keyword('#interrupt.irq')

        # define the value
        symbol = Word(alphas, alphanums + '_').setResultsName('symbol')

        # start interrupt line
        start_line = Suppress(start) + \
                     symbol + \
                     Suppress(LineEnd())
        start_line.setParseAction(self._start_line)
        start_line_address = Suppress(start) + \
                     NumericValue.exprs().setResultsName('address') + \
                     Suppress(LineEnd())
        start_line_address.setParseAction(self._start_line)

        # nmi interrupt line
        nmi_line = Suppress(nmi) + \
                   symbol + \
                   Suppress(LineEnd())
        nmi_line.setParseAction(self._nmi_line)
        nmi_line_address = Suppress(nmi) + \
                     NumericValue.exprs().setResultsName('address') + \
                     Suppress(LineEnd())
        nmi_line_address.setParseAction(self._start_line)

        # irq interrupt line
        irq_line = Suppress(irq) + \
                   symbol + \
                   Suppress(LineEnd())
        irq_line.setParseAction(self._irq_line)
        irq_line_address = Suppress(irq) + \
                     NumericValue.exprs().setResultsName('address') + \
                     Suppress(LineEnd())
        irq_line_address.setParseAction(self._start_line)

        # put the expressions in the top level map
        self._preprocessor_exprs.append(('start_line', start_line))
        self._preprocessor_exprs.append(('start_line_address', start_line_address))
        self._preprocessor_exprs.append(('nmi_line', nmi_line))
        self._preprocessor_exprs.append(('nmi_line_address', nmi_line_address))
        self._preprocessor_exprs.append(('irq_line', irq_line))
        self._preprocessor_exprs.append(('irq_line_address', irq_line_address))

    def _init_compiler_exprs(self):
        pass

    #
    # Parse Action Callbacks
    #

    def _start_line(self, pstring, location, tokens):
        if 'symbol' in tokens.keys():
            return InterruptVector(InterruptVector.START, tokens.symbol)
        elif 'address' in tokens.keys():
            return InterruptVector(InterruptVector.START, tokens.address)

        raise ParseFatalException('invalid argument for #interrupt.start')

    def _nmi_line(self, pstring, location, tokens):
        if 'symbol' in tokens.keys():
            return InterruptVector(InterruptVector.NMI, tokens.symbol)
        elif 'address' in tokens.keys():
            return InterruptVector(InterruptVector.NMI, tokens.address)

        raise ParseFatalException('invalid argument for #interrupt.nmi')

    def _irq_line(self, pstring, location, tokens):
        if 'symbol' in tokens.keys():
            return InterruptVector(InterruptVector.IRQ, tokens.symbol)
        elif 'address' in tokens.keys():
            return InterruptVector(InterruptVector.IRQ, tokens.address)

        raise ParseFatalException('invalid argument for #interrupt.nmi')

    """
    def _standard_variable(self, pstring, location, tokens):

        if 'type' not in tokens.keys():
            raise ParseFatalException('variable declaration is missing type')

        if 'label' not in tokens.keys():
            raise ParseFatalException('variable declaration is missing name')

        shared = 'shared' in tokens.keys()
        
        address = None
        if 'address' in tokens.keys():
            address = tokens.address
        
        value = None
        if 'value' in tokens.keys():
            value = tokens.value

        # check to see if the type is registered
        if TypeRegistry.instance()[tokens.type] is None:
            raise ParseFatalException('unknown type %s' % tokens.type)

        # create the variable, this adds it to the symbol table
        v = Variable(tokens.label, TypeRegistry.instance()[tokens.type], shared, address)

        # if there is a value specified, then return an AssignValue AST
        if value:
            return AssignValue(v, value)

        return v

    def _variable_list_item(self, pstring, location, tokens):

        if 'label' not in tokens.keys():
            raise ParseFatalException('variable list item missing name')

        address = None
        if 'address' in tokens.keys():
            address = tokens.address

        value = None
        if 'value' in tokens.keys():
            value = tokens.value

        return VariableDeclaration(tokens.label, address=address, value=value)

    def _variable_list(self, pstring, location, tokens):

        if 'var_list' not in tokens.keys():
            raise ParseFatalException('variable list declaration missing names')

        if 'var' not in tokens.keys():
            raise ParseFatalException('variable list missing variable type')

        t = [ tokens.var ]
        for i in range(0, len(tokens.var_list)):
            tokens.var_list[i].set_shared(tokens.var.get_shared())
            tokens.var_list[i].set_type(tokens.var.get_type())
            t.append(tokens.var_list[i])

        return t

    def _array_value(self, pstring, location, tokens):
        if 'number' not in tokens.keys():
            raise ParseFatalException('array value missing')

        labels = []
        if 'label_list' in tokens.keys():
            for i in range(0, len(tokens.label_list)):
                labels.append(tokens.label_list[i])

        return ArrayValue(tokens.number, labels)

    def _array_value_block(self, pstring, location, tokens):
        
        if 'value' not in tokens.keys():
            raise ParseFatalException('array block missing at least one value')

        values = [ tokens.value ]
        if 'value_list' in tokens.keys():
            for i in range(0, len(tokens.value_list)):
                values.append(tokens.value_list[i])

        return values

    def _array_variable_string(self, pstring, location, tokens):
        if 'type' not in tokens.keys():
            raise ParseFatalException('variable declaration is missing type')

        if 'label' not in tokens.keys():
            raise ParseFatalException('variable declaration is missing name')

        shared = 'shared' in tokens.keys()
        
        address = None
        if 'address' in tokens.keys():
            address = tokens.address
       
        size = None
        if 'size' in tokens.keys():
            size = tokens.size

        value = []
        if 'value' in tokens.keys():
            if not isinstance(tokens.value, str):
                raise ParseFatalException('array string value not a string')

            # decode the string
            v = tokens.value.decode('string-escape')

            for c in v:
                value.append(ArrayValue(ord(c)))

        return ArrayDeclaration(tokens.label, tokens.type, value, address, shared)

    def _array_variable_block(self, pstring, location, tokens):

        if 'type' not in tokens.keys():
            raise ParseFatalException('variable declaration is missing type')

        if 'label' not in tokens.keys():
            raise ParseFatalException('variable declaration is missing name')

        shared = 'shared' in tokens.keys()
        
        address = None
        if 'address' in tokens.keys():
            address = tokens.address
       
        size = None
        if 'size' in tokens.keys():
            size = tokens.size

        value = []
        if 'value' in tokens.keys():
            # check to see if they specified the correct size
            if size != None and size != len(tokens.value):
                raise ParseFatalException('array size doesn\'t match the number of values given')

            for i in range(0, len(tokens.value)):
                value.append(tokens.value[i])

        return ArrayDeclaration(tokens.label, tokens.type, value, address, shared)

    def _struct_block(self, pstring, location, tokens):
        if 'var_list' not in tokens.keys():
            raise ParseFatalException('struct missing members')

        vars = []
        for i in range(0, len(tokens.var_list)):
            vars.append(tokens.var_list[i])

        return vars

    def _struct_label_item(self, pstring, location, tokens):
        if 'label' not in tokens.keys():
            raise ParseFatalException('struct variable missing label')

        address = None
        if 'address' in tokens.keys():
            address = tokens.address

        return StructDeclaration(tokens.label, address=address)

    def _struct_variable(self, pstring, location, tokens):
        if 'type' not in tokens.keys():
            raise ParseFatalException('struct missing type name')

        shared = 'shared' in tokens.keys()

        address = None
        if 'address' in tokens.keys():
            address = tokens.address


        members = []
        if 'members' in tokens.keys():
            for i in range(0, len(tokens.members)):
                members.append(tokens.members[i])

        #TODO: process the label list to generate zero or more struct declarations

        return StructDeclaration(tokens., members, address, shared)
    """