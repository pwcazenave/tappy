# filelike.py
#
# Copyright (C) 2006, Ryan Kelly
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#
"""

    filelike.wrappers:  wrapper classes modifying file-like objects
    

This module builds on the basic functionality of the filelike module to
provide a collection of useful classes.  These include:
    
    * TransFile:  pass file contents through an arbitrary translation
                  function (e.g. compression, encryption, ...)
                  
    * FixedBlockSizeFile:  ensure all read/write requests are aligned with
                           a given blocksize
                           
    * DecryptFile:    on-the-fly reading and writing to an encrypted file
                      (using PEP272 cipher API)

    * BZ2File:    on-the-fly decompression of bzip'd files
                  (like the standard library's bz2 module, but accepts
                   any file-like object)
 
As an example of the type of thing this module is designed to achieve, here's
an example of using the DecryptFile class to transparently access an encrypted
file:
    
    # Create the decryption key
    from Crypto.Cipher import DES
    cipher = DES.new('abcdefgh',DES.MODE_ECB)
    # Open the encrypted file
    f = DecryptFile(file("some_encrypted_file.bin","r"),cipher)
    
The object in <f> now behaves as a file-like object, transparently decrypting
the file on-the-fly as it is read.

""" 

from filelike import FileLikeBase

import unittest
import StringIO
import bz2



class FileWrapper(FileLikeBase):
    """Base class for objects that wrap a file-like object.
    
    This class provides basic functionality for implementing file-like
    objects that wrap another file-like object to alter its functionality
    in some way.  It takes care of house-keeping duties such as flushing
    and closing the wrapped file.

    Access to the wrapped file is given by the private member _fileobj.
    By convention, the subclass's constructor should accept this as its
    first argument and pass it to its superclass's constructor in the
    same position.
    
    This class provides a basic implementation of _read() and _write()
    which just calls read() and write() on the wrapped object.  Many
    subclasses will probably want to override these.
    """
    
    def __init__(self,fileobj,mode=None):
        """FileWrapper constructor.
        
        <fileobj> must be a file-like object, which is to be wrapped
        in another file-like object to provide additional functionality.
        
        If given, <mode> must be the access mode string for with which
        the wrapped file is to be accessed.  If not given or None, it
        is looked up on the wrapped file if possible.  Otherwise, it
        is not set on the object.
        """
        FileLikeBase.__init__(self)
        self._fileobj = fileobj
        if mode is None:
            if hasattr(fileobj,"mode"):
                self.mode = fileobj.mode
        else:
            self.mode = mode
        # Copy useful attributes of the fileobj
        if hasattr(fileobj,"name"):
            self.name = fileobj.name
        
    def close(self):
        """Close the object for reading/writing."""
        FileLikeBase.close(self)
        if hasattr(self._fileobj,"close"):
            self._fileobj.close()

    def flush(self):
        """Flush the write buffers of the file."""
        FileLikeBase.flush(self)
        if hasattr(self._fileobj,"flush"):
            self._fileobj.flush()
    
    def _read(self,sizehint=-1):
        data = self._fileobj.read(sizehint)
        if data == "":
            return None
        return data

    def _write(self,string):
        return self._fileobj.write(string)


