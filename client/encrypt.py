"""
Encrypts files

"""

from client import simplecrypt

class Encryptafile(object):
    """
    Encrypts a file with the key specified.
    """

    def __init__(self, filein, fileout, key=None):
        """
        key - string to use as an encryption key
        filein - full pathname of file to encrypt
        fileout - full pathname of encrypted file.
        """
        if key == None:
            raise Exception("Need a key to do this")

        self.key = key
        self.filein = filein
        self.fileout = fileout
        
    def execute(self):

        s = simplecrypt.SimpleCrypt(self.key)
        
        fi = open(self.filein,"rb")
        fo = open(self.fileout,"wb")
        
        # loop over the file and save to the encrypted version.
        for block in s.EncryptFile(fi):
            fo.write(block)

        fi.close()
        fo.close()
