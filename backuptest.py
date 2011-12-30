"""
backuptest.py - test the backup / encrtyption
"""

from client import backup, encrypt
from client.settingsmanager import settings
from client.logger import log

import uuid

# backup all .txt files from c:/program files/
log.info("Backup / encryption testing starting")

filespec = ".+\.txt$"
temppath = "c:/temp/"
dbpath = "./"
drives = ("c:/program files/",)
pk = settings[".publickey"]

# backup.
b = backup.Backup(filespec, 
				  temppath, 
				  dbpath,
				  drives)

b.execute()

# encrypt
# all stuff is backed up now. b has closed the files, but hasn't deleted them yet.
fi = b.zipfilename
fo = b.tempfile.name + ".enc"
key = str(uuid.uuid4() )

encrypt.EncryptAFile(filein=fi,fileout=fo,key=key)
# file is encrypted, sitting at fileout.
# encrypt the key and push to server?
ekey = "".join(encrypt.EncryptAString(key, pk))
log.info("Encrypted key is %s" % ekey)



# we need to encrypt the .zip file (b.zipfilename)

del(b)