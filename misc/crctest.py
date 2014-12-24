import sys
import zlib
import time

# read the file with variable ways

filename = sys.argv[1]

start = time.clock()
prev = 0
for eachLine in open(filename,"rb"):
    prev = zlib.adler32(eachLine, prev)
print "seconds = %s" % (time.clock() - start)

start = time.clock()
prev = 0
for eachLine in open(filename,"rb"):
    prev = zlib.crc32(eachLine, prev)

print "seconds = %s" % (time.clock() - start)

