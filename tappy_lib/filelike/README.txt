

    filelike: a python module for creating and handling file-like objects.

This module takes care of the groundwork for implementing and manipulating
objects that provide a rich file-like interface, including reading, writing,
seeking and iteration.  It also provides a number of useful classes built on
top of this functionality.

The main class is FileLikeBase, which implements the entire file-like interface
on top of primitive _read(), _write(), _seek(), _tell() and _truncate() methods.
Subclasses may implement any or all of these methods to obtain the related
higher-level file behaviors.

It also provides some nifty file-handling functions:

    :open:    mirrors the standard open() function but is much cleverer;
              URLs are automatically fetched, .bz2 files are transparently
              decompressed, and so-on.

    :join:    concatenate multiple file-like objects together so that they
              act like a single file.

    :slice:   access a section of a file-like object as if it were an
              independent file.


The "wrappers" subpackage contains a collection of useful classes built on
top of this framework.  These include:
    
    :Translate:  pass file contents through an arbitrary translation
                 function (e.g. compression, encryption, ...)
                  
    :Decrypt:    on-the-fly reading and writing to an encrypted file
                 (using PEP272 cipher API)

    :UnBZip2:    on-the-fly decompression of bzip'd files
                 (like the standard library's bz2 module, but accepts
                 any file-like object)

As an example of the type of thing this module is designed to achieve, here's
how the Decrypt wrapper can be used to transparently access an encrypted
file::
    
    # Create the decryption key
    from Crypto.Cipher import DES
    cipher = DES.new('abcdefgh',DES.MODE_ECB)
    # Open the encrypted file
    from filelike.wrappers import Decrypt
    f = Decrypt(file("some_encrypted_file.bin","r"),cipher)
    
The object in 'f' now behaves as a file-like object, transparently decrypting
the file on-the-fly as it is read.


The "pipeline" subpackage contains facilities for composing these wrappers
in the form of a unix pipeline.  In the following example, 'f' will read the
first five lines of an encrypted file::
    
    from filelike.pipeline import Decrypt, Head
    f = file("some_encrypted_file.bin") > Decrypt(cipher) | Head(lines=5)


Finally, two utility functions are provided for when code expects to deal with
file-like objects:
    
    :is_filelike(obj):   checks that an object is file-like
    :to_filelike(obj):   wraps a variety of objects in a file-like interface

