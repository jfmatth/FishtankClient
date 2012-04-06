"""
Backup() will backup all files specified by filespec and drives.  The system will scan for changes to 
files and zip them up and keep a record of them in a DBM file.

At the end of the backup.execute(), two files should be retrieved:
  .zipfilename - full pathname to the .zip file that contains all the files
  .diffdbname  - full pathname to the .dbm file that indexes all the files.
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
import uuid


from client.logger import log

def crcval(fileName):
    prev = 0
    for eachLine in open(fileName,"rb"):
        prev = zlib.crc32(eachLine, prev)
    return "%X"%(prev & 0xFFFFFFFF)



def fileinfo(filename):
    """ returns a dict of all the file information we want of a file """
    fi = {}
    fs = os.stat(filename)

    fi['crc']      = crcval(filename)
    fi['filename'] = filename
    fi['size']     = fs[stat.ST_SIZE]
    fi['modified'] = time.strftime("%m/%d/%Y %I:%M:%S %p",time.localtime(fs[stat.ST_MTIME]))
    fi['accessed'] = time.strftime("%m/%d/%Y %I:%M:%S %p",time.localtime(fs[stat.ST_ATIME]))
    fi['created']  = time.strftime("%m/%d/%Y %I:%M:%S %p",time.localtime(fs[stat.ST_CTIME]))
    
    return fi


def ZipDBFile(path):
    """ Return a unique pair for zip and db filenames, prefixed with the path """
    tempname = str( uuid.uuid4() )

    zipfilename = os.path.join(path, tempname + ".backup")
    dbfilename  = os.path.join(path, tempname + ".db")

    return zipfilename, dbfilename


def BackupGenerator(filespec = None,
                    temppath = None,
                    datapath = None,
                    drives   = None,
                    limit    = 100,
                    ):
    """ A generators that returns two filenames:
        zipfile, dbfile. zipfile is a zip of all files that should be backed up because the CRC changed, or it wasn't 
        in the fulldb.dbm database.  dbfile is a DBM of the zipfile files
        
        filespec - which files to backup (*.txt), but as a python regular expression.
        temppath - Where to put the temporary files (zip and db)
        datapath - where does the dbfull.db live?
        drives   - the outer loop of which locations to backup (C:/, d:/, etc), can be folder qualification too.
        limit    - how big in MB should each (pre compressed) backup set be before yielding. backed up
    """
    
    if (filespec == None or temppath == None or datapath == None or drives == None):
        raise Exception("invalid values for Backup")

    if not type(drives)==list:
        raise Exception("drives must be of type list") 
    
    fulldbname = os.path.join(datapath, "dbfull.db")
    fileregex = re.compile(filespec)
    
    _limit = limit * 1024 * 1024
    _size = 0 
    _zip    = None
    _dbdiff = None
    _dbfull = anydbm.open(fulldbname, "c")

    _count = 0

    for currdir in drives:
        if len(currdir) != 0:
            for root, dirs, files in os.walk(currdir):
                for f in files:
                    fullpath = os.path.normcase(os.path.normpath(os.path.join(root,f) ) ) 

                    if os.path.isfile(fullpath) and fileregex.match(fullpath):
                        try:
                            finfo = fileinfo(fullpath)
                            
                            if not _dbfull.has_key(fullpath) or not json.loads(_dbfull[fullpath])['crc'] == finfo['crc']:
                                # it's not in our DB or it's different, then update the DB and the zip
                                
                                if _zip == None:
                                    # we need a zip and DBM opened, cause they may have been closed
                                    # when we generated back.
                                    zf, dbf = ZipDBFile(temppath)
                                    _zip    = zipfile.ZipFile(zf, "w", compression=zipfile.ZIP_DEFLATED)
                                    _dbdiff = anydbm.open(dbf, "n")
    
                                sfinfo = json.dumps(finfo)                            
                                _dbdiff[fullpath] = sfinfo
                                _zip.write(fullpath)
    
                                _size  += finfo['size']
    
                                if _size >= _limit:
                                    # we have "filled" our zip /db combo, yield.
                                    _zip.close()
                                    _dbdiff.close()
                                    _zip = None
                                    _dbdiff = None
                                    _size = 0
                                    yield zf, dbf

                        except Exception as e:
                            log.critical("%s Exception on %s" % (e, fullpath) )
 

    # once we have traversed everything, clean up the last of it all.                                
    if not _zip == None:
        # still here 
        _zip.close()
        _dbdiff.close()
        _zip = None
        _dbdiff = None
        _dbfull.close()
        _dbfull = None
        
        yield zf, dbf





##########################
# OLD CODE BELOW 
##########################


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
        if not type(drives) == list:
            raise Exception("drives parameter needs to be a tuple")
        
        self.filespec = filespec    # file regular expression of what files to backup.
        self.workingpath = tpath    # where we should store our files.
        self.dbpath = dbpath        # location where we should keep our DB files.
        self.drives = drives        # what drives to try, can be directories.

        # generate a file and name in the temporary space, ans use that as the starting 
        # point for the zip and diff db names.
        self.tempfile = tempfile.TemporaryFile(dir=self.workingpath)
        self.zipfilename = self.tempfile.name + ".zip"
        log.debug("zipfilename %s"%self.zipfilename)
        
        self.diffdbname = os.path.join(self.dbpath, self.tempfile.name + ".db")
        log.debug("diffdbname %s"%self.diffdbname)
        
        self.fulldbname = os.path.join(self.dbpath, "dbfull.db")
        log.debug("fulldbname %s"%self.fulldbname)
        
        # our actuall storage.
        self.zipfile = zipfile.ZipFile(self.zipfilename, "w", compression=zipfile.ZIP_DEFLATED)
        self.dbfull = anydbm.open(self.fulldbname, "c")
        self.dbdiff = anydbm.open(self.diffdbname, "n")

        self.regex = re.compile(self.filespec)

        self.backupcount = 0

    def __del__(self):
        del(self.dbfull)
        del(self.dbdiff)
        os.remove(self.diffdbname)
        self.zipfile.close()
        del(self.zipfile)
        os.remove(self.zipfilename)


    
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

        log.debug("Backup starting..")
        for currdir in self.drives:
            if len(currdir) != 0:
                log.debug("backing up %s" % currdir)
                for root, dirs, files in os.walk(currdir):
                    for f in files:
                        fullpath = os.path.normcase(os.path.normpath(os.path.join(root,f) ) ) # c:/dir/dir/filename
                        try:
                            if os.path.isfile(fullpath) and regex.match(fullpath):
                                finfo = self.fileinfo(fullpath)
                                
                                # figure out what we need to do with it.
                                if not dbfull.has_key(fullpath):
                                    log.debug("Adding %s" % fullpath)
                                    sfinfo = json.dumps(finfo)
                                    dbfull[fullpath] = sfinfo
                                    dbdiff[fullpath] = sfinfo
                                    thezip.write(fullpath)
                                else:
                                    if not json.loads(dbfull[fullpath])['crc'] == finfo['crc']:
                                        log.debug("refreshing %s" % fullpath)
                                        sfinfo = json.dumps(finfo)
                                        dbfull[fullpath] = sfinfo
                                        dbdiff[fullpath] = sfinfo
                                        thezip.write(fullpath)
                        except Exception as e:
                            log.critical("%s Exception on %s" % (e, fullpath) )

        # we only do this once, so close all the files when we are done.
        self.backupcount = len(dbdiff)
        thezip.close()
        dbfull.close()
        dbdiff.close()
       
        log.info("Backup completed, %s files backed up" % self.backupcount)

    def execute(self):
        self._backupfiles()