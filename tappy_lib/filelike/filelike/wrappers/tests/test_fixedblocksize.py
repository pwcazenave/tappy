 
import unittest
from filelike.wrappers import FixedBlockSize
from filelike import tests

from StringIO import StringIO

class Test_FixedBlockSize5(tests.Test_ReadWriteSeek):
    """Testcases for the FixedBlockSize class, with blocksize 5."""

    blocksize = 5
    
    def makeFile(self,contents,mode):
        f = StringIO(contents)
        f.seek(0)
        class BSFile:
            """Simulate reads/writes, asserting correct blocksize."""
            def read(s,size=-1):
                self.assert_(size < 0 or size % self.blocksize == 0)
                return f.read(size)
            def write(s,data):
                if not s._flushing:
                    self.assert_(len(data)%self.blocksize == 0)
                f.write(data)
            def seek(s,offset,whence):
                f.seek(offset,whence)
            def tell(s):
                return f.tell()
            def flush(self):
                f.flush()
        bsf = BSFile()
        bsf._flushing = False
        fbsf = FixedBlockSize(bsf,self.blocksize)
        # Patch it to indicate when it's flushing, so we don't raise errors
        oldflush = fbsf.flush
        def newflush():
            bsf._flushing = True
            oldflush()
            bsf._flushing = False
        fbsf.flush = newflush
        def getvalue():
            return f.getvalue()
        fbsf.getvalue = getvalue
        return fbsf


class Test_FixedBlockSize7(Test_FixedBlockSize5):
    """Testcases for the FixedBlockSize class, with blocksize 7."""
    blocksize = 7


class Test_FixedBlockSize24(Test_FixedBlockSize5):
    """Testcases for the FixedBlockSize class, with blocksize 24."""
    blocksize = 24