class TransFile(FileWrapper):
    """Class implementing some translation on a file's contents.
    
    This class wraps a file-like object in another file-like object,
    applying a given function to translate the file's contents as it is
    read or written.  It could be used, for example, to read from a 
    gzipped source file or to encrypt a file as it's being written.
    
    The translating function must accept a string as its only argument,
    and return a transformed string representing the updated file contents.
    No guarantees are made about the amount of data fed into the function
    at a time (although another wrapper like FixedBlockSizeFile could be
    used to do so.)  If the transform needs to be flushed when reading/writing
    is finished, it should provide a flush() method that returns either None,
    or any data remaining to be read/written.
    
    The default use case assumes either reading+writing with a stateless
    translation function, or exclusive reading or writing.  So, a single
    function is used for translation on both reads and writes.  Seperate
    reading and writing translation functions may be provided using keyword
    arguments <rfunc> and <wfunc> to the constructor.
    """
    
    def __init__(self,fileobj,func=None,mode=None,rfunc=None,wfunc=None):
        """TransFile constructor.
        <fileobj> must be the file-like object whose contents are to be
        transformed, and <func> the callable that will transform the
        contents.  <mode> should be one of "r" or "w" to indicate whether
        reading or writing is desired.  If omitted it is determined from
        <fileobj> where possible, otherwise it defaults to "r".
        
        If seperate reading/writing translations are required, the
        keyword arguments <rfunc> and <wfunc> can be used in place of
        <func>
        """
        FileWrapper.__init__(self,fileobj,mode)
        self._finished = False
        if func is not None:
            if rfunc is not None:
                raise ValueError("Cannot specify both <func> and <rfunc>")
            if wfunc is not None:
                raise ValueError("Cannot specify both <func> and <wfunc>")
            self._rfunc = func
            self._wfunc = func
        else:
            if "r" in self.mode and rfunc is None:
                raise ValueError("Must provide <rfunc> for readable files")
            if "w" in self.mode or "a" in self.mode:
                if wfunc is None:
                   raise ValueError("Must provide <wfunc> for writable files")
            self._rfunc = rfunc
            self._wfunc = wfunc
            
    
    def _flush_rfunc(self):
        """Call flush on the reading translation function, if necessary."""
        if hasattr(self._rfunc,"flush"):
            return self._rfunc.flush()
        return None
   
    def _flush_wfunc(self):
        """Call flush on the writing translation function, if necessary."""
        if hasattr(self._wfunc,"flush"):
            return self._wfunc.flush()
        return 

    def _read(self,sizehint=-1):
        """Read approximately <sizehint> bytes from the file."""
        if self._finished:
            return None
        if sizehint <= 0:
            sizehint = 100
        data = self._fileobj.read(sizehint)
        if data == "":
            self._finished = True
            # Flush func if necessary
            data = self._flush_rfunc()
            return data
        data = self._rfunc(data)
        return data
    
    def _write(self,data):
        """Write the given data to the file."""
        self._fileobj.write(self._wfunc(data))

    def flush(self):
        # Flush func if necessary, when writing
        data = self._flush_wfunc()
        if data is not None:
            self._fileobj.write(data)
        FileWrapper.flush(self)


class Test_TransFile(unittest.TestCase):
    """Testcases for the TransFile class."""
    
    def setUp(self):
        import StringIO
        self.testlines = ["this is a simple test\n"," file with a\n"," few lines."]
        self.testfileR = StringIO.StringIO("".join(self.testlines))
        self.testfileW = StringIO.StringIO()
        def noop(string):
            return string
        self.f_noop = noop
    
    def tearDown(self):
        del self.testfileR
        del self.testfileW

    def test_read(self):
        """Test reading the entire file"""
        tf = TransFile(self.testfileR,self.f_noop,"r")
        self.assert_(tf.read() == "".join(self.testlines))

    def test_readbytes(self):
        """Test reading a specific number of bytes"""
        tf = TransFile(self.testfileR,self.f_noop,"r")
        self.assert_(tf.read(10) == "".join(self.testlines)[:10])
        
    def test_readlines(self):
        """Test reading lines one at a time."""
        tf = TransFile(self.testfileR,self.f_noop,"r")
        self.assert_(tf.readlines() == self.testlines)
    
    def test_write(self):
        """Test basic behavior of writing to a file."""
        tf = TransFile(self.testfileW,self.f_noop,"w")
        tf.write("".join(self.testlines))
        self.assert_(self.testfileW.getvalue() == "".join(self.testlines))
    
    def test_writelines(self):
        """Test writing several lines with writelines()."""
        tf = TransFile(self.testfileW,self.f_noop,"w")
        tf.writelines(self.testlines)
        self.assert_(self.testfileW.getvalue() == "".join(self.testlines))
        

