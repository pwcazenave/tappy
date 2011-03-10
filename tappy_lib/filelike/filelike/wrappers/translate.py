# filelike/wrappers/translate.py
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

    filelike.wrappers.translate:  pass file contents through translation func
    
This module provides the filelike wrapper 'Translate', which passes file
data through a translation function as it is read/written.  The default mode
of operation presumes a streaming translation function, which makes operations
such as seeking, or switching between reads and writes, quite expensive.

For more efficient operation the class 'BytewiseTranslate' is provided, which
assumes that the translation takes place on a byte-by-byte basis and can 
therefore optimise these operations.

""" 

import filelike
from filelike.wrappers import FileWrapper, Debug


class Translate(FileWrapper):
    """Class implementing some translation on a file's contents.
    
    This class wraps a file-like object in another file-like object,
    applying a given function to translate the file's contents as it is
    read or written.
    
    The translating function must accept a string as its only argument,
    and return a transformed string representing the updated file contents.
    If the function is symmetric than a single function may be specified;
    to use separate functions for reading and writing, provide the two
    keyword arguments 'rfunc' and 'wfunc'.

    If the transform needs to be flushed when reading/writing is finished, it
    should provide a flush() method that returns either None, or any data
    remaining to be read/written.  If it needs to be reset after flushing,
    it should provide a reset() method.

    If the translation function operates on a byte-by-byte basis and
    does not buffer any data, consider using the 'BytewiseTranslate'
    class instead; the efficiency of several operations can be improved
    dramatically given such properties of the translation function.
    """

    _append_requires_overwrite = True
    
    def __init__(self,fileobj,rfunc=None,wfunc=None,mode=None):
        """Translate file wrapper constructor.

        'fileobj' must be the file-like object whose contents are to be
        transformed, and 'rfunc' and 'wfunc' the callable objects that will
        transform the file's contents.
        """
        if mode is None:
            mode = getattr(fileobj,"mode","r+")
        # rfunc must be provided for readable files
        if self._check_mode("r-",mode):
            if rfunc is None:
                raise ValueError("Must provide 'rfunc' for readable files")
        # wfunc should be given for writable files, but we default to
        # using rfunc if it is specified.
        if self._check_mode("w-",mode):
            if wfunc is None:
                if rfunc is None:
                    raise ValueError("Must provide 'wfunc' for writable files")
                wfunc = rfunc
        self._rfunc = self._normalise_func(rfunc)
        self._wfunc = self._normalise_func(wfunc)
        self._pos = 0
        self._read_eof = False
        super(Translate,self).__init__(fileobj,mode)

    def _normalise_func(self,func):
        """Adjust a function to support flush() and reset() methods.

        This avoids the need to constantly check for these methods
        before invoking them.
        """
        def mknoop():
            def noop():
                return None
            return noop
        if func is None:
            func = mknoop()
        if not hasattr(func,"flush"):
            func.flush = mknoop()
        if not hasattr(func,"reset"):
            func.reset = mknoop()
        return func

    def flush(self):
        # TODO: this should read-and-write the rest of the data in the file
        data = self._wfunc.flush()
        if data is not None:
            self._fileobj.write(data)
        super(Translate,self).flush()
        if not self._closing:
            if "-" not in self.mode:
                self.seek(self.tell())
            else:
                if hasattr(self._rfunc,"reset"):
                    self._rfunc.reset()
                if hasattr(self._wfunc,"reset"):
                    self._wfunc.reset()

    def _read(self,sizehint=-1):
        if self._read_eof:
            return None
        data = self._fileobj.read(sizehint)
        if data == "":
            self._read_eof = True
            tData = self._rfunc.flush()
            if tData is None:
                return tData
        else:
            tData = self._rfunc(data)
        self._pos += len(tData)
        return tData
    
    def _write(self,data,flushing=False):
        """Write the given data to the file."""
        self._pos += len(data)
        wData = self._wfunc(data)
        self._fileobj.write(wData)
 
    def _tell(self):
        return self._pos

    def _seek(self,offset,whence):
        #  For generic translation functions, we can't do much more than
        #  go back to the beginning.  See BytewiseTranslate for a much
        #  more efficient seek().
        if whence > 0 or offset > 0:
            raise NotImplementedError
        self._fileobj.seek(0,0)
        self._pos = 0
        self._read_eof = False
        if hasattr(self._rfunc,"reset"):
            self._rfunc.reset()
        if hasattr(self._wfunc,"reset"):
            self._wfunc.reset()

    def _truncate(self,size):
        #  For generic translation functions, we can only sensibly truncate
        #  to zero bytes.  See BytewiseTranslate for truncation to any size.
        if size != 0:
            msg = "Translate wrapper can only be truncated to zero size"
            raise IOError(msg)
        self._seek(0,0)
        self._fileobj.truncate(0)
        

 
class BytewiseTranslate(FileWrapper):
    """Class implementing a bytewise translation on a file's contents.
    
    This class wraps a file-like object in another file-like object,
    applying a given function to translate the file's contents as it is
    read or written.  It could be used, for example, to encrypt a file
    as it's being written.
    
    The translating function must accept a string as its only argument,
    and return a transformed string representing the updated file contents.
    Since this is a bytewise translation, the returned string must be of
    the same length.  The translation function may not buffer any data.
    
    If a single function is provided it is used for both reads and writes.
    To use separate functions, provide the keyword arguments 'wfunc' and
    'rfunc'.
    """

    def __init__(self,fileobj,func=None,mode=None,rfunc=None,wfunc=None):
        """BytewiseTranslate file wrapper constructor.

        'fileobj' must be the file-like object whose contents are to be
        transformed, and 'func' the callable that will transform the
        contents.  'mode' should be one of "r" or "w" to indicate whether
        reading or writing is desired.  If omitted it is determined from
        'fileobj' where possible, otherwise it defaults to "r".
        
        If separate reading/writing translations are required, the
        keyword arguments 'rfunc' and 'wfunc' can be used in place of
        'func'.
        """
        super(BytewiseTranslate,self).__init__(fileobj,mode)
        if func is not None:
            if rfunc is not None:
                raise ValueError("Cannot specify both <func> and <rfunc>")
            if wfunc is not None:
                raise ValueError("Cannot specify both <func> and <wfunc>")
            self._rfunc = func
            self._wfunc = func
        else:
            if self._check_mode("r-"):
                if rfunc is None:
                    raise ValueError("Must provide <rfunc> for readable files")
            if self._check_mode("w-"):
                if wfunc is None:
                    raise ValueError("Must provide <wfunc> for writable files")
            self._rfunc = rfunc
            self._wfunc = wfunc
            
    def _read(self,sizehint=-1):
        """Read approximately <sizehint> bytes from the file."""
        data = self._fileobj.read(sizehint)
        if data == "":
            return None
        return self._rfunc(data)
    
    def _write(self,data,flushing=False):
        """Write the given data to the file."""
        self._fileobj.write(self._wfunc(data))

    # Since this is a bytewise translation, the default implementations of
    # _seek(), _tell() and _truncate() will do what we want.

