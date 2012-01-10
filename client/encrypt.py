"""
Encrypts files

"""

from client import simplecrypt
from client.Crypto.PublicKey import RSA

from client.settingsmanager import settings

def EncryptAString(AString, PK):
    """
    Encrypts a string with the included public Key.  
	
	AString - String to Encrypt
	PK - Pycrypto PublicKey to encrypt with.
	
	sEncrypted = EncryptAString("This will be encrypted", myPK)
    """

    key = RSA.importKey(PK)
    return key.encrypt(AString, 101)


# class Encryptafile(object):
    # """
    # Encrypts a file with the key specified.
    
    # x = Encryptafile("filein.txt", "fileout.enc", "thisisakey")
    # x.execute()
    # """

    # def __init__(self, filein, fileout, key=None):
        # """
        # key - string to use as an encryption key
        # filein - full pathname of file to encrypt
        # fileout - full pathname of encrypted file.
        # """
        # if key == None:
            # raise Exception("Need a key to do this")

        # self.key = key
        # self.filein = filein
        # self.fileout = fileout
        
    # def execute(self):

        # s = simplecrypt.SimpleCrypt(self.key)
        
        # fi = open(self.filein,"rb")
        # fo = open(self.fileout,"wb")
        
        #loop over the file and save to the encrypted version.
        # for block in s.EncryptFile(fi):
            # fo.write(block)

        # fi.close()
        # fo.close()
def EncryptAFile(filein = None, fileout=None, key=None):
    """
    Encrypts a file with the key specified, using simplecrypt

    key - string to use as an encryption key
    filein - full pathname of file to encrypt
    fileout - full pathname of encrypted file.

    Encryptafile("filein.txt", "fileout.enc", "thisisakey")	
    """

    s = simplecrypt.SimpleCrypt(key, BLOCK_SZ=(int(settings["block_sz"]) or 1024) )
#    s = simplecrypt.SimpleCrypt(key)

    fi = open(filein,"rb")
    fo = open(fileout,"wb")

    # loop over the file and save to the encrypted version.
    for block in s.EncryptFile(fi):
        fo.write(block)

    fi.close()
    fo.close()