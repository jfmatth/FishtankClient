"""
backuptest.py - test the backup / encryption
"""

from client import backup, encrypt, upload
#from client.settingsmanager import settings
from client.logger import log
#from client.torrent import cloud
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
	
	log.debug("BackupFromCloud() Starting.")

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
			
	log.debug("BackupFromCloud() finished")


def BackupToCloud(cloud = None, settings = None, stopfunc=None):
	
	if cloud == None:
		log.exception("no cloud to backup to")
		raise Exception("No cloud to backup to :) ")
	
	if settings == None:
		log.exception("No settings passed in")
		raise Exception("No Settings to use :)")
	
	if not hasattr(stopfunc, '__call__'):
		log.exception("no stopfunc defined")
		raise Exception("no stopfunc defined")
	
	log.info("BackupToCloud() starting")
		
	insdir = settings['.installdir']

	filespec = settings["filespec"]
	if filespec == None:
		raise("Can't have a blank filespec")
	log.info("filespec = %s" % filespec)
	
	if settings["temppath"] == None:
		raise("No temppath specified")
	temppath = settings['temppath']
	
	log.info("temppath = %s" % temppath)
	
	if settings["dbpath"] == None:
		raise("no DB path specified")
	dbpath = os.path.normpath(insdir + settings['dbpath'])
	log.info("dbpath = %s" % dbpath)
	
	if not settings["backupdrives"]==None:
		drives = settings["backupdrives"].split(",")
	else:
		raise Exception("No backupdrives specified")
	log.info("drives = %s" % drives)
	
	backupsize = settings["backupsize"] or 1000
	backupsize = int(backupsize)
	
#	blocksize = settings["block_sz"]	# how big are the encryption blocks
	
	pk = settings[".publickey"]
	
	if settings["cloud_files"] == None:
		raise("no cloud_files specified")
	cloudpath = os.path.normpath(insdir + settings['cloud_files'])
	
	log.info("Starting backup loop")

	# define them here, since we need to check them at close
	_dbfull = None
	_dbdiff = None
	
	if stopfunc():
		log.debug("stopfunc returned true, returnning from module.")
		return
	
	#
	# we get backup 'sets' in sizes of limit in each loop
	# once we get a generated pair (zf=zipfile, dbf=database of files in zip), we encrypt and upload to tracker.
	#
	for zf, dbf in backup.BackupGenerator(filespec, temppath, dbpath, drives, limit=backupsize, stopbackup=stopfunc):

		if stopfunc():
			log.debug("Stopfunc() returned true")
			if os.path.exists(dbf):
				if not _dbdiff == None: _dbdiff = None
				log.debug("erasing %s" % dbf)
				os.remove(dbf)
	
			if os.path.exists(zf):
				log.debug("erasing %s" % zf)
				os.remove(zf)
			
			break
		
		# we should be able to modularize this better, but it is somewhat critical section, 
		# if any of the items below are interrupted, then the backup will be incomplete.

		log.debug("zf = %s\n dbf = %s" % (zf, dbf) )

		filein  = zf
		fileout = os.path.join(cloudpath,os.path.basename(zf) + "-e") 
	
		key = str(uuid.uuid4() )

		log.info("Encrypting %s"  % filein)
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

		# now upload the DBF for the tracker for keeping track of all files backed up.		
		log.info("Uploading %s" % dbf)
		status, reason, data = upload.httppost_multipart(host, url, fields, files)
		log.debug("status = %s" % status)
		log.debug("reason = %s" % reason)
		
		if status == 200:
			# so the file is encrypted and uploaded, now put it in the cloud.
			log.debug("Adding to cloud")
			cloud.put(fileout)
	
			# now, update the dbfull database to show that the files are updated.
			log.debug("Updating dbfull.db")
			if _dbfull == None:
				# only open if we need to.
				_dbfull = anydbm.open(os.path.join(dbpath, "dbfull.db"), "c") 
			_dbdiff = anydbm.open(dbf)
			for key in _dbdiff:
				# if it's not there, or the CRC's are different, update the DBfull db.
				if ( not _dbfull.has_key(key) ) or ( not json.loads(_dbfull[key])['crc'] == json.loads(_dbdiff[key])['crc'] ): 
					_dbfull[key] = _dbdiff[key]
			_dbdiff.close()
			log.debug("dbfull.db updated")
		else:
			log.critical("Failed to upload DB for backup, canceling backup")
		
		if os.path.exists(dbf):
			if not _dbdiff == None: _dbdiff = None
			log.debug("erasing %s" % dbf)
			os.remove(dbf)

		if os.path.exists(zf):
			log.debug("erasing %s" % zf)
			os.remove(zf)

	# close up...
	log.debug("cleaning up session..")
	if not _dbfull == None:
		log.debug("closing dbfull")
		_dbfull.close()
	if not _dbdiff == None:
		log.debug("closing & removing dbdiff(%s)" % dbf)
		_dbdiff.close()
		os.remove(dbf)
	log.debug("all cleaned up")

	log.info("BackupToCloud() finished")
