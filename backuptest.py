"""
backuptest.py - test the backup / encrtyption
"""

from client import backup, encrypt, upload
from client.settingsmanager import settings
from client.logger import log
from client.torrent import cloud

import uuid
import urllib
import os
	
# backup all .txt files from c:/program files/
log.info("Backup / encryption testing starting")

# settings for our environment
filespec = settings["filespec"] or ".+\.txt$"
temppath = settings["temppath"] or "c:/temp/" 
dbpath = settings["./db/"] or "./db/"
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
	
	#add the path to the cloud files
	pathout = settings["cloud_files"]
	if pathout == None:
		raise Exception("No cloud_files setting")

	fi = b.zipfilename
	fo = os.path.join(pathout,os.path.basename(b.tempfile.name + ".enc") )

	key = str(uuid.uuid4() )

	log.info("Encrypting %s to %s" % (fi, fo) )

	encrypt.EncryptAFile(filein=fi,fileout=fo,key=key)
	# file is encrypted, sitting at fileout.
	
	# delete our original file.
	# encrypt the key and push to server?
	ekey = "".join(encrypt.EncryptAString(key, pk))

	rawfilename = os.path.basename(b.diffdbname)

	# now push all this to the server
	host = settings[".managerhost"]
	url = "/manager/dbmupload/"
	fields = [("eKey",urllib.quote(ekey)),("guid", settings[".guid"]) ]
	files = [("dFile",rawfilename,open(b.diffdbname,"rb").read() )]
	
	log.info("Uploading %s" % b.diffdbname)
	
	status, reason, data = upload.httppost_multipart(host, url, fields, files)
	log.info("Status response = %s" % status)
	log.info("reason %s" % reason)
	log.info(data)

	# so the file is encrypted and uploaded, now put it in the cloud.
	if settings["tracker_ip"] == None:
		raise Exception("No tracker_ip in settings, sorry")
	
	c = cloud.Cloud(tracker_ip=settings["tracker_ip"],
				    torr_dir = settings["cloud_meta"],
				    data_dir = settings["cloud_files"],
				    )
	c.put(fo)
	del(b)

	raw_input("press any key to stop the cloud")

#	os.remove(fo)	

else:
	log.info("No files backed up, oh well")

log.info("Done")

