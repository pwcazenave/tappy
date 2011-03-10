# filelike/wrappers/compress.py
#
# Copyright (C) 2006-2009, Ryan Kelly
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

    filelike.wrappers.compress:  wrapper classes handling compressed files
    
This module provides the filelike wrappers 'BZip2' and 'UnBZip2' for dealing
with files compressed in bz2 format.  It also provides some base classes for
building other compression wrappers.

""" 

import filelike
from filelike.wrappers import FileWrapper
from filelike.wrappers.translate import Translate
from filelike.wrappers.buffer import FlushableBuffer

import bz2

class Decompress(FileWrapper):
    """Abstract base class for decompressing files.

    Instances of this class represent the decompressed version of a file - 
    all data read from the file is decompressed on demand, and all data
    written to the file is compressed.

    Subclases must provide compress() and decompress() methods.
    """

    def __init__(self,fileobj,mode=None):
        if mode is None:
            try:
                mode = fileobj.mode
            except AtributeError:
                mode = "r+"
        myFileObj = None
        if "r" in mode:
            if "w" not in mode and "a" not in mode and "+" not in mode:
                # Nice and easy, just a streaming decompress on read
                myFileObj = Translate(fileobj,mode=mode,rfunc=self.decompress)
        else:
            if "-" in mode:
                # Nice and easy, just a streaming compress on write
                myFileObj = Translate(fileobj,mode=mode,wfunc=self.compress)
        if not myFileObj:
            # Rats, writing + seekabilty == inefficient.
            # Operating in a buffer is the only sensible option
            myFileObj = Translate(fileobj,mode=mode,rfunc=self.decompress,wfunc=self.compress)
            myFileObj = FlushableBuffer(myFileObj,mode=mode)
        super(Decompress,self).__init__(myFileObj,mode=mode)

    def _read(self,sizehint=-1):
        data = super(Decompress,self)._read(sizehint)
        return data


class Compress(FileWrapper):
    """Abstract base class for compressing files.

    Instances of this class represent the compressed version of a file - 
    all data read from the file is compressed on demand, and all data
    written to the file is decompressed.

    Subclases must provide compress() and decompress() methods.
    """

    def __init__(self,fileobj,mode=None):
        if mode is None:
            try:
                mode = fileobj.mode
            except AtributeError:
                mode = "r+"
        myFileObj = None
        if "r" in mode:
            if "w" not in mode and "a" not in mode and "+" not in mode:
                # Nice and easy, just a streaming compress on read
                myFileObj = Translate(fileobj,mode=mode,rfunc=self.compress)
        else:
            if "-" in mode:
                # Nice and easy, just a streaming decompress on write
                myFileObj = Translate(fileobj,mode=mode,wfunc=self.decompress)
        if not myFileObj:
            # Rats, writing + seekabilty == inefficient
            # Operating in a buffer is the only sensible option
            myFileObj = Translate(fileobj,mode=mode,rfunc=self.compress,wfunc=self.decompress)
            myFileObj = FlushableBuffer(myFileObj,mode=mode)
        super(Compress,self).__init__(myFileObj,mode=mode)


class BZip2Mixin(object):
    """Mixin for Compress/Decompress subclasses using Bzip2."""

    def __init__(self,*args,**kwds):
        if not hasattr(self,"compresslevel"):
            self.compresslevel = 9
        # Compression function with flush and reset.
        c = [bz2.BZ2Compressor()]
        def compress(data):
            if data == "":
                return ""
            return c[0].compress(data)
        def c_flush():
            return c[0].flush()
        def c_reset():
            c[0] = bz2.BZ2Compressor()
        compress.flush = c_flush
        compress.reset = c_reset
        self.compress = compress
        # Decompression funtion with reset
        d = [bz2.BZ2Decompressor()]
        def decompress(data):
            if data == "":
                return ""
            return d[0].decompress(data)
        def d_reset():
            d[0] = bz2.BZ2Decompressor()
        decompress.reset = d_reset
        self.decompress = decompress
        # These can now be used by superclass constructors
        super(BZip2Mixin,self).__init__(*args,**kwds)


class UnBZip2(BZip2Mixin,Decompress):
    """Class for reading and writing to a un-bziped file.
        
    This class behaves almost exactly like the bz2.BZ2File class from
    the standard library, except that it accepts an arbitrary file-like
    object.  All reads from the file are decompressed, all writes are
    compressed.
    """
    
    def __init__(self,fileobj,mode=None,compresslevel=9):
        self.compresslevel = compresslevel
        super(UnBZip2,self).__init__(fileobj,mode=mode)


class BZip2(BZip2Mixin,Compress):
    """Class for reading and writing a bziped file.
        
    This class is the dual of UnBZip2 - it compresses read data, and
    decompresses written data.  Thus BZip2(f) is the compressed version
    of f.
    """
    
    def __init__(self,fileobj,mode=None,compresslevel=9):
        self.compresslevel = compresslevel
        super(BZip2,self).__init__(fileobj,mode=mode)


##  Add handling of .bz2 files to filelike.open()
def _BZip2_decoder(fileobj):
    """Decoder function for handling .bz2 files with filelike.open"""
    if not fileobj.name.endswith(".bz2"):
        return None
    f = UnBZip2(fileobj)
    f.name = fileobj.name[:-4]
    return f
filelike.open.decoders.append(_BZip2_decoder)

import zlib
class GZipMixin(object):
    """Mixin for Compress/Decompress subclasses using gzip."""

    def __init__(self,*args,**kwds):
        if not hasattr(self,"compresslevel"):
            self.compresslevel = 6
        # Compression function with flush and reset.
        c = [zlib.compressobj(self.compresslevel)]
        def compress(data):
            if data == "":
                return ""
            return c[0].compress(data)
        def c_flush():
            return c[0].flush()
        def c_reset():
            c[0] = zlib.compressobj(self.compresslevel)
        compress.flush = c_flush
        compress.reset = c_reset
        self.compress = compress
        # Decompression funtion with reset
        d = [zlib.decompressobj(16+zlib.MAX_WBITS)]
        def decompress(data):
            if data == "":
                return ""
            return d[0].decompress(data)
        def d_reset():
            d[0] = zlib.compressobj(16+zlib.MAX_WBITS)
        decompress.reset = d_reset
        self.decompress = decompress
        # These can now be used by superclass constructors
        super(GZipMixin,self).__init__(*args,**kwds)


class UnGZip(GZipMixin,Decompress):
    """Class for reading and writing to a zipped file.
        
    This class behaves almost exactly like the zlib class from
    the standard library, except that it accepts an arbitrary file-like
    object.  All reads from the file are decompressed, all writes are
    compressed.
    """
    
    def __init__(self,fileobj,mode=None,compresslevel=9):
        self.compresslevel = compresslevel
        super(UnGZip,self).__init__(fileobj,mode=mode)


class GZip(GZipMixin,Compress):
    """Class for reading and writing a zipped file.
        
    This class is the dual of UnGZip - it compresses read data, and
    decompresses written data.  Thus GZip(f) is the compressed version
    of f.
    """
    
    def __init__(self,fileobj,mode=None,compresslevel=9):
        self.compresslevel = compresslevel
        super(GZip,self).__init__(fileobj,mode=mode)


##  Add handling of .gz files to filelike.open()
def _GZip_decoder(fileobj):
    """Decoder function for handling .gz files with filelike.open"""
    if not fileobj.name.endswith(".gz"):
        return None
    f = UnGZip(fileobj)
    f.name = fileobj.name[:-3]
    return f
filelike.open.decoders.append(_GZip_decoder)


class NullZipMixin(object):
    """Mixin for Compress/Decompress subclasses using NullZip."""

    def __init__(self,*args,**kwds):
        class NullCompressor(object):
            def compress(self,data):
                return data
            def decompress(self,data):
                return data
            def flush(self):
                return ""
        # Compression function with flush and reset.
        c = [NullCompressor()]
        def compress(data):
            if data == "":
                return ""
            return c[0].compress(data)
        def c_flush():
            return c[0].flush()
        def c_reset():
            c[0] = NullCompressor()
        compress.flush = c_flush
        compress.reset = c_reset
        self.compress = compress
        # Decompression funtion with reset
        d = [NullCompressor()]
        def decompress(data):
            if data == "":
                return ""
            return d[0].decompress(data)
        def d_reset():
            d[0] = NullCompressor()
        decompress.reset = d_reset
        self.decompress = decompress
        # These can now be used by superclass constructors
        super(NullZipMixin,self).__init__(*args,**kwds)


class UnNullZip(NullZipMixin,Decompress):
    """Class for reading and writing to a null-ziped file."""
    pass


class NullZip(NullZipMixin,Compress):
    """Class for reading and writing a null-ziped file."""
    pass

