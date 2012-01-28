"""
backuptest.py - test the backup / encrtyption
"""

from client import backup, encrypt, upload
from client.settingsmanager import settings
from client.logger import log
from client.torrent import cloud
from client import utility

import uuid
import urllib
import httplib
import os

c = []

def testbackup():

	# backup all .txt files from c:/program files/
	log.info("Backup / encryption testing starting")
		
	# settings for our environment
	log.info("getting settings for backup")
	
	filespec = settings["filespec"] or ".+\.txt$"
	log.info("filespec = %s" % filespec)
	
	temppath = settings["temppath"] or "c:/temp/"
	log.info("temppath = %s" % temppath)
	
	dbpath = settings["dbpath"] or "./db/"
	log.info("dbpath = %s" % dbpath)
	
	if not settings["backupdrives"]==None:
		drives = settings["backupdrives"].split(",")
	else:
		drives = ("c:/",)
	log.info("drives = %s" % drives)
	
	pk = settings[".publickey"]
	log.info("public key = %s" % pk)
	
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
			log.critical("no tracker_ip in settings - FAIL")
			raise Exception("No tracker_ip in settings, sorry")

		log.info("Adding to cloud")
		c.put(fo)
	
		del(b)

	else:
		log.info("No files backed up, oh well")


def testgetcloud():
		
	# get files from the cloud for here
	percFree = int(settings["max_free_perc"]) / 100.00
	maxGB = int(settings["min_free_gb"]) * 1024 * 1024 * 1024
	
	#calculate free space
	fs = utility.get_free_space("/")
	
	amount = min(fs*percFree, maxGB)
	
	# we will ask for a torrent of size < = amount then.
	
	HTTPConnection = httplib.HTTPConnection(settings[".managerhost"])
	URL = "/manager/getcloud/?%s" % urllib.urlencode( {'size':amount,
													   'guid': settings[".guid"] 
													  }
													)

	HTTPConnection.request("GET", URL)
	response = HTTPConnection.getresponse()
	
	if response.status != 200:
		print "Error"
	else:
		ih = response.read()
		if len(ih) > 0:
			# get it from the cloud()
			print "asking for %s" % ih
			c.get(ih)
		else:
			print "Nothing to get"		

if __name__ == "__main__":
	# make sure we have the necessary settings

	# validate all necessary settings first
	if settings["block_sz"] == None:
		raise Exception("setting block_sz missing")
	if settings["filespec"] == None:
		raise Exception("setting filespec missing")
	if settings["temppath"] == None:
		raise Exception("setting temppath missing")
	if settings["dbpath"] == None:
		raise Exception("setting dbpath missing")
	if settings[".publickey"] == None:
		raise Exception("setting .publickey missing")
	if settings["cloud_files"] == None:
		raise Exception("setting cloud_files missing")
	if settings["cloud_meta"] == None:
		raise Exception("setting cloud_meta missing")
	if settings["tracker_ip"] == None:
		raise Exception("setting tracker_ip missing")
	if settings["max_free_perc"] == None:
		raise Exception("max_free_perc missing")
	if settings["min_free_gb"] == None:
		raise Exception("min_free_gb missing")
	
	# start up the cloud
	print "Starting the cloud"
	c = cloud.Cloud(tracker_ip=settings["tracker_ip"],
					torr_dir = settings["cloud_meta"],
				    data_dir = settings["cloud_files"],
				    session_dir = settings["cloud_meta"]
				    )
	c.start()
	
	char = ""
	while not char == "x":
		print "Menu"
		print "b - Backup to the cloud"
		print "g - Backup from the cloud"
		print "x - Exit test"
		char = raw_input("press any key to stop the cloud")
	
		if char == "b":
			testbackup()
		elif char=="g":
			testgetcloud()

#	c.stop() - No workie yet!
	