class FixedBlockSizeFile(FileWrapper):
    """Class reading/writing to files at a fixed block size.
    
    This file wrapper can be used to read or write to a file-like
    object at a specific block size.  All reads request strings
    whose length is a multiple of the block size, and all writes
    pass on strings of a similar nature.  This could be useful, for
    example, to write data to a cipher function without manually 
    chunking text to match the cipher's block size.
    
    If the total data written to the file when it is flushed or closed
    is not a multiple of the blocksize, it will be padded to the
    appropriate size with null bytes.
    """
    
    def __init__(self,fileobj,blocksize,mode=None):
        FileWrapper.__init__(self,fileobj,mode)
        self._blocksize = blocksize
    
    def _round_up(self,num):
        """Round <num> up to a multiple of the block size."""
        return ((num/self._blocksize)+1) * self._blocksize
    
    def _round_down(self,num):
        """Round <num> down to a multiple of the block size."""
        return (num/self._blocksize) * self._blocksize

    def _pad_to_size(self,data):
        """Add padding data to make it an appropriate size."""
        size = self._round_up(len(data))
        if len(data) < size:
            data = data + ("\0"*(size-len(data)))
        return data
    
    def _read(self,sizehint=-1):
        """Read approximately <sizehint> bytes from the file."""
        if sizehint <= 0:
            sizehint = 100
        size = self._round_up(sizehint)
        data = self._fileobj.read(size)
        if data == "":
            return None
        return data

    def _write(self,data,flushing=False):
        """Write the given string to the file."""
        # Pad the data if the buffers are being flushed
        if flushing:
            data = self._pad_to_size(data)
            size = len(data)
        else:
            size = self._round_down(len(data))
        self._fileobj.write(data[:size])
        return data[size:]



class Test_FixedBlockSizeFile(unittest.TestCase):
    """Testcases for the FixedBlockSize class."""
    
    def setUp(self):
        import StringIO
        class BSFile:
            def __init__(s,bs):
                s.bs = bs
            def read(s,size=-1):
                self.assert_(size > 0)
                self.assert_(size%s.bs == 0)
                return "X"*size
            def write(s,data):
                self.assert_(len(data)%s.bs == 0)
        self.BSFile = BSFile
    
    def tearDown(self):
        del self.BSFile

    def test_readbytes(self):
        """Test reading different numbers of bytes"""
        bsf = FixedBlockSizeFile(self.BSFile(8),8)
        self.assert_(len(bsf.read(5)) == 5)
        self.assert_(len(bsf.read(8)) == 8)
        self.assert_(len(bsf.read(76)) == 76)
        bsf = FixedBlockSizeFile(self.BSFile(5),5)
        self.assert_(len(bsf.read(5)) == 5)
        self.assert_(len(bsf.read(8)) == 8)
        self.assert_(len(bsf.read(76)) == 76)
            
    def test_write(self):
        """Test writing different numbers of bytes"""
        bsf = FixedBlockSizeFile(self.BSFile(8),8)
        bsf.write("this is some text, it is")
        bsf.write("shrt")
        bsf.flush()
        bsf.write("longer text, with some\n newlines in it\n yessir.")   
        bsf.close() 


class PaddedToBlockSizeFile(FileWrapper):
    """Class padding files to a fixed block size.
    
    This file wrapper can be used to pad a file to a specific block size.
    If the total data written to the file when it is flushed or closed
    is not a multiple of the blocksize, it will be padded to the
    appropriate size by writing the following data:
    
        * Two null bytes
        * "PaddedToBlockSizeFile"
        * Enough null bytes to fit the block size
        
    This data is removed from the end of the file if it is encoutered
    upon reading.
    
    No guarantee is made that reads or writes are requsted at the
    blocksize - use FixedBlockSizeFile to achieve this.
    """
    
    _padstr = "\0\0PaddedToBlockSizeFile"
    
    def __init__(self,fileobj,blocksize,mode=None):
        FileWrapper.__init__(self,fileobj,mode)
        self._blocksize = blocksize
        self._maxpadlen = len(self._padstr) + blocksize-1
        self._padwritten = False
    
    def _round_up(self,num):
        """Round <num> up to a multiple of the block size."""
        nm = ((num/self._blocksize)+1) * self._blocksize
        if nm == num + self._blocksize:
            return num
        return nm
    
    def _round_down(self,num):
        """Round <num> down to a multiple of the block size."""
        return (num/self._blocksize) * self._blocksize
    
    def _pad_to_size(self,data):
        """Pad data to make it an appropriate size."""
        data = data + self._padstr
        size = self._round_up(len(data))
        if len(data) < size:
            data = data + ("\0"*(size-len(data)))
        return data
    
    def _read(self,sizehint=-1):
        """Read approximately <sizehint> bytes from the file."""
        data = self._fileobj.read(sizehint)
        # If we might be near the end, read far enough ahead to see
        while "\0" in data[-1*self._maxpadlen:]:
            newData = self._fileobj.read(self._maxpadlen)
            data = data + newData
            idx = data.rfind(self._padstr)
            if idx != -1:
                data = data[:idx]
                break
            if newData == "":
                break
        if data == "":
            return None
        return data

    def _write(self,data,flushing=False):
        """Write the given string to the file."""
        # Writing at the block size means we dont have to count bytes written
        # Pad the data if the buffers are being flushed
        if flushing:
            if self._padwritten:
                size = 0
                data = ""
            else:
                data = self._pad_to_size(data)
                size = len(data)
                self._padwritten = True
        else:
            size = self._round_down(len(data))
        self._fileobj.write(data[:size])
        return data[size:]

    def flush(self):
        FileWrapper.flush(self)
        if not self._padwritten:
            self._write("",flushing=True)


