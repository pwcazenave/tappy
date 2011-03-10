
import unittest
from StringIO import StringIO

from filelike.pipeline import *

class Test_Pipeline(unittest.TestCase):
    """Testcases for the construction of pipelines."""
    
    def setUp(self):
        from Crypto.Cipher import DES
        self.cipher = DES.new('abcdefgh',DES.MODE_ECB)
        self.plaintext = "Guido van Rossum is a space alien." + "\0"*6
        self.ciphertext = "\x11,\xe3Nq\x8cDY\xdfT\xe2pA\xfa\xad\xc9s\x88\xf3,\xc0j\xd8\xa8\xca\xe7\xe2I\xd15w\x1d\xfe\x92\xd7\xca\xc9\xb5r\xec"
        self.plainfile = StringIO(self.plaintext)
        self.cryptfile = StringIO(self.ciphertext)
        self.outfile = StringIO()

    def tearDown(self):
        pass

    def test_ReaderLine(self):
        """Test a simple reading pipeline."""
        pf = self.ciphertext > Decrypt(self.cipher) | Head(bytes=10)
        txt = pf.read()
        self.assertEquals(txt,self.plaintext[:10])

    def test_WriterLine(self):
        """Test a simple writer pipeline."""
        pf = Decrypt(self.cipher) | Head(bytes=15) | FixedBlockSize(10) > self.outfile
        pf.write(self.plaintext)
        pf.flush()
        txt = self.outfile.getvalue()
        self.assertEquals(txt,self.ciphertext[:15])

