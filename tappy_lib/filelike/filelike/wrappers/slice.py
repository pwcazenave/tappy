# filelike/wrappers/slice.py
#
# Copyright (C) 2006-2008, Ryan Kelly
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

    filelike.wrappers.slice:  read/write to a slice of a file
    
This module provides the filelike wrapper 'Slice' which exposes only a
portion of a file for reading and writing.

""" 

import filelike
from filelike.wrappers import FileWrapper


class Slice(FileWrapper):
    """Class for reading/writing only a portion of a file.
    
    This file wrapper can be used to read or write to a specified
    portion of a file-like object.  The constructor argument 'start'
    indicates the offset from the beginning of the file at which
    the slice should start, and the argument 'stop' indicates the
    offset at which it should end.  For example:

        s = Slice(f,20)       # read from byte 20 onwards in f
        s = Slice(f,10,20)    # read from byte 10 up to byte 20 of f

    If 'stop' is given and the file is writable, the default behavior is
    for writes beyond the stop position to raise on IOError.  To permit
    the slice to resize itself over any existing data in the underlying
    file, specify the 'resizable' keyword argument to the constructor.

    If 'stop' is negative then it is taken as on offset from the end of the
    file, just like standard list/tuple slicing.

    """
    
    def __init__(self,fileobj,start=0,stop=None,mode=None,resizable=False):
        """Slice constuctor.

        'start' and 'stop' are the indicies at which to start and stop the
        slice, and 'resizable' indicates whether the slice is allowed to grow
        in response to writes beyond the 'stop' index.
        """
        if start < 0:
            raise ValueError("start index cannot be negative.")
        if stop is not None and stop < 0:
            try:
                stop = fileobj.size + stop
            except AttributeError:
                pos = fileobj.tell()
                fileobj.seek(0,2)
                stop = fileobj.tell() + stop
                fileobj.seek(pos,0)
        self.start = start
        self.stop = stop
        self._resizable = resizable
        super(Slice,self).__init__(fileobj,mode)
        if "a" not in self.mode:
            if self._fileobj.tell() < start:
                self._fileobj.seek(start)
    
    def _read(self,size=-1):
        """Read approximately <size> bytes from the file."""
        pos = self._fileobj.tell()
        if self.stop is not None:
            if size < 0:
                size = self.stop - pos
            elif pos + size > self.stop:
                size = self.stop - pos
        if size == 0:
            return None
        data = self._fileobj.read(size)
        if data == "":
            return None
        return data

    def _write(self,data,flushing=False):
        """Write the given string to the file."""
        if self.stop is None:
            self._fileobj.write(data)
        else:
            pos = self._fileobj.tell()
            end = pos + len(data)
            if end > self.stop:
                if self._resizable:
                    self.stop = end
                    self._fileobj.write(data)
                else:
                    self._fileobj.write(data[:(self.stop - pos)])
                    raise IOError("File not resizable")
            else:
                self._fileobj.write(data)

    def _seek(self,offset,whence):
        """Seek within the file."""
        if whence == 0:
            offset = offset + self.start
            if offset < self.start:
                offset = self.start
            if self.stop is not None:
                if offset > self.stop:
                    if self._resizable:
                        self.stop = offset
                    else:
                        offset = self.stop
            self._fileobj.seek(offset,0)
        elif whence == 1:
            pos = self._fileobj.tell()
            if pos + offset < self.start:
                offset = self.start - pos
            if self.stop is not None:
                if pos + offset > self.stop:
                    offset = self.stop - pos
            self._fileobj.seek(offset,1)
        elif whence == 2:
            if self.stop is None:
                self._fileobj.seek(offset,2)
                if offset < 0:
                    pos = self._fileobj.tell()
                    if pos < self.start:
                        self._fileobj.seek(self.start,0)
            else:
                if offset > 0 and not self._resizable:
                    offset = self.stop - self.start
                else:
                    offset = self.stop + offset - self.start
                self._seek(offset,0)
        else:
            raise ValueError("Invalid value for whence: " + str(whence))

    def _tell(self):
        """Get position of file pointer."""
        return self._fileobj.tell() - self.start

    def _truncate(self,size):
        msg = "File slices are not truncatable"
        raise filelike.NotTruncatableError(msg)
 