class Test_PaddedToBlockSizeFile(unittest.TestCase):
    """Testcases for the PaddedToBlockSizeFile class."""
    
    def setUp(self):
        import StringIO
        self.textin = "this is sample text"
        self.textout5 = "this is sample text\0\0PaddedToBlockSizeFile\0\0\0"
        self.textout7 = "this is sample text\0\0PaddedToBlockSizeFile"
        self.outfile = StringIO.StringIO()
    
    def tearDown(self):
        del self.outfile

    def test_write5(self):
        """Test writing at blocksize=5"""
        bsf = PaddedToBlockSizeFile(self.outfile,5,mode="w")
        bsf.write(self.textin)
        bsf.flush()
        self.assertEquals(self.outfile.getvalue(),self.textout5)

    def test_write7(self):
        """Test writing at blocksize=7"""
        bsf = PaddedToBlockSizeFile(self.outfile,7,mode="w")
        bsf.write(self.textin)
        bsf.flush()
        self.assertEquals(self.outfile.getvalue(),self.textout7)
    
    def test_read5(self):
        """Test reading at blocksize=5"""
        inf = StringIO.StringIO(self.textout5)
        bsf = PaddedToBlockSizeFile(inf,5,mode="r")
        txt = bsf.read()
        self.assertEquals(txt,self.textin)
        
    def test_read7(self):
        """Test reading at blocksize=7"""
        inf = StringIO.StringIO(self.textout7)
        bsf = PaddedToBlockSizeFile(inf,7,mode="r")
        txt = bsf.read()
        self.assertEquals(txt,self.textin)


class DecryptFile(FileWrapper):
    """Class for reading and writing to an encrypted file.
    
    This class accesses an encrypted file using a ciphering object
    compliant with PEP272: "API for Block Encryption Algorithms".
    All reads from the file are automatically decrypted, while writes
    to the file and automatically encrypted.  Thus, DecryptFile(fobj)
    can be seen as the decrypted version of the file-like object fobj.
    
    Because this class is implemented on top of FixedBlockSizeFile,
    the plaintext may be padded with null characters to reach a multiple
    of the block size.
    
    There is a dual class, EncryptFile, where all reads are encrypted
    and all writes are decrypted.  This would be used, for example, to
    encrypt the contents of an existing file using a series of read()
    operations.
    """

    def __init__(self,fileobj,cipher,mode=None):
        """DecryptFile Constructor.
        <fileobj> is the file object with encrypted contents, and <cipher>
        is the cipher object to be used.  Other arguments are passed through
        to FileWrapper.__init__
        """
        self.__cipher = cipher
        myFileObj = TransFile(fileobj,mode=mode,
                                      rfunc=cipher.decrypt,
                                      wfunc=cipher.encrypt)
        myFileObj = FixedBlockSizeFile(myFileObj,cipher.block_size)
        FileWrapper.__init__(self,myFileObj)


