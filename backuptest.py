"""
backuptest.py - test the backup / encrtyption
"""

from client import backup, encrypt, upload
from client.settingsmanager import settings
from client.logger import log

import uuid
import urllib
import os

# backup all .txt files from c:/program files/
log.info("Backup / encryption testing starting")

filespec = ".+\.txt$"
temppath = "c:/temp/"
dbpath = "./"
#drives = ("c:/code/fishtankclient/",)
drives = ("c:/",)
pk = settings[".publickey"]

# backup.
log.info("backing up...")
b = backup.Backup(filespec, 
				  temppath, 
				  dbpath,
				  drives)

b.execute()
if b.backupcount > 0:
	# encrypt
	# all stuff is backed up now. b has closed the files, but hasn't deleted them yet.
	fi = b.zipfilename
	fo = b.tempfile.name + ".enc"
	key = str(uuid.uuid4() )
	
	log.info("Encrypting %s" % fi)
	
	encrypt.EncryptAFile(filein=fi,fileout=fo,key=key)
	# file is encrypted, sitting at fileout.
	# encrypt the key and push to server?
	ekey = "".join(encrypt.EncryptAString(key, pk))

	rawfilename = os.path.basename(b.diffdbname)
	
	# now push all this to the server
	host = "172.16.223.128:8000"
	url = "/manager/dbmupload/"
	fields = [("eKey",urllib.quote(ekey)), ]
	files = [("dFile",rawfilename,open(b.diffdbname,"rb").read() )]
	
	log.info("Uploading")
	
	status, reason, data = upload.httppost_multipart(host, url, fields, files)
	log.debug("Status response = %s" % status)
	log.debug("reason %s" % reason)
	log.debug(data)

	os.remove(fo)

	# we need to encrypt the .zip file (b.zipfilename)
else:
	log.info("No files backed up, oh well")

log.info("Done")
raw_input("press any key")

del(b)