
from filelike.wrappers import PadToBlockSize, UnPadToBlockSize
from filelike import tests, NotSeekableError

from StringIO import StringIO


class Test_PadToBlockSize5(tests.Test_ReadWriteSeek):
    """Testcases for PadToBlockSize with blocksize=5."""

    contents = "this is some sample textZ"
    empty_contents = "ZXXXX"
    text_plain = ["Zhis is sample texty"]
    text_padded = ["Zhis is sample textyZXXXX"]
    blocksize = 5

    def makeFile(self,contents,mode):
        # Careful here - 'contents' should be the contents of the returned
        # file, and is therefore expected to contain the padding.  But for
        # easy testing we allow it to omit the padding and be used directly
        # in the underlying StringIO object.
        idx = contents.rfind("Z")
        if idx < 0:
            idx = len(contents)
        s = StringIO(contents[:idx])
        f = PadToBlockSize(s,self.blocksize,mode=mode)
        def getvalue():
            val = s.getvalue() + "Z"
            if len(val) % self.blocksize != 0:
                val = val + (self.blocksize - (len(val) % self.blocksize))*"X"
            return val
        f.getvalue = getvalue
        return f

    def test_padding(self):
        for (plain,padded) in zip(self.text_plain,self.text_padded):
            f = self.makeFile(padded,"rw")
            self.assert_(len(padded) % self.blocksize == 0)
            self.assertEquals(f._fileobj.getvalue(),plain)

    def test_write_zeds(self):
        f = self.makeFile("","w")
        txt = "test data Z with lots of Z's embedded in it Z"
        f.write("test data Z w")
        f.write("ith lots of Z's e")
        f.write("mbedded in it Z")
        f.write(f._padding(txt))
        f.flush()
        self.assertEquals(f._fileobj.getvalue(),txt)

    def test_write_at_end(self):
        pass


class Test_PadToBlockSize7(Test_PadToBlockSize5):
    """Testcases for PadToBlockSize with blocksize=7."""

    contents = "this is som\n sample textZXXX"
    empty_contents = "ZXXXXXX"
    text_plain = ["Zhis is sample texty"]
    text_padded = ["Zhis is sample textyZ"]
    blocksize = 7


class Test_PadToBlockSize16(Test_PadToBlockSize5):
    """Testcases for PadToBlockSize with blocksize=16."""

    contents = "This is Zome Zample TeZTZXXXXXXX"
    empty_contents = "ZXXXXXXXXXXXXXXX"
    text_plain = ["short"]
    text_padded = ["shortZXXXXXXXXXX"]
    blocksize = 16


class Test_UnPadToBlockSize5(tests.Test_ReadWriteSeek):
    """Testcases for UnPadToBlockSize with blocksize=5."""

    contents = "this is some sample text"
    text_plain = ["Zhis is sample texty"]
    text_padded = ["Zhis is sample textyZXXXX"]
    blocksize = 5

    def makeFile(self,contents,mode):
        f = UnPadToBlockSize(StringIO(""),self.blocksize,mode=mode)
        s = StringIO(contents + f._padding(contents))
        f._fileobj = s
        def getvalue():
            val = s.getvalue()
            idx = val.rfind("Z")
            return val[:idx]
        f.getvalue = getvalue
        return f

    def test_padding(self):
        for (plain,padded) in zip(self.text_plain,self.text_padded):
            f = self.makeFile(plain,"rw")
            self.assertEquals(f._fileobj.getvalue(),padded)

    def test_write_zeds(self):
        f = self.makeFile("","w")
        txt = "test data Z with lots of Z's embedded in it Z"
        f.write("test data Z w")
        f.write("ith lots of Z's e")
        f.write("mbedded in it Z")
        f.flush()
        self.assertEquals(f._fileobj.getvalue(),txt + f._padding(txt))

    def test_read_zeds(self):
        f = self.makeFile("","r")
        txt = "test data Z with lots of Z's embedded in it Z"
        f._fileobj = StringIO(txt + f._padding(txt))
        self.assertEquals(f.read(),txt)


class Test_UnPadToBlockSize7(Test_UnPadToBlockSize5):
    """Testcases for UnPadToBlockSize with blocksize=7."""

    contents = "this is som\n sample text"
    text_plain = ["Zhis is sample texty"]
    text_padded = ["Zhis is sample textyZ"]
    blocksize = 7


class Test_UnPadToBlockSize8(Test_UnPadToBlockSize5):
    """Testcases for UnPadToBlockSize with blocksize=7."""

    contents = "this text is a multiple of eight"
    text_plain = ["Zhis is sample texty"]
    text_padded = ["Zhis is sample textyZXXX"]
    blocksize = 8


class Test_UnPadToBlockSize16(Test_UnPadToBlockSize5):
    """Testcases for UnPadToBlockSize with blocksize=16."""

    contents = "This is Zome Zample TeZTZ"
    text_plain = ["short"]
    text_padded = ["shortZXXXXXXXXXX"]
    blocksize = 16

