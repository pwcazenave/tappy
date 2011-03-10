# filelike/wrappers/debug.py
#
# Copyright (C) 2009, Ryan Kelly
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

    filelike.wrappers.debug:  debug accesses to a file

For the moment, just prints to stdout.
    
""" 

import filelike
from filelike.wrappers import FileWrapper

from StringIO import StringIO


class Debug(FileWrapper):
    """Class for debugging activity on a file.
    
    Currently it just logs activity to stdout, it will probably do
    more sophisticated things in the future.
    """

    def _debug(self,action,*args):
        args = [repr(a) for a in args]
        print "<%s : %s>  %s" % (self.label,action," | ".join(args))
    
    def __init__(self,fileobj,label="",mode=None):
        self.label = label
        self._debug("INIT",fileobj,mode)
        super(Debug,self).__init__(fileobj,mode)
    
    def _read(self,size=-1):
        self._debug("READING",size)
        data = self._fileobj.read(size)
        self._debug("READ",data)
        if data == "":
            return None
        return data
        
    def _write(self,data,flushing=False):
        self._debug("WRITING",data,flushing)
        self._fileobj.write(data)
        self._debug("WROTE")

    def _seek(self,offset,whence):
        self._debug("SEEKING",offset,whence)
        self._fileobj.seek(offset,whence)
        self._debug("SEEKED")

    def _tell(self):
        self._debug("TELLING")
        pos = self._fileobj.tell()
        self._debug("TELLED",pos)
        return pos

    def _truncate(self,size):
        self._debug("TRUNCATING",size)
        self._fileobj.truncate(size)
        self._debug("TRUNCATED")
        return pos

    def flush(self):
        self._debug("FLUSHING")
        self._fileobj.flush()
        self._debug("FLUSHED")

    def close(self):
        self._debug("CLOSING")
        self._fileobj.flush()
        self._debug("CLOSED")
 

