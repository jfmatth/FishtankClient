import os
import zlib
import time
import stat
import anydbm
import json
import time

def crcval(fileName):
    return "%X"%(0xFFFFFFFF)

    try:
        prev = 0
        for eachLine in open(fileName,"rb"):
            prev = zlib.crc32(eachLine, prev)
        return "%X"%(prev & 0xFFFFFFFF)
    except:
        return "%X"%(0xFFFFFFFF)


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


def main():
    db = anydbm.open("./walktest.db", "c")
    for root, dirs, files in os.walk("c:/"):
        line = ""
        print root,
        for f in files:
            fullpath = os.path.join(root, f)

            try:
                finfo = fileinfo(fullpath)
                if not db.has_key(fullpath) or not json.loads(db[fullpath])['crc'] == finfo['crc']:
                    db[fullpath] = json.dumps( fileinfo(fullpath) )
                    
            except:
                pass
            
            line+="."
            
        print line
    db.close()


if __name__ =="__main__":
    start = time.clock()
    main()
    print "seconds = %s" % (time.clock() - start)