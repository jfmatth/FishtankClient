"""
    Backup() will backup all files specified by filespec and drives.  The system will scan for changes to 
            files and zip them up and keep a record of them in a DBM file.
            
            At the end of the Backup.execute() command, two attributes should be accessed:
            
                Backup.Backupfile - a zip file containing all backed up files.
                Backup.BackupDB   - a DBM database of files and their fileinfo.
                
            
        
"""

import zlib
import os
import tempfile
import stat
import time
import json
import anydbm
import zipfile
import re


class Backup(object):
    
    def __init__(self, filespec, tpath, dbpath, drives):
        """
        filespec - Regex of which files to backup.
        tpath    - Temp path for working files.
        dbpath   - Path to where databases are stored.
        drives   - what drives to go through
        """

# need to clean up the init section and how i open files, etc, move to _backupfiles method?

        # error checking
        if not type(drives) == tuple:
            raise Exception("drives parameter needs to be a tuple")
        
        self.filespec = filespec    # file regular expression of what files to backup.
        self.workingpath = tpath    # where we should store our files.
        self.dbpath = dbpath        # location where we should keep our DB files.
        self.drives = drives        # what drives to try, can be directories.

        self.tempfile = tempfile.TemporaryFile(dir=self.workingpath)
        
        self.backupfile = self.tempfile.name + ".zip"
        self.backupdb = os.path.join(self.dbpath, self.tempfile.name + ".db")
        self.backupfull = os.path.join(self.dbpath, "dbfull.db")
        
        self.zipfile = zipfile.ZipFile(self.backupfile, "w", compression=zipfile.ZIP_DEFLATED)
        self.regex = re.compile(self.filespec)
        
        # open our DB's
        self.dbfull = anydbm.open(self.backupfull, "c")
        self.dbdiff = anydbm.open(self.backupdb, "n")



    def __del__(self):
        print "Cleaning up..."

        print "removing dbfull object"
        del(self.dbfull)
        print "removing dbdiff object, and deleting file %s" % self.backupdb
        del(self.dbdiff)
        os.remove(self.backupdb)
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


 
    
    def _backupfiles(self):
        """
        does the actual backup of files to the .zip file.  Comparing the CRC of files it finds to what's in
        the fulldb, if something is found that doesn't match or isn't there, it adds to the diff db and then
        adds to teh zip file.
        
        At the end of execute(), you should have an updated full DB and a diffdb with all files that are in the
        zip file.
        """

       
        # local pointers to class variables.
        dbfull = self.dbfull
        dbdiff = self.dbdiff	
        thezip = self.zipfile
        regex = self.regex

        if not dbfull.isOpen():
            return

        for currdir in self.drives:
            print "backing up %s" % currdir
            for root, dirs, files in os.walk(currdir):
                for f in files:
                    fullpath = os.path.join(root,f)  # c:/dir/dir/filename
                    try:
                        if os.path.isfile(fullpath) and regex.match(fullpath):
                            finfo = self.fileinfo(fullpath)
                            
                            # figure out what we need to do with it.
                            if not dbfull.has_key(fullpath):
                                print "Adding %s" % fullpath,
                                sfinfo = json.dumps(finfo)
                                dbfull[fullpath] = sfinfo
                                dbdiff[fullpath] = sfinfo
                                thezip.write(fullpath)
                                print "..Done!"
                            else:
                                print "Checking %s" % fullpath,
                                if not json.loads(dbfull[fullpath])['crc'] == finfo['crc']:
                                    print "..updating",
                                    sfinfo = json.dumps(finfo)
                                    dbfull[fullpath] = sfinfo
                                    dbdiff[fullpath] = sfinfo
                                    thezip.write(fullpath)
                                    
                                print "..Done!"
                    except Exception as e:
                        print "%s Exception on %s" % (e, fullpath)

            thezip.close()
            dbfull.close()
            dbdiff.close()
       
    def execute(self):
        self._backupfiles()