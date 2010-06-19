"""
HLAKit Tests
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
import os
import sys
import unittest
from pyparsing import ParseException, ParseFatalException
from cStringIO import StringIO
from hlakit.common.preprocessor import Preprocessor
from hlakit.common.session import Session, CommandLineError
from hlakit.common.tell import TellBank, TellBankOffset, TellBankSize, TellBankFree, TellBankType
from hlakit.common.incbin import Incbin
from hlakit.common.usepath import Usepath
from hlakit.common.ram import RamOrg, RamEnd
from hlakit.common.rom import RomOrg, RomEnd, RomBanksize, RomBank
from hlakit.common.setpad import SetPad
from hlakit.common.align import Align

class PreprocessorTester(unittest.TestCase):
    """
    This class aggregates all of the tests for the preprocessor.
    """

    def setUp(self):
        Session().parse_args(['--cpu=generic'])

    def tearDown(self):
        Session().preprocessor().reset_state()

    def testPreprocessor(self):
        session = Session()
        self.assertTrue(isinstance(session._target.preprocessor(), Preprocessor))

    pp_define = '#define FOO\n'
    pp_define_value = '#define FOO 1\n'
    pp_define_string = '#define FOO "blah blah blah"\n'
    pp_define_bar = '#define BAR\n'
    pp_undef = '#undef FOO\n'

    def testDefine(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_define))
        self.assertTrue(pp.has_symbol('FOO'))
    
    def testDefineValue(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_define_value))
        self.assertEquals(pp.get_symbol('FOO'), '1')

    def testDefineString(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_define_string))
        self.assertEquals(pp.get_symbol('FOO'), '"blah blah blah"')

    def testUndef(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_define))
        self.assertTrue(pp.has_symbol('FOO'))

        pp.parse(StringIO(self.pp_undef))
        self.assertFalse(pp.has_symbol('FOO'), 'FOO shouldn\'t be defined')


    pp_ifdef = '#ifdef FOO\n'
    pp_ifndef = '#ifndef FOO\n'
    pp_else = '#else\n'
    pp_endif = '#endif\n'

    def testIfdef(self):
        pp = Session().preprocessor()

        #define FOO
        pp.parse(StringIO(self.pp_define))
        self.assertTrue(pp.has_symbol('FOO'))
        self.assertEquals(len(pp.get_ignore_stack()), 1)

        #ifdef FOO
        pp.parse(StringIO(self.pp_ifdef))
        self.assertEquals(len(pp.get_ignore_stack()), 2)
        self.assertFalse(pp.ignore_stack_top())
        self.assertFalse(pp.ignore())

        #define BAR
        pp.parse(StringIO(self.pp_define_bar))
        self.assertTrue(pp.has_symbol('BAR'))

        #endif
        pp.parse(StringIO(self.pp_endif))
        self.assertEquals(len(pp.get_ignore_stack()), 1)
        
        self.assertTrue(pp.has_symbol('BAR'))

    def testIfndef(self):
        pp = Session().preprocessor()
        
        self.assertEquals(len(pp.get_ignore_stack()), 1)

        #ifndef FOO
        pp.parse(StringIO(self.pp_ifndef))
        self.assertEquals(len(pp.get_ignore_stack()), 2)
        self.assertFalse(pp.ignore_stack_top())
        self.assertFalse(pp.ignore())

        #define BAR
        pp.parse(StringIO(self.pp_define_bar))
        self.assertTrue(pp.has_symbol('BAR'))

        #endif
        pp.parse(StringIO(self.pp_endif))
        self.assertEquals(len(pp.get_ignore_stack()), 1)
        
        self.assertTrue(pp.has_symbol('BAR'))

    def testElse(self):
        pp = Session().preprocessor()

        #ifdef FOO
        pp.parse(StringIO(self.pp_ifdef))
        self.assertEquals(len(pp.get_ignore_stack()), 2)
        self.assertTrue(pp.ignore_stack_top())
        self.assertTrue(pp.ignore())

        #define FOO
        pp.parse(StringIO(self.pp_define))
        self.assertFalse(pp.has_symbol('FOO'))
        self.assertTrue(pp.ignore())

        #else
        pp.parse(StringIO(self.pp_else))
        self.assertEquals(len(pp.get_ignore_stack()), 2)
        self.assertFalse(pp.ignore_stack_top())
        self.assertFalse(pp.ignore())

        #define BAR
        pp.parse(StringIO(self.pp_define_bar))
        self.assertTrue(pp.has_symbol('BAR'))

        #endif
        pp.parse(StringIO(self.pp_endif))
        self.assertEquals(len(pp.get_ignore_stack()), 1)
        
        self.assertFalse(pp.has_symbol('FOO'))
        self.assertTrue(pp.has_symbol('BAR'))

    def testBadUndef(self):
        pp = Session().preprocessor()
        
        #undef FOO 
        pp.parse(StringIO(self.pp_undef))


    pp_todo = '#todo %s\n'
    pp_warning = '#warning %s\n'
    pp_error = '#error %s\n'
    
    def testTodo(self):
        pp = Session().preprocessor()

        #todo "Hello World"
        pp.parse(StringIO(self.pp_todo % '"Hello World!"'))


    def testBadTodo(self):
        pp = Session().preprocessor()

        #todo
        try:
            pp.parse(StringIO(self.pp_todo))
            self.assertTrue(False)
        except ParseException, e:
            pass

    def testWarning(self):
        pp = Session().preprocessor()

        #warning "Hello World"
        pp.parse(StringIO(self.pp_warning % '"Hello World!"'))


    def testBadWarning(self):
        pp = Session().preprocessor()

        #warning
        try:
            pp.parse(StringIO(self.pp_warning))
            self.assertTrue(False)
        except ParseException, e:
            pass

    def testError(self):
        pp = Session().preprocessor()

        #error "Hello World"
        try:
            pp.parse(StringIO(self.pp_error % '"Hello World!"'))
            self.assertTrue(False)
        except ParseFatalException, e:
            pass

    def testBadError(self):
        pp = Session().preprocessor()

        #error
        try:
            pp.parse(StringIO(self.pp_error))
            self.assertTrue(False)
        except ParseException, e:
            pass

    pp_tellbank = '#tell.bank\n'
    pp_tellbankoffset = '#tell.bankoffset\n'
    pp_tellbanksize = '#tell.banksize\n'
    pp_tellbankfree = '#tell.bankfree\n'
    pp_tellbanktype = '#tell.banktype\n'

    def testTellBank(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_tellbank))
        self.assertTrue(isinstance(pp.get_output()[0], TellBank))

    def testTellBankOffset(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_tellbankoffset))
        self.assertTrue(isinstance(pp.get_output()[0], TellBankOffset))

    def testTellBankSize(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_tellbanksize))
        self.assertTrue(isinstance(pp.get_output()[0], TellBankSize))

    def testTellBankFree(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_tellbankfree))
        self.assertTrue(isinstance(pp.get_output()[0], TellBankFree))

    def testTellBankType(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_tellbanktype))
        self.assertTrue(isinstance(pp.get_output()[0], TellBankType))


    pp_include = '#include %s\n'
    pp_incbin = '#incbin %s\n'
    pp_usepath = '#usepath %s\n'

    def testImpliedInclude(self):
        Session().parse_args(['--cpu=generic', '--include=tests'])
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_include % '<dummy.h>'))
        self.assertTrue(pp.has_symbol('FOO'))

    def testImpliedDirInclude(self):
        pp = Session().preprocessor()

        path = '<%s>' % os.path.join('tests', 'dummy.h')
        pp.parse(StringIO(self.pp_include % path))
        self.assertTrue(pp.has_symbol('FOO'))

    def testLiteralInclude(self):
        pp = Session().preprocessor()

        path = '"%s"' % os.path.join('tests', 'dummy.h')
        pp.parse(StringIO(self.pp_include % path))
        self.assertTrue(pp.has_symbol('FOO'))

    def testFullPathLiteralInclude(self):
        pp = Session().preprocessor()

        full_path = '"%s"' % os.path.join(os.getcwd(), 'tests', 'dummy.h')
        pp.parse(StringIO(self.pp_include % full_path))
        self.assertTrue(pp.has_symbol('FOO'))

    def testBadImpliedInclude(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_include % '<dummy.h>'))
            self.assertTrue(False)
        except ParseFatalException, e:
            pass

    def testBadLiteralInclude(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_include % '"dummy.y"'))
            self.assertTrue(False)
        except ParseFatalException, e:
            pass

    def testImpliedIncbin(self):
        Session().parse_args(['--cpu=generic', '--include=tests'])
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_incbin % '<blob.bin>'))
        self.assertTrue(isinstance(pp.get_output()[0], Incbin))

    def testImpliedDirIncbin(self):
        pp = Session().preprocessor()

        path = '<%s>' % os.path.join('tests', 'blob.bin')
        pp.parse(StringIO(self.pp_incbin % path))
        self.assertTrue(isinstance(pp.get_output()[0], Incbin))

    def testLiteralIncbin(self):
        pp = Session().preprocessor()

        path = '"%s"' % os.path.join('tests', 'blob.bin')
        pp.parse(StringIO(self.pp_incbin % path))
        self.assertTrue(isinstance(pp.get_output()[0], Incbin))

    def testFullPathLiteralIncbin(self):
        pp = Session().preprocessor()

        full_path = '"%s"' % os.path.join(os.getcwd(), 'tests', 'blob.bin')
        pp.parse(StringIO(self.pp_incbin % full_path))
        self.assertTrue(isinstance(pp.get_output()[0], Incbin))

    def testBadImpliedIncbin(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_incbin % '<blob.bin>'))
            self.assertTrue(False)
        except ParseFatalException, e:
            pass

    def testBadLiteralIncbin(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_include % '"blob.bin"'))
            self.assertTrue(False)
        except ParseFatalException, e:
            pass

    def testImpliedUsepath(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_usepath % '<tests>'))
        self.assertEquals(Session().get_include_dirs()[-1], 'tests')

    def testLiteralUsepath(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_usepath % '"tests"'))
        self.assertEquals(Session().get_include_dirs()[-1], 'tests')

    pp_ramorg = '#ram.org %s\n'
    pp_ramend = '#ram.end\n'
    pp_romorg = '#rom.org %s\n'
    pp_romend = '#rom.end\n'
    pp_rombanksize = '#rom.banksize %s\n'
    pp_rombank = '#rom.bank %s\n'

    def testRamOrg(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_ramorg % '0x0100'))
        self.assertTrue(isinstance(pp.get_output()[0], RamOrg))
        self.assertEquals(int(pp.get_output()[0].get_address()), 0x100)

    def testRamOrgMaxsize(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_ramorg % '0x0100, 0x1000'))
        self.assertTrue(isinstance(pp.get_output()[0], RamOrg))
        self.assertEquals(int(pp.get_output()[0].get_address()), 0x0100)
        self.assertEquals(int(pp.get_output()[0].get_maxsize()), 0x1000)

    def testBadRamOrg(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_ramorg % ''))
            self.assertTrue(False)
        except ParseException:
            pass

    def testBadRamOrgMaxsize(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_ramorg % '0x0100,'))
            self.assertTrue(False)
        except ParseException:
            pass

    def testRamEnd(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_ramend))
        self.assertTrue(isinstance(pp.get_output()[0], RamEnd))

    def testRomOrg(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_romorg % '0x0100'))
        self.assertTrue(isinstance(pp.get_output()[0], RomOrg))
        self.assertEquals(int(pp.get_output()[0].get_address()), 0x100)

    def testRomOrgMaxsize(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_romorg % '0x0100, 0x1000'))
        self.assertTrue(isinstance(pp.get_output()[0], RomOrg))
        self.assertEquals(int(pp.get_output()[0].get_address()), 0x0100)
        self.assertEquals(int(pp.get_output()[0].get_maxsize()), 0x1000)

    def testBadRomOrg(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_romorg % ''))
            self.assertTrue(False)
        except ParseException:
            pass

    def testBadRomOrgMaxsize(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_romorg % '0x0100,'))
            self.assertTrue(False)
        except ParseException:
            pass

    def testRomEnd(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_romend))
        self.assertTrue(isinstance(pp.get_output()[0], RomEnd))

    def testRomBanksize(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_rombanksize % '0x4000'))
        self.assertTrue(isinstance(pp.get_output()[0], RomBanksize))
        self.assertEquals(int(pp.get_output()[0].get_size()), 0x4000)

    def testBadRomBanksize(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_rombanksize % ''))
            self.assertTrue(False)
        except ParseException:
            pass

    def testRomBank(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_rombank % '3'))
        self.assertTrue(isinstance(pp.get_output()[0], RomBank))
        self.assertEquals(int(pp.get_output()[0].get_number()), 3)

    def testRomBankMaxsize(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_rombank % '3, 0x1000'))
        self.assertTrue(isinstance(pp.get_output()[0], RomBank))
        self.assertEquals(int(pp.get_output()[0].get_number()), 3)
        self.assertEquals(int(pp.get_output()[0].get_maxsize()), 0x1000)

    def testBadRomBank(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_rombank % ''))
            self.assertTrue(False)
        except ParseException:
            pass

    def testBadRomBankMaxsize(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_rombank % '3,'))
            self.assertTrue(False)
        except ParseException:
            pass

    pp_setpad = '#setpad %s\n'
    pp_align = '#align %s\n'

    def testSetPadNum(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_setpad % '0xFF'))
        self.assertTrue(isinstance(pp.get_output()[0], SetPad))
        self.assertEquals(pp.get_output()[0].get_value(), 0xFF)

    def testSetPadString(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_setpad % '"Foo"'))
        self.assertTrue(isinstance(pp.get_output()[0], SetPad))
        self.assertEquals(pp.get_output()[0].get_value(), 'Foo')

    def testBadSetPad(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_setpad % ''))
            self.assertTrue(False)
        except ParseException:
            pass

    def testAlign(self):
        pp = Session().preprocessor()

        pp.parse(StringIO(self.pp_align % '1K'))
        self.assertTrue(isinstance(pp.get_output()[0], Align))
        self.assertEquals(pp.get_output()[0].get_value(), 1024)

    def testBadAlign(self):
        pp = Session().preprocessor()

        try:
            pp.parse(StringIO(self.pp_align % ''))
            self.assertTrue(False)
        except ParseException:
            pass
