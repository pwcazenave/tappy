
from filelike.wrappers import Slice
from filelike import tests

import unittest
from StringIO import StringIO
 

class Test_Slice_Whole(tests.Test_ReadWriteSeek):
    """Testcases for the Slice wrapper class."""

    def makeFile(self,contents,mode,start=0,stop=None,resizable=False):
        s = StringIO(contents)
        f = Slice(s,start,stop,resizable=resizable,mode=mode)
        def getvalue():
            val = s.getvalue()
            if stop:
                val = val[:f.stop]
            if start:
                val = val[f.start:]
            return val
        f.getvalue = getvalue
        return f


class Test_Slice_Start(Test_Slice_Whole):
    """Testcases for the Slice wrapper class with a start offset."""

    def makeFile(self,contents,mode):
        c2 = "testing" + contents
        return super(Test_Slice_Start,self).makeFile(c2,mode,7)


class Test_Slice_StartStop(Test_Slice_Whole):
    """Testcases for the Slice wrapper class with both start and stop."""

    def makeFile(self,contents,mode):
        c2 = "testing" + contents + "hello"
        return super(Test_Slice_StartStop,self).makeFile(c2,mode,7,-5)

    def test_write(self):
        method = super(Test_Slice_StartStop,self).test_write
        self.assertRaises(IOError,method)

    def test_append(self):
        method = super(Test_Slice_StartStop,self).test_write
        self.assertRaises(IOError,method)

    def test_write_stream(self):
        method = super(Test_Slice_StartStop,self).test_write_stream
        self.assertRaises(IOError,method)

    def test_write_at_end(self):
        method = super(Test_Slice_StartStop,self).test_write_at_end
        self.assertRaises(IOError,method)

    def test_write_twice(self):
        method = super(Test_Slice_StartStop,self).test_write_twice
        self.assertRaises(IOError,method)


class Test_Slice_StartStopResize(Test_Slice_Whole):
    """Testcases for the Slice wraper, with resizable stop."""

    contents = "a simple test string"

    def makeFile(self,contents,mode):
        c2 = "testing" + contents + "hello"
        return super(Test_Slice_StartStopResize,self).makeFile(c2,mode,7,-5,True)
    
    def test_resizability(self):
        """Test that resizing slices works correctly."""
        #  By default, can't write beyond end of slice.
        f = Slice(StringIO("mytestdata"),start=2,stop=6)
        f.write("TE")
        f.seek(0)
        self.assertEquals(f.read(),"TEst")
        self.assertEquals(f._fileobj.getvalue(),"myTEstdata")
        f.seek(0)
        self.assertRaises(IOError,f.write,"TESTDATA")
        self.assertEquals(f._fileobj.getvalue(),"myTESTdata")
        # Resizability allows data to be overwritten
        f = Slice(StringIO("mytestdata"),start=2,stop=6,resizable=True)
        f.write("TESTDA")
        self.assertEquals(f._fileobj.getvalue(),"myTESTDAta")
        self.assertEquals(f.stop,8)
        
