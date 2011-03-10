
from filelike.wrappers import *
from filelike import tests

import os
import tempfile
import unittest
from StringIO import StringIO


class Test_FileWrapper(tests.Test_ReadWriteSeek):
    """Testcases for FileWrapper base class."""
    
    def makeFile(self,contents,mode):
        s = StringIO(contents)
        f = FileWrapper(s,mode)
        def getvalue():
            return s.getvalue()
        f.getvalue = getvalue
        return f


class Test_OpenerDecoders(unittest.TestCase):
    """Testcases for the filelike.Opener decoder functions."""
    
    def setUp(self):
        import tempfile
        fd, self.tfilename = tempfile.mkstemp()
        os.close(fd)

    def tearDown(self):
        os.unlink(self.tfilename)

    def test_LocalFile(self):
        """Test opening a simple local file."""
        f = open(self.tfilename,"w")
        f.write("contents")
        f.close()
        f = filelike.open(self.tfilename,"r")
        self.assertEquals(f.name,self.tfilename)
        self.assertEquals(f.read(),"contents")
        f.close()
    
    def test_RemoteBzFile(self):
        """Test opening a remote BZ2 file."""
        f = filelike.open("http://www.rfk.id.au/static/test.txt.bz2","r-")
        self.assertEquals(f.read(),"contents goes here if you please.\n\n")

