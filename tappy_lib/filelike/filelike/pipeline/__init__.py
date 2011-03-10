# filelike/pipeline/__init__.py
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

    filelike.pipeline:  manipulate file-like objects in unix pipeline style
    
This module utilises python's operator overloading magic to allow file-like
wrappers such as those found in filelike.wrappers to be composed in the style
of a unix pipeline.

Ideas based on the following ASPN Cookbook Recipie:
    
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/276960

The base class PipelineEntry implements the operator magic, and a mirror
class is provided for each wrapper in filelike.wrappers. To allow additional
wrappers to be used, use pipeline() on the class:
    
    class MyNewWrapper(FileWrapper):
        ...
    
    MyNewWrapper = pipeline(MyNewWrapper)
    

As an example, here's how to print the first 20 lines of an encrypted file:
    
    for ln in file("enc_file.bin","r") > Decrypt(key) | Head(lines=20)
        print ln

Some folks would say this aids readability when using long combinations of
wrappers.  A lot would probably call it a horrible abuse of operator semantics.
Mostly I consider it a fun hack.

The following pipline operators are supported:
    
    >     Read or write from a wrapper into a file-like object
    >>    Write from a wrapper into a file-like object in append mode
    |     Read/write from one wrapper into another

Because of the way python's operator lookup works, > is used for both read
and write.  At the beginning of a pipeline, it indicates that data is to
be read from the file.  At the end, it indicates data should be written
to the file.

"""

import filelike

class PipelineEntry:
    """Class implementing a step in a file-like pipeline.
    
    Objects of this class may form a stage in a file-like pipeline.  Typically
    this will be either the first entry in the pipeline, or an entry following
    a readable file-like object.
    
    Each instance of this class must implement the method _create(fileobj),
    which creates and returns an appropriate wrapper around the given
    file-like object.
    """
    
    def __init__(self,cls,*args,**kwds):
        """PipelineEntry constructor.

        'cls' is the class of the file-like wrapper to create.  Additional
        args may be specified and will be passed in after the requisite
        'fileobj' first argument in the class's constructor.
        """
        self._cls = cls
        self._args = args
        self._kwds = kwds
    
    def _create(self,fileobj,mode=None):
        """Create instance of the FileWrapper over given file object."""
        if mode is not None and not self._kwds.has_key("mode"):
            kwds = self._kwds.copy()
            kwds["mode"] = mode
        else:
            kwds = self._kwds
        return self._cls(fileobj,*self._args,**kwds)
    
    def __lt__(self,obj):
        """Implement read-from-file pipeline stage.
        
        'obj' must not be a PipelineEntry, and must be coercable
        to a file-like object using filelike.to_filelike() with
        mode "r".
        
        A new file-like object will be returned that reads from the
        opened file-like object.
        """
        if isinstance(obj,PipelineEntry):
            raise ValueError("Cannot read from existing pipeline entry.")
        obj = filelike.to_filelike(obj,"r")
        return self._create(obj,"r")
    
    def __gt__(self,obj):
        """Implement write-to-file pipeline stage.
        
        'obj' must not be a PipelineEntry, and must be coercable
        to a file-like object using filelike.to_filelike() with
        mode "w".
        
        A new file-like wrapper will be returned that writes to
        the given object.
        """
        if isinstance(obj,PipelineEntry):
            raise ValueError("Cannot write to existing pipeline entry.")
        obj = filelike.to_filelike(obj,"w")
        return self._create(obj,"w")

    def __rshift__(self,obj):
        """Implement append-to-file pipeline stage.
        
        This behaves as __gt__, but opens the file in append mode.
        """
        if isinstance(obj,PipelineEntry):
            raise ValueError("Cannot write to existing pipeline entry.")
        obj = filelike.to_filelike(obj,"a")
        return self._create(obj,"a")

    def __or__(self,obj):
        """Implement left-hand pipe segment in pipeling stage.
        
        'obj' should be the next pipeline stage.  This starts a
        PipelineStack.
        """
        return PipelineStack(self,obj)

class PipelineStack:
    """Class collecting pipeline entries to be read/written to.
    
    This class collects a stack of pipeline entries. These will
    be converted to a filelike object in the appropriate order
    when the write/read-to-file pipeline stage is encountered.
    """
    
    def __init__(self,first,second):
        """PipelineStack constructor.

        'first' and 'second' must be the initial two stages in the
        pipeline.
        """
        self._stages = [second,first]
    
    def __or__(self,obj):
        """Implement left-hand pipe segment in pipeling stage.
        
        'obj' should be the next pipeline stage, which is added to the stack.
        """
        self._stages.append(obj)
        return self
    
    def __gt__(self,obj):
        """Implement write-to-file pipeline stage.
        
        'obj' must not be a PipelineEntry, and must be coercable
        to a file-like object using filelike.to_filelike() with
        mode "w".
        
        A new file-like wrapper will be returned that writes to
        the given object.
        """
        if isinstance(obj,PipelineEntry):
            raise ValueError("Cannot write to existing pipeline entry.")
        obj = filelike.to_filelike(obj,"w")
        while len(self._stages) > 0:
            next = self._stages.pop(0)
            obj = next._create(obj,"w")
        return obj

    def __lt__(self,obj):
        """Implement read-from-file pipeline stage.
        
        'obj' must not be a PipelineEntry, and must be coercable
        to a file-like object using filelike.to_filelike() with
        mode "w".
        
        A new file-like wrapper will be returned that writes to
        the given object.
        """
        if isinstance(obj,PipelineEntry):
            raise ValueError("Cannot read from existing pipeline entry.")
        obj = filelike.to_filelike(obj,"r")
        while len(self._stages) > 0:
            next = self._stages.pop()
            obj = next._create(obj,"r")
        return obj

    def __rshift__(self,obj):
        """Implement append-to-file pipeline stage.
        
        This behaves as __gt__, but opens the file in append mode.
        """
        if isinstance(obj,PipelineEntry):
            raise ValueError("Cannot write to existing pipeline entry.")
        obj = filelike.to_filelike(obj,"a")
        while len(self._stages) > 0:
            next = self._stages.pop(0)
            obj = next._create(obj,"a")
        return obj


def pipeline(cls):
    """Create a PipelineEntry factory function using given class."""
    def create_entry(*args,**kwds):
        return PipelineEntry(cls,*args,**kwds)
    return create_entry


##  Create a PipelineEntry factory for each wrapper
##  defined in filelike.wrappers
from filelike import wrappers
for nm in dir(wrappers):
    cls = getattr(wrappers,nm)
    try:
        if issubclass(cls,wrappers.FileWrapper):
            if cls is not wrappers.FileWrapper:
                globals()[nm] = pipeline(cls)
    except TypeError:
        pass

