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

from pyparsing import ParseFatalException
from hlakit.common.session import Session
from hlakit.common.file import File

class Incbin(File):
    """
    This defines the rules for parsing a #incbin <path> and #incbin "path" 
    lines in a file
    """

    @classmethod
    def _get_keyword(klass):
        return '#incbin'

    @classmethod
    def _handle_file(klass, path, implied=False):
        if not path or len(path) <= 0:
            raise ParseFatalException('invalid include file path')

        session = Session()
        pp = session.preprocessor()
        file_path = session.get_file_path(path)

        if not file_path:
            raise ParseFatalException('included file does not exist: %s' % file_path)

        return klass(file_path)

    def __init__(self, f, label = None):
        self._name = f
        inf = open(f, 'r')
        self._data = inf.read()
        inf.close()
        self._label = label

    def get_data(self):
        return self._data

    def get_label(self):
        return self._label

    def __str__(self):
        if self._label is None:
            return "<%s>" % self._name
        return "<%s: %s>" % (self._label, self._name)

    __repr__ = __str__

