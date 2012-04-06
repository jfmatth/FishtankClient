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

def BackupFromCloud( cloud = None, settings = None):

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
			log.info("Asing for hash %s" % infohash)
			cloud.get(infohash)


def BackupToCloud(cloud = None, settings = None, fast=False):
	
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
	
	blocksize = settings["block_sz"]	# how big are the encryption blocks
	
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
#		encrypt.EncryptAFile(filein=filein, fileout=fileout, key=key, block_sz=blocksize, fast=fast)
		encrypt.EncryptAFile(filein=filein, fileout=fileout, key=key)
		# file is encrypted, sitting at fileout.
		
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
	
		log.debug("status = %s" % status)
		log.debug("reason = %s" % reason)
		log.debug("data = %s" % data)

		# so the file is encrypted and uploaded, now put it in the cloud.
		log.debug("Adding to cloud")
		cloud.put(fileout)

		# now, update the dbfull database to show that the files are updated.
		log.debug("Updating dbfull.db")
		_dbfull = anydbm.open(os.path.join(dbpath, "dbfull.db"), "c") 
		_dbdiff = anydbm.open(dbf)
		for key in _dbdiff:
			# if it's not there, or the CRC's are different, update the DBfull db.
			if ( not _dbfull.has_key(key) ) or ( not json.loads(_dbfull[key])['crc'] == json.loads(_dbdiff[key])['crc'] ): 
				_dbfull[key] = _dbdiff[key]

		# close up...		
		_dbfull.close()
		_dbdiff.close()
		os.remove(dbf)
		os.remove(zf)