class EncryptFile(FileWrapper):
    """Class for reading and writing to an decrypted file.
    
    This class accesses a decrypted file using a ciphering object
    compliant with PEP272: "API for Block Encryption Algorithms".
    All reads from the file are automatically encrypted, while writes
    to the file are automatically decrypted.  Thus, DecryptFile(fobj)
    can be seen as the encrypted version of the file-like object fobj.

    Because this class is implemented on top of FixedBlockSizeFile,
    the plaintext may be padded with null characters to reach a multiple
    of the block size.
    
    There is a dual class, DecryptFile, where all reads are decrypted
    and all writes are encrypted.  This would be used, for example, to
    decrypt the contents of an existing file using a series of read()
    operations.
    """

    def __init__(self,fileobj,cipher,mode=None):
        """EncryptFile Constructor.
        <fileobj> is the file object with decrypted contents, and <cipher>
        is the cipher object to be used.  Other arguments are passed through
        to FileWrapper.__init__
        """
        self.__cipher = cipher
        myFileObj = TransFile(fileobj,mode=mode,
                                      rfunc=self.__encrypt,
                                      wfunc=cipher.decrypt)
        myFileObj = FixedBlockSizeFile(myFileObj,cipher.block_size)
        FileWrapper.__init__(self,myFileObj)
    
    def __encrypt(self,data):
        """Encrypt the given data.
        This function pads any data given that is not a multiple of
        the cipher's blocksize.  Such a case would indicate that it
        is the last data to be read.
        """
        if len(data) % self.__cipher.block_size != 0:
            data = self._fileobj._pad_to_size(data)
        return self.__cipher.encrypt(data)


class Test_CryptFiles(unittest.TestCase):
    """Testcases for the (En/De)CryptFile classes."""
    
    def setUp(self):
        import StringIO
        from Crypto.Cipher import DES
        # Example inspired by the PyCrypto manual
        self.cipher = DES.new('abcdefgh',DES.MODE_ECB)
        self.plaintextin = "Guido van Rossum is a space alien."
        self.plaintextout = "Guido van Rossum is a space alien." + "\0"*6
        self.ciphertext = "\x11,\xe3Nq\x8cDY\xdfT\xe2pA\xfa\xad\xc9s\x88\xf3,\xc0j\xd8\xa8\xca\xe7\xe2I\xd15w\x1d\xfe\x92\xd7\xca\xc9\xb5r\xec"
        self.plainfile = StringIO.StringIO(self.plaintextin)
        self.cryptfile = StringIO.StringIO(self.ciphertext)
        self.outfile = StringIO.StringIO()

    def tearDown(self):
        pass

    def test_ReadDecrypt(self):
        """Test reading from an encrypted file."""
        df = DecryptFile(self.cryptfile,self.cipher,"r")
        self.assert_(df.read() == self.plaintextout)

    def test_ReadEncrypt(self):
        """Test reading from a decrypted file."""
        ef = EncryptFile(self.plainfile,self.cipher,"r")
        self.assert_(ef.read() == self.ciphertext)
    
    def test_WriteDecrypt(self):
        """Test writing to an encrypted file."""
        df = DecryptFile(self.outfile,self.cipher,"w")
        df.write(self.plaintextin)
        df.flush()
        self.assert_(self.outfile.getvalue() == self.ciphertext)
        
    def test_WriteEncrypt(self):
        """Test writing to a decrypted file."""
        ef = EncryptFile(self.outfile,self.cipher,"w")
        ef.write(self.ciphertext)
        self.assert_(self.outfile.getvalue() == self.plaintextout)


