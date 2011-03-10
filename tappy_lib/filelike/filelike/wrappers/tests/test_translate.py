
from filelike.wrappers import Translate, BytewiseTranslate
from filelike import tests, NotSeekableError

import unittest
from StringIO import StringIO


class Test_Translate(tests.Test_ReadWriteSeek):
    """Testcases for the Translate class, with null translation func."""
    
    def makeFile(self,contents,mode):
        def noop(string):
            return string
        s = StringIO(contents)
        f = Translate(s,noop,mode=mode)
        def getvalue():
            return s.getvalue()
        f.getvalue = getvalue
        return f


class Test_BytewiseTranslate(tests.Test_ReadWriteSeek):
    """Testcases for the BytewiseTranslate class."""
    
    def makeFile(self,contents,mode):
        def rot13(string):
            return string.encode("rot13")
        s = StringIO(contents.encode("rot13"))
        f = BytewiseTranslate(s,rot13,mode=mode)
        def getvalue():
            return s.getvalue().encode("rot13")
        f.getvalue = getvalue
        return f

