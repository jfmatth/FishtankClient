"""
backuptest.py - test the backup / encryption
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
import anydbm
import json

def BackupFromCloud(cloud = None, 
					settings = None):

	if cloud == None:
		raise Exception("No cloud to backup to :) ")
	
	if settings == None:
		raise Exception("No Settings to use :)")
	
	
	percFree = int(settings["max_free_perc"]) / 100.00
	maxGB = int(settings["min_free_gb"]) * 1024 * 1024 * 1024
	
	#calculate free space
	fs = utility.get_free_space("/")
	
	amount = min(int(fs*percFree), int(maxGB))
	
	# we will ask for a torrent of size < = amount then.
	
	managerhost = settings[".managerhost"]
	guid = settings[".guid"]
	HTTPConnection = httplib.HTTPConnection(managerhost)
	URL = "/manager/getcloud/?%s" % urllib.urlencode( {'size':amount,
													   'guid': guid 
													  }
													)

	HTTPConnection.request("GET", URL)
	response = HTTPConnection.getresponse()
	
	if response.status != 200:
		log.debug("error : URL: %s" % URL)
	else:
		infohash = response.read()
		if len(infohash) > 0:
			# get it from the cloud()
			print "asking for %s" % infohash
			cloud.get(infohash)
		else:
			print "Nothing to get"		



def BackupToCloud(cloud = None,
				  settings = None):
	
	if cloud == None:
		raise Exception("No cloud to backup to :) ")
	
	if settings == None:
		raise Exception("No Settings to use :)")
	
	log.info("BackupToCloud() starting")
		
	filespec = settings["filespec"]
	if filespec == None:
		raise("Can't have a blank filespec")
	log.info("filespec = %s" % filespec)
	
	temppath = settings["temppath"]
	if temppath == None:
		raise("No temppath specified")
	log.info("temppath = %s" % temppath)
	
	dbpath = settings["dbpath"]
	if dbpath == None:
		raise("no DB path specified")
	log.info("dbpath = %s" % dbpath)
	
	if not settings["backupdrives"]==None:
		drives = settings["backupdrives"].split(",")
	else:
		raise Exception("No backupdrives specified")
	log.info("drives = %s" % drives)
	
	backupsize = settings["backupsize"] or 1000
	backupsize = int(backupsize)
	
	pk = settings[".publickey"]
	
	cloudpath = settings["cloud_files"]
	if cloudpath == None:
		raise("no cloud_files specified")
	
	for zf, dbf in backup.BackupGenerator(filespec, temppath, dbpath, drives, limit=10):

		# we should be able to modularize this better, but it is somewhat critical section, 
		# if any of the items below are interrupted, then the backup will be incomplete.
		
		log.debug("zf = %s\n dbf = %s" % (zf, dbf) )
				
		filein  = zf
		fileout = os.path.join(cloudpath,os.path.basename(zf) + "-e") 
	
		key = str(uuid.uuid4() )

		log.info("Encrypting %s"  % filein)
		encrypt.EncryptAFile(filein=filein, fileout=fileout, key=key)
		# file is encrypted, sitting at fileout.
		
		# delete our original file.
		# encrypt the key and push to server?
		ekey = "".join(encrypt.EncryptAString(key, pk))

		rawfilename = os.path.basename(dbf)
		host = settings[".managerhost"]
		url = "/manager/dbmupload/"
		fields = [("eKey",urllib.quote(ekey)),
				  ("clientguid", settings[".guid"]),
				  ("backupguid", rawfilename.split(".")[0]),
				 ]
		files = [("dFile",rawfilename,open(dbf,"rb").read() )]
		
		log.info("Uploading %s" % dbf)
		
		status, reason, data = upload.httppost_multipart(host, url, fields, files)
	
		log.info("status = %s" % status)
		log.info("reason = %s" % reason)
		log.info("data = %s" % data)

		# so the file is encrypted and uploaded, now put it in the cloud.
		log.info("Adding to cloud")
		cloud.put(fileout)

		# now, update the dbfull database to show that the files are updated.
		log.debug("Updating dbfull.db")
		_dbfull = anydbm.open(os.path.join(dbpath, "dbfull.db"), "c") 
		_dbdiff = anydbm.open(dbf)
		for key in _dbdiff:
			# if it's not there, or the CRC's are different, update the DBfull db.
			if ( not _dbfull.has_key(key) ) or ( not json.loads(_dbfull[key])['crc'] == json.loads(_dbdiff[key])['crc'] ): 
				_dbfull[key] = _dbdiff[key]

		log.debug("Finishing backup...")

		# close up...		
		_dbfull.close()
		_dbdiff.close()
		os.remove(dbf)
		os.remove(zf)




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
	
	backupsize = settings["backupsize"] or 1000
	backupsize = int(backupsize)
	
	pk = settings[".publickey"]
	
	cloudpath = settings["cloud_files"]
	
	log.info("backing up...")

	for zf, dbf in backup.BackupGenerator(filespec, temppath, dbpath, drives, limit=10):

		# we should be able to modularize this better, but it is somewhat critical section, 
		# if any of the items below are interrupted, then the backup will be incomplete.
		
		log.debug("zf = %s\n dbf = %s" % (zf, dbf) )
				
		filein  = zf
		fileout = os.path.join(cloudpath,os.path.basename(zf) + "-e") 
	
		key = str(uuid.uuid4() )

		log.info("Encrypting %s"  % filein)
		encrypt.EncryptAFile(filein=filein, fileout=fileout, key=key)
		# file is encrypted, sitting at fileout.
		
		# delete our original file.
		# encrypt the key and push to server?
		ekey = "".join(encrypt.EncryptAString(key, pk))

		rawfilename = os.path.basename(dbf)
		host = settings[".managerhost"]
		url = "/manager/dbmupload/"
		fields = [("eKey",urllib.quote(ekey)),
				  ("clientguid", settings[".guid"]),
				  ("backupguid", rawfilename.split(".")[0]),
				 ]
		files = [("dFile",rawfilename,open(dbf,"rb").read() )]
		
		log.info("Uploading %s" % dbf)
		
		status, reason, data = upload.httppost_multipart(host, url, fields, files)
	
		log.info("status = %s" % status)
		log.info("reason = %s" % reason)
		log.info("data = %s" % data)
	
	
		# so the file is encrypted and uploaded, now put it in the cloud.
		log.info("Adding to cloud")
		c.put(fileout)

		# now, update the dbfull database to show that the files are updated.
		log.debug("Updating dbfull.db")
		_dbfull = anydbm.open(os.path.join(dbpath, "dbfull.db"), "c") 
		_dbdiff = anydbm.open(dbf)
		for key in _dbdiff:
			# if it's not there, or the CRC's are different, update the DBfull db.
			if ( not _dbfull.has_key(key) ) or ( not json.loads(_dbfull[key])['crc'] == json.loads(_dbdiff[key])['crc'] ): 
				_dbfull[key] = _dbdiff[key]

		log.debug("Finishing backup...")

		# close up...		
		_dbfull.close()
		_dbdiff.close()
		os.remove(dbf)
		os.remove(zf)


def testgetcloud():
		
	# get files from the cloud for here
	percFree = int(settings["max_free_perc"]) / 100.00
	maxGB = int(settings["min_free_gb"]) * 1024 * 1024 * 1024
	
	#calculate free space
	fs = utility.get_free_space("/")
	
	amount = min(int(fs*percFree), int(maxGB))
	
	# we will ask for a torrent of size < = amount then.
	
	managerhost = settings[".managerhost"]
	guid = settings[".guid"]
	HTTPConnection = httplib.HTTPConnection(managerhost)
	URL = "/manager/getcloud/?%s" % urllib.urlencode( {'size':amount,
													   'guid': guid 
													  }
													)

	HTTPConnection.request("GET", URL)
	response = HTTPConnection.getresponse()
	
	if response.status != 200:
		print "Error"
		log.debug("URL: %s" % URL)
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


	log.debug("Starting backuptest.py")
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
	log.debug("starting cloud")
	c.start()
	
	char = ""
	while not char == "x":
		print "Menu"
		print "b - Backup to the cloud"
		print "g - Backup from the cloud"
		print "s - Start the cloud"
		print "p - Stop the cloud"
		print "i - Is Serving?"
		print "e - Serving What?"
		print "d - Contents of database"
		print "x - Exit test"
		char = raw_input("press any key to stop the cloud: ")
	
		if char == "b":
			BackupToCloud(c, settings)
			#testbackup()
			
		elif char=="g":
			BackupFromCloud(c, settings)
			
		elif char=="s":
			c.start()
			
		elif char=="p":
			c.stop()
			
		elif char=="i":
			print "Is serving?: %s" % c.is_serving()
			
		elif char=="e":
			c.serving()
			
		elif char=="d":
			c.show_db()

	log.debug("deleting cloud")
	c.stop()
	del(c)
	
	log.debug("ending")