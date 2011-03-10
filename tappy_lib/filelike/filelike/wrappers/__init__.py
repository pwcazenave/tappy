# filelike/wrappers/__init__.py
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

    filelike.wrappers:  wrapper classes modifying file-like objects
    
This module builds on the basic functionality of the filelike module to
provide a collection of useful classes.  These include:
    
    * Translate:  pass file contents through an arbitrary translation
                  function (e.g. compression, encryption, ...)
                  
    * Decrypt:    on-the-fly reading and writing to an encrypted file
                  (using PEP272 cipher API)

    * UnBZip2:    on-the-fly decompression of bzip'd files
                  (like the standard library's bz2 module, but accepts
                  any file-like object)
 
As an example of the type of thing this module is designed to achieve, here's
how to use the Decrypt wrapper to transparently access an encrypted file:
    
    # Create the decryption key
    from Crypto.Cipher import DES
    cipher = DES.new('abcdefgh',DES.MODE_ECB)
    # Open the encrypted file
    f = Decrypt(file("some_encrypted_file.bin","r"),cipher)
    
The object in 'f' now behaves as a file-like object, transparently decrypting
the file on-the-fly as it is read.

""" 

import filelike
from filelike import FileLikeBase


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
    which just calls read() and write() on the wrapped object.  Subclasses
    will probably want to override these.
    """

    _append_requires_overwrite = False

    def __init__(self,fileobj,mode=None):
        """FileWrapper constructor.
        
        'fileobj' must be a file-like object, which is to be wrapped
        in another file-like object to provide additional functionality.
        
        If given, 'mode' must be the access mode string under which
        the wrapped file is to be accessed.  If not given or None, it
        is looked up on the wrapped file if possible.  Otherwise, it
        is not set on the object.
        """
        # This is used for working around flush/close inefficiencies
        self._closing = False
        super(FileWrapper,self).__init__()
        self._fileobj = fileobj
        if mode is None:
            self.mode = getattr(fileobj,"mode","r+")
        else:
            self.mode = mode
        self._validate_mode()
        # Copy useful attributes of the fileobj
        if hasattr(fileobj,"name"):
            self.name = fileobj.name
        # Respect append-mode setting
        if "a" in self.mode:
            if self._check_mode("r"):
                self._fileobj.seek(0)
            self.seek(0,2)

    def _validate_mode(self):
        """Check that various file-mode conditions are satisfied."""
        #  If append mode requires overwriting the underlying file,
        #  if must not be opened in append mode.
        if self._append_requires_overwrite:
            if self._check_mode("w"):
                if "a" in getattr(self._fileobj,"mode",""):
                    raise ValueError("Underlying file can't be in append mode")

    def __del__(self):
        #  Errors in subclass constructors could result in this being called
        #  without invoking FileWrapper.__init__.  Establish some simple
        #  invariants to prevent errors in this case.
        if not hasattr(self,"_fileobj"):
            self._fileobj = None
        if not hasattr(self,"_closing"):
            self._closing = False
        #  Close the wrapper and the underlying file independently, so the
        #  latter is still closed on cleanup even if the former errors out.
        try:
            super(FileWrapper,self).close()
        except Exception:
            if hasattr(getattr(self,"_fileobj",None),"close"):
                self._fileobj.close()
            raise
        
    def close(self):
        """Close the object for reading/writing."""
        #  The superclass implementation of this will call flush(),
        #  which calls flush() on our wrapped object.  But we then call
        #  close() on it, which will call its flush() again!  To avoid
        #  this inefficiency, our flush() will not flush the wrapped
        #  fileobj when we're closing.
        self._closing = True
        super(FileWrapper,self).close()
        if hasattr(self._fileobj,"close"):
            self._fileobj.close()

    def flush(self):
        """Flush the write buffers of the file."""
        super(FileWrapper,self).flush()
        if not self._closing and hasattr(self._fileobj,"flush"):
            self._fileobj.flush()
    
    def _read(self,sizehint=-1):
        data = self._fileobj.read(sizehint)
        if data == "":
            return None
        return data

    def _write(self,string,flushing=False):
        return self._fileobj.write(string)

    def _seek(self,offset,whence):
        self._fileobj.seek(offset,whence)

    def _tell(self):
        return self._fileobj.tell()

    def _truncate(self,size):
        return self._fileobj.truncate(size)

##  Import the various classes from our sub-modules.

from filelike.wrappers.debug import Debug

from filelike.wrappers.translate import Translate, BytewiseTranslate

from filelike.wrappers.fixedblocksize import FixedBlockSize

from filelike.wrappers.padtoblocksize import PadToBlockSize, UnPadToBlockSize

from filelike.wrappers.crypto import Encrypt, Decrypt

from filelike.wrappers.buffer import Buffer, FlushableBuffer

from filelike.wrappers.compress import BZip2, UnBZip2

from filelike.wrappers.unix import Head

from filelike.wrappers.slice import Slice

