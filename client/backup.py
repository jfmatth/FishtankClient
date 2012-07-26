"""
Backup() will backup all files specified by filespec and drives.  The system will scan for changes to 
files and zip them up and keep a record of them in a DBM file.

At the end of the backup.execute(), two files should be retrieved:
  .zipfilename - full pathname to the .zip file that contains all the files
  .diffdbname  - full pathname to the .dbm file that indexes all the files.
"""

import zlib
import os
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

def BackupGenerator(spec = None,
                    temppath = None,
                    datapath = None,
                    drives   = None,
                    limit    = 100,
                    stopbackup = None,
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
    
    if (spec == None or temppath == None or datapath == None or drives == None):
        raise Exception("invalid values for Backup")

    if not type(drives)==list:
        raise Exception("drives must be of type list") 

    log.debug("temppath = %s" % temppath)
    log.debug("datapath = %s" % datapath)
    log.debug("drives = %s" % drives)

    maxfilecount = 1000

    try:
        fulldbname = os.path.join(datapath, "dbfull.db")
        
        _limit = limit * 1024 * 1024
        log.debug("filesize = %s" % _limit)
        _size = 0 
        _zip    = None
        _dbdiff = None
        _dbfull = anydbm.open(fulldbname, "c")
        
        # define our filenames as blanks, so we can see them?
        zf = None
        dbf = None
    
        _count = 0
        
        # define a variable to stop us backing up, cause the runbackup() could be "expensive"
        stoprunning = False
    
        log.debug("Starting loop over drives")
        
        for drive in drives:
#            if stoprunning:
#                break
        
            currdir = os.path.normpath(drive)
                
            log.debug("currdir %s in drives" % currdir)
                
            if len(currdir) != 0:
                
                for root, dirs, files in os.walk(currdir):
                    
                    if stopbackup():
                        log.debug("raise StopIteration")
                        raise StopIteration

                    # if this directory shouldn't be 'walked' then move on
                    if not spec.dirok(root):
                        continue

                    log.debug("backup: size = %s, count=%s" % (_size, _count) )
                    
                    for f in files:
                        fullpath = os.path.normcase(os.path.normpath(os.path.join(root,f) ) ) 
    
                        if os.path.isfile(fullpath) and spec.fileok(fullpath):
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
                                    _zip.write(fullpath)
                                    _dbdiff[fullpath] = sfinfo
                                    _count += 1
        
                                    _size  += finfo['size']
        
                                    # check for stop 'zipping' condition.
                                    if (_size >= _limit or _count >= maxfilecount or stoprunning):
                                        log.debug("Size: %s, len(_dbdiff) = %s " % (_size, len(_dbdiff) ) )
                                        _zip.close()
                                        _dbdiff.close()
                                        _zip = None
                                        _dbdiff = None
                                        _size = 0
                                        _count = 0
                                        yield zf, dbf
    
                            except Exception as e:
                                log.critical("%s Exception on %s" % (e, fullpath) )
     
        log.debug("Done looping over drives")

    
        if stoprunning:
            log.debug("Stoprunning signal received")
            
        # once we have traversed everything, clean up the last of it all.                                
        if not _zip == None:
            # still here
            log.info("len(_dbdiff) = %s " % len(_dbdiff) )
            _zip.close()
            _dbdiff.close()
            _zip = None
            _dbdiff = None
            _dbfull.close()
            _dbfull = None

            yield zf, dbf
    
    except StopIteration:
        #                        stoprunning = True
        #                        break
        if not _zip == None:
            _zip.close()
            _dbdiff.close()
            _zip = None
            _dbdiff = None
            log.debug("Erase dbf %s" % dbf)
            os.remove(dbf)
            log.debug("Erase zip %s" % zf)
            os.remove(zf)
            _size = 0
            _count = 0
            
    
    except:
        log.exception("Error in BackupGenerator")
    