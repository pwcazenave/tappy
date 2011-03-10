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

    filelike.wrappers.crypto:  wrapper classes for cryptography
    
This module provides the filelike wrappers 'Encrypt' and 'Decrypt' for
dealing with encrypted files.

""" 

import filelike
from filelike.wrappers import FileWrapper
from filelike.wrappers.translate import Translate, BytewiseTranslate
from filelike.wrappers.buffer import FlushableBuffer
from filelike.wrappers.fixedblocksize import FixedBlockSize


class Decrypt(FileWrapper):
    """Class for reading and writing to an encrypted file.
    
    This class accesses an encrypted file using a ciphering object
    compliant with PEP272: "API for Block Encryption Algorithms".
    All reads from the file are automatically decrypted, while writes
    to the file and automatically encrypted.  Thus, Decrypt(fobj)
    can be seen as the decrypted version of the file-like object fobj.
    
    Because this class is implemented on top of FixedBlockSize, it
    assumes that the file size is a multiple of the block size.  If this
    is not appropriate, wrap it with UnPadToBlockSize.
    
    There is a dual class, Encrypt, where all reads are encrypted
    and all writes are decrypted.  This would be used, for example, to
    encrypt the contents of an existing file using a series of read()
    operations.
    """

    def __init__(self,fileobj,cipher,mode=None):
        """Decrypt Constructor.

        'fileobj' is the file object with encrypted contents, and 'cipher'
        is the cipher object to be used.  Other arguments are passed through
        to FileWrapper.__init__
        """
        if mode is None:
            try:
                mode = fileobj.mode
            except AttributeError:
                mode = "r+"
        self._cipher = cipher
        if cipher.mode == 1:
            # MODE_ECB is a bytewise translation
            myFileObj = BytewiseTranslate(fileobj,mode=mode,
                                                  rfunc=cipher.decrypt,
                                                  wfunc=cipher.encrypt)
            myFileObj = FixedBlockSize(myFileObj,cipher.block_size,mode=mode)
            if self._check_mode("w",mode) and "-" not in mode:
                if not self._check_mode("r",mode):
                    myFileObj = FlushableBuffer(myFileObj,mode=mode)
        else:
            # Other modes are stateful translations.
            # To reset them, we simply reset the initialisation vector
            initialIV = cipher.IV
            def rfunc(data):
                return cipher.decrypt(data)
            def wfunc(data):
                return cipher.encrypt(data)
            def reset():
                cipher.IV = initialIV
            rfunc.reset = reset
            wfunc.reset = reset
            myFileObj = Translate(fileobj,mode=mode,rfunc=rfunc,wfunc=wfunc)
            myFileObj = FixedBlockSize(myFileObj,cipher.block_size,mode=mode)
            #  To allow writes with seeks, we need to buffer.
            #  TODO: find a way around this.
            if self._check_mode("rw",mode):
                myFileObj = FlushableBuffer(myFileObj,mode=mode)
            elif self._check_mode("w",mode) and "-" not in mode:
                myFileObj = FlushableBuffer(myFileObj,mode=mode)
        super(Decrypt,self).__init__(myFileObj,mode=mode)


class Encrypt(FileWrapper):
    """Class for reading and writing to an decrypted file.
    
    This class accesses a decrypted file using a ciphering object
    compliant with PEP272: "API for Block Encryption Algorithms".
    All reads from the file are automatically encrypted, while writes
    to the file are automatically decrypted.  Thus, Encrypt(fobj)
    can be seen as the encrypted version of the file-like object fobj.

    Because this class is implemented on top of FixedBlockSize, it
    assumes that the file size is a multiple of the block size.  If this
    is not appropriate, wrap the underlying file object with PadToBlockSize.
    You will need to write the padding data yourself.
    
    There is a dual class, Decrypt, where all reads are decrypted
    and all writes are encrypted.  This would be used, for example, to
    decrypt the contents of an existing file using a series of read()
    operations.
    """

    def __init__(self,fileobj,cipher,mode=None):
        """Encrypt Constructor.

        'fileobj' is the file object with decrypted contents, and 'cipher'
        is the cipher object to be used.  Other arguments are passed through
        to FileWrapper.__init__
        """
        self._cipher = cipher
        if cipher.mode == 1:
            # MODE_ECB is a bytewise translation
            myFileObj = BytewiseTranslate(fileobj,mode=mode,
                                                  rfunc=cipher.encrypt,
                                                  wfunc=cipher.decrypt)
            myFileObj = FixedBlockSize(myFileObj,cipher.block_size,mode=mode)
            if self._check_mode("w",mode) and "-" not in mode:
                if not self._check_mode("r",mode):
                    myFileObj = FlushableBuffer(myFileObj,mode=mode)
        else:
            # Other modes are stateful translations.
            # To reset them, we simply reset the initialisation vector
            initialIV = cipher.IV
            def rfunc(data):
                return cipher.encrypt(data)
            def wfunc(data):
                return cipher.decrypt(data)
            def reset():
                cipher.IV = initialIV
            rfunc.reset = reset
            wfunc.reset = reset
            myFileObj = Translate(fileobj,mode=mode,rfunc=rfunc,wfunc=wfunc)
            myFileObj = FixedBlockSize(myFileObj,cipher.block_size,mode=mode)
            #  To allow writes with seeks, we need to buffer.
            #  TODO: find a way around this.
            if mode is None:
                try:
                    mode = fileobj.mode
                except AttributeError:
                    mode = "r+"
            if self._check_mode("rw",mode):
                myFileObj = FlushableBuffer(myFileObj,mode=mode)
            elif self._check_mode("w",mode) and "-" not in mode:
                myFileObj = FlushableBuffer(myFileObj,mode=mode)
        super(Encrypt,self).__init__(myFileObj,mode=mode)

