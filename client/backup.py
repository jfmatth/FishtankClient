"""
backup class
"""

from client import simplecrypt
import sys
import zlib
import os
import tempfile
import stat
import hashlib
import time
import json
import anydbm
import zipfile
import re


class Backup(object):
    
    def __init__(self, filespec, tpath, dbpath, key, drives):
        """
			filespec - Regex of which files to backup.
            tpath    - Temp path for working files.
            dbpath   - Path to where databases are stored.
            key      - Encryption key
            drives   - what drives to go through
		"""
        self.filespec = filespec    # file regular expression of what files to backup.
        self.workingpath = tpath    # where we should store our files.
        self.dbpath = dbpath        # location where we should keep our DB files.
        self.encryptkey = key       # Encryption key for simplecrypt, if None, then not encrypted
        self.drives = drives        # what drives to try, can be directories.

        self.backupfile = None      # result backup file (randomnunber.enc)
        self.backuplist = None      # DB of backed up files.
        self.tempfilename = None
        
        # generate some random file names for use.
        self.tempfile = tempfile.TemporaryFile(dir=self.workingpath)
        self.backupfile = self.tempfile.name + ".zip"
        self.backupfull = os.path.join(self.dbpath, "dbfull.db")
        self.backupdiff = self.tempfile.name + ".db"
        
        self.zipfile = zipfile.ZipFile(self.backupfile, "w", compression=zipfile.ZIP_DEFLATED)
        self.regex = re.compile(self.filespec)
        
        # open our DB's
        self.dbfull = anydbm.open(self.backupfull, "c")
        self.dbdiff = anydbm.open(self.backupdiff, "n")
		
    def __del__(self):
        print "Cleaning up..."

        print "removing dbfull object"
        del(self.dbfull)
        print "removing dbdiff object, and deleting file %s" % self.backupdiff
        del(self.dbdiff)
        os.remove(self.backupdiff)
        print "Removing object and deleting file %s" % self.backupfile
        self.zipfile.close()
        del(self.zipfile)
        os.remove(self.backupfile)

    def fileinfo(self, filename):
        """ returns a dict of all the file information we want of a file """
        fi = {}
        fs = os.stat(filename)
    
        fi['crc'] = self.crcval(filename)
        fi['filename'] = filename
        fi['size'] = fs[stat.ST_SIZE]
        fi['modified'] = time.strftime("%m/%d/%Y %I:%M:%S %p",time.localtime(fs[stat.ST_MTIME]))
        fi['accessed'] = time.strftime("%m/%d/%Y %I:%M:%S %p",time.localtime(fs[stat.ST_ATIME]))
        fi['created']  = time.strftime("%m/%d/%Y %I:%M:%S %p",time.localtime(fs[stat.ST_CTIME]))
        
        return fi

    def crcval(self, fileName):
        prev = 0
        for eachLine in open(fileName,"rb"):
            prev = zlib.crc32(eachLine, prev)
        return "%X"%(prev & 0xFFFFFFFF)
 
    def execute(self):

        dbfull = self.dbfull
        dbdiff = self.dbdiff	
        zip = self.zipfile
        regex = self.regex
		
        # loop over all drives and the files below that.function
        for dir in self.drives:
            print "backing up %s" % dir
            for root, dirs, files in os.walk(dir):
                for file in files:
                    fullpath = os.path.join(root,file)
                    try:
                        if os.path.isfile(fullpath) and regex.match(fullpath):
                            finfo = self.fileinfo(fullpath)  # a dict object
                            
                            # figure out what we need to do with it.
                            if not dbfull.has_key(fullpath):
                                print "Adding %s" % fullpath,
                                sfinfo = json.dumps(finfo)
                                dbfull[fullpath] = sfinfo
                                dbdiff[fullpath] = sfinfo
                                zip.write(fullpath)
                                print "..Done!"
                            else:
                                print "Checking %s" % fullpath,
                                if not json.loads(dbfull[fullpath])['crc'] == finfo['crc']:
                                    print "..updating",
                                    sfinfo = json.dumps(finfo)
                                    dbfull[fullpath] = sfinfo
                                    dbdiff[fullpath] = sfinfo
                                    zip.write(fullpath)
                                    
                                print "..Done!"
                    except Exception as e:
                        print "%s Exception on %s" % (e, fullpath)
                            
        # at the end of the backup.

    def upload(self):
        """  upload current backup to tracker
        """
        print "Upload to tracker"
		