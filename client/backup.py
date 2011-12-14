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
    
    def __init__(self, filespec, tpath, dbpath, key ):
        
        self.filespec = filespec    # file regular expression of what files to backup.
        self.workingpath = tpath    # where we should store our files.
        self.dbpath = dbpath        # location where we should keep our DB files.
        self.encryptkey = key       # Encryption key for simplecrypt, if None, then not encrypted

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
        self.dbfull = anydbm.open(self.backupfull, "w")
        self.dbdiff = anydbm.open(self.backupdiff, "c")
        
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

    def crcval(self, fileName):
        prev = 0
        for eachLine in open(fileName,"rb"):
            prev = zlib.crc32(eachLine, prev)
        return "%X"%(prev & 0xFFFFFFFF)
 

    def backup(self):
        # main backup function
    
        
        
        pass
    
