"""
Encrypt things

"""

from client import simplecrypt
from Crypto.PublicKey import RSA

import time

def EncryptAString(AString, PK):
    """
    Encrypts a string with the included public Key.  
        AString - String to Encrypt
        PK - Pycrypto PublicKey to encrypt with.
        sEncrypted = EncryptAString("This will be encrypted", myPK)
    """

    key = RSA.importKey(PK)
    return key.encrypt(AString, 101)


def EncryptAFile(filein = None, fileout=None, key=None, blocks=4096):
    """
    Encrypts a file with the key specified, using simplecrypt

    key - string to use as an encryption key
    filein - full pathname of file to encrypt
    fileout - full pathname of encrypted file.

    Encryptafile("filein.txt", "fileout.enc", "thisisakey")	
    """

#    s = simplecrypt.SimpleCrypt(key, BLOCK_SZ=(int(settings["block_sz"]) or 1024) )
    s = simplecrypt.SimpleCrypt(key, BLOCK_SZ=blocks)

    fi = open(filein,"rb")
    fo = open(fileout,"wb")

    # loop over the file and save to the encrypted version.
    for block in s.EncryptFile(fi):
        #time.sleep(.1)
        fo.write(block)

    fi.close()
    fo.close()