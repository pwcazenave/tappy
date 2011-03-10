# filelike/wrappers/padtoblocksize.py
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

    filelike.wrappers.padtoblocksize:  pad a file to a given blocksize
    
This module provides the dual filelike wrappers 'PadToBlockSize' and 
'UnPadToBlockSize' to handle padding of a file to a specified blocksize.

""" 

import filelike
from filelike.wrappers import FileWrapper


class PadToBlockSize(FileWrapper):
    """Class padding files to a fixed block size.
    
    This file wrapper can be used to pad a file to a specific block size.
    The file data is followed by a 'Z', then as many 'X' bytes as needed
    to meet the block size.  This is automatically added when reading,
    and stripped when writing.  The dual of this class is UnPadToBlockSize.

    This class does not necessarily align reads or writes along block
    boundaries - use the FixedBlockSize wrapper to achieve this.
    """

    def __init__(self,fileobj,blocksize,mode=None):
        self.blocksize = blocksize
        self._pad_read = ""
        self._pad_unread = ""
        super(PadToBlockSize,self).__init__(fileobj,mode)
        if "a" in self.mode:
            # Position at the start of the padding, since that's
            # where any additional writes need to happen
            self._pad_unread = self._pad_read
            self._pad_read = ""
            self._sbuffer = None
    
    def _round_up(self,num):
        """Round <num> up to a multiple of the block size."""
        if num % self.blocksize == 0:
            return num
        return ((num/self.blocksize)+1) * self.blocksize
    
    def _round_down(self,num):
        """Round <num> down to a multiple of the block size."""
        if num % self.blocksize == 0:
            return num
        return (num/self.blocksize) * self.blocksize
    
    def _padding(self,data):
        """Get the padding needed to make 'data' match the blocksize."""
        padding = "Z"
        size = self._round_up(len(data)+1)
        padding = padding + ("X"*(size-len(data)-1))
        return padding

    def _read(self,sizehint=-1):
        # If there is unread padding, return that
        if self._pad_unread:
            data = self._pad_unread
            self._pad_read = self._pad_read + data
            self._pad_unread = ""
            return data
        # If the padding has been read, return EOF
        if self._pad_read:
            return None
        # Always read at the blocksize, as it makes padding easier
        if sizehint > 0:
            sizehint = self._round_up(sizehint)
        data = self._fileobj.read(sizehint)
        if sizehint < 0 or len(data) < sizehint:
            self._pad_unread = self._padding(data)
        return data

    def _write(self,string,flushing=False):
        # Check whether this could contain the padding block, which
        # will need to be removed.
        zIdx = string.rfind("Z")
        maybePad = zIdx >= len(string) - self.blocksize - 1
        for c in string[zIdx+1:]:
            if c != "X":
                maybePad = False
                break
        # If it may contain the padding block, don't write those blocks
        # just yet.  Otherwise, write as much as possible.
        if maybePad:
            size = self._round_down(zIdx)
        else:
            size = self._round_down(len(string))
        self._fileobj.write(string[:size])
        leftover = string[size:]
        # If there's no leftover, well, that was easy :-)
        if not leftover:
            return None
        # If we're not flushing, we can delay writing the leftovers.
        if not flushing:
            return leftover
        # If we are flushing, we need to write the leftovers.
        # If we're in the middle of the file, write out a complete block
        # using the existing file contents.  Only works if readable...
        if self._check_mode("r"):
            lenNB = self._round_up(len(leftover))
            nextBlock = self._fileobj.read(lenNB)
            self._fileobj.seek(-1*len(nextBlock),1)
            if lenNB == len(nextBlock):
                padstart = len(leftover)
                self._fileobj.write(leftover + nextBlock[padstart:])
                self.seek(padstart - lenNB,1)
                return None
        # Otherwise, we must be at the end of the file.
        # Remove the padding data from the leftovers
        if maybePad:
            zIdx = leftover.rfind("Z")
            data = leftover[:zIdx]
            padding = self._padding(data)
            padstop = len(leftover) - zIdx
            self._fileobj.write(data)
            self._pad_read = padding[:padstop]
            self._pad_unread = padding[padstop:]
        return None

    def _seek(self,offset,whence):
        """Seek to approximately 'offset' bytes from start of file.

        This method implements absolute seeks and will not seek to
        positions beyond the end of the file.  If you try to seek past
        the file and its padding, you'll be placed at EOF.
        """
        if whence > 0:
            # TODO: implementing these shouldn't be that hard...
            raise NotImplementedError
        self._fileobj.seek(0,0)
        self._pad_unread = ""
        self._pad_read = ""
        if offset == 0:
            return None
        # Slow simulation of seek by actually re-reading all the data.
        boundary = self._round_down(offset)
        bytes_read = 0
        while bytes_read < boundary:
            data = self._fileobj.read(min(self._bufsize,boundary-bytes_read))
            if data == "":
                break
            bytes_read += len(data)
        # If the boundary is not within the file, we must have seeked right
        # to (or past) the end of the padding.  So just position at end.
        if bytes_read < boundary:
            data = ""
            self._pad_read = self._padding("A"*(bytes_read % self.blocksize))
            return None
        # Otherwise, we may have to return some data from the underlying file
        pos = self._fileobj.tell()
        data = self._fileobj.read(offset-boundary)
        self._fileobj.seek(-1*len(data),1)
        assert self._fileobj.tell() == pos, "peeking failed"
        diff = offset - (len(data) + bytes_read)
        assert diff >= 0, "peeking failed"
        if diff > 0:
            # The target offset is somewhere in the padding
            padding = self._padding(data)
            return data + padding[:diff]
        return data

    def _tell(self):
        return self._fileobj.tell() + len(self._pad_read)

    def _truncate(self,size):
        if size % self.blocksize != 0:
            msg = "PadToBlockSize must be truncated to a multiple of " \
                  "the blocksize"
            raise IOError(msg)
        pos = self._fileobj.tell()
        if size <= pos:
            self._pad_read = self._pad_unread = None
        else:
            self._fileobj.seek(0,2)
            fsize = self._fileobj.tell()
            self._fileobj.seek(pos,0)
            if size > fsize:
                msg = "PadToBlockSize can't truncate past end of file"
                raise IOError(msg)
        self._fileobj.truncate(size)


class UnPadToBlockSize(FileWrapper):
    """Class removing block-size padding from a file.
    
    This file wrapper can be used to reverse the effects of PadToBlockSize,
    removing extraneous padding data when reading, and adding it back in
    when writing.
    """

    _append_requires_overwrite = True
    
    def __init__(self,fileobj,blocksize,mode=None):
        self.blocksize = blocksize
        self._pad_seen = ""
        super(UnPadToBlockSize,self).__init__(fileobj,mode)

    def _round_up(self,num):
        """Round <num> up to a multiple of the block size."""
        if num % self.blocksize == 0:
            return num
        return ((num/self.blocksize)+1) * self.blocksize
    
    def _round_down(self,num):
        """Round <num> down to a multiple of the block size."""
        if num % self.blocksize == 0:
            return num
        return (num/self.blocksize) * self.blocksize
    
    def _padding(self,data):
        """Get the padding needed to make 'data' match the blocksize."""
        padding = "Z"
        size = self._round_up(len(data)+1)
        padding = padding + ("X"*(size-len(data)-1))
        return padding
    
    def _read(self,sizehint=-1):
        """Read approximately <sizehint> bytes from the file."""
        if sizehint >= 0:
            sizehint = self._round_up(sizehint)
        data = self._fileobj.read(sizehint)
        # If we might be near the end, read far enough ahead to find the pad
        zIdx = data.rfind("Z")
        if sizehint >= 0:
            if data == "X"*self.blocksize:
                newData = self._fileobj.read(self.blocksize)
                sizehint += self.blocksize
                data = data + newData
            if zIdx >= 0:
                while zIdx >= (len(data) - self.blocksize - 1):
                    newData = self._fileobj.read(self.blocksize)
                    sizehint += self.blocksize
                    data = data + newData
                    zIdx = data.rfind("Z")
                    if newData == "":
                        break
        # Return the data, stripping the pad if we're at the end
        if data == "":
            return None
        if sizehint < 0 or len(data) < sizehint:
            if zIdx < 0:
                assert len(data) <= self.blocksize
                return None
            else:
                self._pad_seen = data[zIdx:]
                return data[:zIdx]
        else:
            return data

    def _write(self,data,flushing=False):
        """Write the given string to the file."""
        #  To ensure the pad is written, we always return non-empty leftovers.
        #  This forces a flushing write on file close.
        if data == "":
            return ""
        size = self._round_down(len(data)-1)
        self._fileobj.write(data[:size])
        leftover = data[size:]
        if not flushing:
            return leftover
        # Flushing, so we need to pad the data.  If the file is readable,
        # check to see if we're in the middle and pad using existing data.
        if self._check_mode("r"):
            lenNB = self._round_up(len(leftover)+1)
            nextBlock = self._fileobj.read(lenNB)
            self._fileobj.seek(-1*len(nextBlock),1)
            if lenNB == len(nextBlock):
                padstart = len(leftover)
                self._fileobj.write(leftover + nextBlock[padstart:])
                self.seek(padstart - lenNB,1)
                return None
        # Otherwise, we must be at the end of the file.
        padding = self._padding(leftover)
        self._fileobj.write(leftover + padding)
        self._pad_seen = padding
        return None

    def _seek(self,offset,whence):
        if whence > 0:
            raise NotImplementedError
        self._fileobj.seek(0,0)
        self._pad_seen = ""
        if offset == 0:
            return None
        data = self._fileobj.read(offset)
        eof = data.rfind("Z")
        if len(data) < offset:
            offset = eof
        elif eof != -1 and eof > len(data) - self.blocksize - 1:
            extra = self._fileobj.read(self.blocksize+1)
            data = data + extra
            if len(extra) <= self.blocksize:
                eof = data.rfind("Z")
                if eof < offset:
                    offset = eof
        boundary = self._round_down(offset)
        self._fileobj.seek(boundary-len(data),1)
        return data[boundary:offset]

    def _tell(self):
        return self._fileobj.tell() - len(self._pad_seen)

    def _truncate(self,size):
        msg = "UnPadToBlockSize objects are not truncatable"
        raise filelike.NotTruncatableError(msg)