class Head(FileWrapper):
    """Wrapper acting like unix "head" command.
    
    This wrapper limits the amount of data read or written to the
    underlying file based on the number of bytes and/or lines.
    """
    
    def __init__(self,fileobj,mode=None,bytes=None,lines=None):
        """Head wrapper constructor.
        The arguments <bytes> and <lines> specify the maximum number
        of bytes and lines to be read or written.  Reading/writing
        will terminate when one of the given values has been exceeded.
        Any extraneous data is simply discarded.
        """
        FileWrapper.__init__(self,fileobj,mode)
        self._maxBytes = bytes
        self._maxLines = lines
        self._bytesR = 0
        self._linesR = 0
        self._bytesW = 0
        self._linesW = 0
        self._finishedR = False
        self._finishedW = False
    
    # TODO: limit amount requested to byte limit
    def _read(self,sizehint=-1):
        if self._finishedR:
            return None
        if sizehint <= 0 or sizehint > 100:
            sizehint = 100
        data = self._fileobj.read(sizehint)
        if data == "":
            self._finishedR = True
            return data
        nBytes = len(data)
        newBytes = self._bytesR + nBytes
        if self._maxBytes is not None and newBytes >= self._maxBytes:
            data = data[:self._maxBytes - self._bytesR]
            self._finishedR = True
        nLines = data.count("\n")
        newLines = self._linesR + nLines
        if self._maxLines is not None and newLines >= self._maxLines:
            limit = self._maxLines - self._linesR
            lines = data.split("\n")
            if len(lines) > limit:
                data = "\n".join(lines[:limit]) + "\n"
            else:
                data = "\n".join(lines[:limit])
            self._finishedR = True
        self._bytesR = newBytes
        self._linesR = newLines
        return data

    def _write(self,data):
        if self._finishedW:
            return None
        nBytes = len(data)
        nLines = data.count("\n")
        newBytes = self._bytesW + nBytes
        newLines = self._linesW + nLines
        if self._maxBytes is not None and newBytes >= self._maxBytes:
            data = data[:self._maxBytes - self._bytesW]
            self._finishedW = True
        elif self._maxLines is not None and newLines >= self._maxLines:
            limit = self._maxLines - self._linesW
            lines = data.split("\n")
            if len(lines) > limit:
                data = "\n".join(lines[:limit]) + "\n"
            else:
                data = "\n".join(lines[:limit])
            self._finishedW = True
        self._bytesW = newBytes
        self._linesW = newLines
        self._fileobj.write(data)
        return None



class Test_Head(unittest.TestCase):
    """Testcases for the Head wrapper class."""
    
    def setUp(self):
        from Crypto.Cipher import DES
        # Example inspired by the PyCrypto manual
        self.intext = "Guido van Rossum\n is a space\n alien."
        self.infile = StringIO.StringIO(self.intext)
        self.outfile = StringIO.StringIO()

    def tearDown(self):
        pass

    def test_ReadHeadBytes(self):
        """Test reading bytes from head of a file."""
        hf = Head(self.infile,"r",bytes=10)
        txt = hf.read()
        self.assertEquals(len(txt),10)
        self.assertEquals(txt,self.intext[:10])
    
    def test_ReadHeadLongBytes(self):
        """Test reading entirety of head of file."""
        hf = Head(self.infile,"r",bytes=1000)
        txt = hf.read()
        self.assertEquals(txt,self.intext)
    
    def test_ReadHeadLines(self):
        """Test reading lines from head of file."""
        hf = Head(self.infile,"r",lines=2)
        txt = hf.read()
        self.assertEquals(txt.count("\n"),2)
        self.assertEquals(txt,"\n".join(self.intext.split("\n")[:2])+"\n")

    def test_ReadHeadLinesExact(self):
        """Test reading exact number of lines from head of file."""
        hf = Head(self.infile,"r",lines=3)
        txt = hf.read()
        self.assertEquals(txt.count("\n"),2)
        self.assertEquals(txt,self.intext)

    def test_ReadHeadLongLines(self):
        """Test reading all lines from head of file."""
        hf = Head(self.infile,"r",lines=200)
        txt = hf.read()
        self.assertEquals(txt,self.intext)
        
    def test_ReadBytesOverLines(self):
        """Test reading limited by bytes, not lines"""
        hf = Head(self.infile,"r",bytes=5,lines=2)
        txt = hf.read()
        self.assertEquals(len(txt),5)
        self.assertEquals(txt,self.intext[:5])
        
    def test_ReadLinesOverBytes(self):
        """Test reading limited by lines, not bytes"""
        hf = Head(self.infile,"r",bytes=500,lines=1)
        txt = hf.read()
        self.assertEquals(txt.count("\n"),1)
        self.assertEquals(txt,self.intext.split("\n")[0]+"\n")

    def test_WriteHeadBytes(self):
        """Test writing bytes to head of a file."""
        hf = Head(self.outfile,"w",bytes=10)
        hf.write(self.intext)
        self.assertEquals(len(self.outfile.getvalue()),10)
        self.assertEquals(self.outfile.getvalue(),self.intext[:10])
    
    def test_WriteHeadLongBytes(self):
        """Test writing entirety of head of file."""
        hf = Head(self.outfile,"w",bytes=1000)
        hf.write(self.intext)
        self.assertEquals(self.outfile.getvalue(),self.intext)
    
    def test_WriteHeadLines(self):
        """Test writing lines to head of file."""
        hf = Head(self.outfile,"w",lines=2)
        hf.write(self.intext)
        self.assertEquals(self.outfile.getvalue().count("\n"),2)
        self.assertEquals(self.outfile.getvalue(),"\n".join(self.intext.split("\n")[:2])+"\n")

    def test_WriteHeadLongLines(self):
        """Test writing all lines to head of file."""
        hf = Head(self.outfile,"w",lines=200)
        hf.write(self.intext)
        self.assertEquals(self.outfile.getvalue(),self.intext)
        
    def test_WriteBytesOverLines(self):
        """Test writing limited by bytes, not lines"""
        hf = Head(self.outfile,"w",bytes=5,lines=2)
        hf.write(self.intext)
        txt = self.outfile.getvalue()
        self.assertEquals(len(txt),5)
        self.assertEquals(txt,self.intext[:5])
        
    def test_writeLinesOverBytes(self):
        """Test writing limited by lines, not bytes"""
        hf = Head(self.outfile,"w",bytes=500,lines=1)
        hf.write(self.intext)
        txt = self.outfile.getvalue()
        self.assertEquals(txt.count("\n"),1)
        self.assertEquals(txt,self.intext.split("\n")[0]+"\n")


