
from filelike.wrappers import Buffer, FlushableBuffer
from filelike import tests

import unittest
from StringIO import StringIO


def get_buffered_value(f):
    if f._check_mode("r"):
        f._read_rest()
    pos = f._buffer.tell()
    f._buffer.seek(0)
    val = f._buffer.read()
    f._buffer.seek(pos)
    return val


def def_getvalue_maybe_buffered(f,s,trans_s=None,trans_b=None):
    if isinstance(f._fileobj,Buffer):
        if trans_b:
            def getvalue():
                return trans_b(get_buffered_value(f._fileobj))
        else:
            def getvalue():
                return get_buffered_value(f._fileobj)
    else:
        if trans_s:
            def getvalue():
                return trans_s(s.getvalue())
        else:
            def getvalue():
                return s.getvalue()
    return getvalue


class Test_Buffer(tests.Test_ReadWriteSeek):
    """Testcases for the Buffer class."""
    
    def makeFile(self,contents,mode):
        s = StringIO(contents)
        if "a" in mode:
            s.seek(0,2)
        f = Buffer(s,mode)
        def getvalue():
            return get_buffered_value(f)
        f.getvalue = getvalue
        return f

    def test_buffer_w(self):
        f = self.makeFile("","w")
        s = f._fileobj
        close = s.close
        def noop():
            pass
        s.close = noop
        f.write("testing")
        f.flush()
        self.assertEquals(f.getvalue(),"testing")
        self.assertEquals(s.getvalue(),"")
        f.close()
        self.assertEquals(s.getvalue(),"testing")

    def test_buffer_rw(self):
        f = self.makeFile("testing","r+")
        s = f._fileobj
        close = s.close
        def noop():
            pass
        s.close = noop
        f.write("hello")
        f.flush()
        self.assertEquals(f.getvalue(),"hellong")
        self.assertEquals(s.getvalue(),"testing")
        f.close()
        self.assertEquals(s.getvalue(),"hellong")

    def test_buffer_a(self):
        f = self.makeFile("hello","a")
        s = f._fileobj
        close = s.close
        def noop():
            pass
        s.close = noop
        f.write("testing")
        f.flush()
        self.assertEquals(f.getvalue(),"testing")
        self.assertEquals(s.getvalue(),"hello")
        f.close()
        self.assertEquals(s.getvalue(),"hellotesting")

    def test_buffer_ra(self):
        f = self.makeFile("hello","a+")
        s = f._fileobj
        close = s.close
        def noop():
            pass
        s.close = noop
        f.write("testing")
        f.flush()
        self.assertEquals(f.getvalue(),"hellotesting")
        self.assertEquals(s.getvalue(),"hello")
        f.close()
        self.assertEquals(s.getvalue(),"hellotesting")


class Test_Buffer_rollover(Test_Buffer):
    """Testcases for the Buffer class with rollover to tempfile."""
    
    def makeFile(self,contents,mode):
        s = StringIO(contents)
        if "a" in mode:
            s.seek(0,2)
        f = Buffer(s,mode,max_size_in_memory=1)
        def getvalue():
            return get_buffered_value(f)
        f.getvalue = getvalue
        return f


class Test_FlushableBuffer(tests.Test_ReadWriteSeek):
    """Testcases for the FlushableBuffer class."""
    
    def makeFile(self,contents,mode):
        s = StringIO(contents)
        if "a" in mode:
            s.seek(0,2)
        f = FlushableBuffer(s,mode)
        def getvalue():
            return s.getvalue()
        f.getvalue = getvalue
        return f

    def test_buffer_w(self):
        f = self.makeFile("","w")
        s = f._fileobj
        close = s.close
        def noop():
            pass
        s.close = noop
        f.write("testing")
        f.close()
        self.assertEquals(s.getvalue(),"testing")

    def test_buffer_rw(self):
        f = self.makeFile("testing","r+")
        s = f._fileobj
        close = s.close
        def noop():
            pass
        s.close = noop
        f.write("hello")
        f.close()
        self.assertEquals(s.getvalue(),"hellong")

    def test_buffer_a(self):
        f = self.makeFile("hello","a")
        s = f._fileobj
        close = s.close
        def noop():
            pass
        s.close = noop
        f.write("testing")
        f.close()
        self.assertEquals(s.getvalue(),"hellotesting")

    def test_buffer_ra(self):
        f = self.makeFile("hello","a+")
        self.assertEquals(f._fileobj.tell(),5)
        self.assertEquals(f.tell(),5)
        s = f._fileobj
        close = s.close
        def noop():
            pass
        s.close = noop
        f.write("testing")
        f.close()
        self.assertEquals(s.getvalue(),"hellotesting")


class Test_FlushableBuffer_rollover(Test_FlushableBuffer):
    """Testcases for the FlushableBuffer class with rollover to tempfile."""
    
    def makeFile(self,contents,mode):
        s = StringIO(contents)
        if "a" in mode:
            s.seek(0,2)
        f = FlushableBuffer(s,mode,max_size_in_memory=1)
        def getvalue():
            return get_buffered_value(f)
        f.getvalue = getvalue
        return f