class Cat(FileWrapper):
    """Class concatenation several file-like objects.
    
    This is similar in functionality to the unix `cat` command.
    Data is read from each file in turn, until all have been
    exhausted.
    
    Since this doesnt make sense when writing to a file, the access
    mode is assumed to be "r" and cannot be set or modified. Each
    file is closed at the time of closing the wrapper.
    """
    
    def __init__(self,*files):
        """Cat wrapper constructor.
        This function accepts any number of file-like objects as its
        only arguments.  Data will be read from them in the order they
        are provided.
        """
        FileWapper.__init__(self,None,"r")
        self._files = files
        self._curFile = 0
    
    def close(self):
        FileWrapper.close(self)
        for f in self._files:
            if hasattr(f,"close"):
                f.close()
    
    def _read(self,sizehint=-1):
        if len(self._files) >= self._curFile:
            return None
        data = self._curFile.read(sizehint)
        if data == "":
            self._curFile += 1
            data = self._read(sizehint)
        return data
    
    def _write(self,data):
        raise IOError("Cat wrappers cannot be written to.")


class BZ2File(FileWrapper):
    """Class for reading and writing to a bziped file.
    
    This class behaves almost exactly like the bz2.BZ2File class from
    the standard library, except that it accepts an arbitrary file-like
    object and it does not support seek() or tell().
    
    All reads from the file as decompressed, all writes are compressed.
    """

    def __init__(self,fileobj,mode=None,buffering=0,compresslevel=9):
        """BZ2File Constructor.
        <fileobj> is the file object with compressed contents.  <mode>
        is the file access mode.  <buffering> is an integer specifying
        the buffer size, and <compresslevel> an integer between 1 and 9
        giving the compression level.
        
        Note that it doesnt make sense to open such a file for both
        reading and writing, so mode should be restricted to either
        "r" or "w".
        """
        # TODO: shall we just ignore <buffering>?
        self.__compressor = bz2.BZ2Compressor(compresslevel)
        self.__decompressor = bz2.BZ2Decompressor()
        def wfunc(data):
            return self.__compressor.compress(data)
        def wflush():
            # Make flush() safe to call multiple times
            data = self.__compressor.flush()
            del wfunc.flush
            return data
        wfunc.flush = wflush
        def rfunc(data):
            return self.__decompressor.decompress(data)
        myFileObj = TransFile(fileobj,mode=mode,
                                      rfunc=rfunc,
                                      wfunc=wfunc)
        FileWrapper.__init__(self,myFileObj)



def testsuite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test_TransFile))
    suite.addTest(unittest.makeSuite(Test_FixedBlockSizeFile))
    suite.addTest(unittest.makeSuite(Test_CryptFiles))
    suite.addTest(unittest.makeSuite(Test_Head))
    suite.addTest(unittest.makeSuite(Test_PaddedToBlockSizeFile))
    return suite
        

# Run regression tests when called from comand-line
if __name__ == "__main__":
    UnitTest.TextTestRunner().run(testsuite())