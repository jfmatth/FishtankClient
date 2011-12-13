# backup class - will backup necessary files 
import os
import re
import zipfile
import simplecrypt
import uuid

# Should add:
#    - Observer pattern to allow for callbacks during the backup.
#    - a Prep() method to prep the files for backup, and then go() will just rip through all them and
#      back them up.

class Backup(object):
            
    def filespec(self):
        # get the filespec for the backup stream (i.e. *.doc | *.xls | etc)
        # this will return a string for a regex parser (i.e. re.compile)
        pass
        
    def filepath(self):
        # return the system path where to put the files you're going to zip and encrypt
        pass
        
    def temppath(self):
        # temp path where to write the files during working
        pass

    def _prebackup(self):
        pass
        
    def _backup(self):
        # execute the backup
        pass
        
    def _postbackup(self):
        pass
  
    def _preencrypt(self):
        pass
        
    def _encrypt(self):
        # encrypt the backup
        pass
    
    def _postencrypt(self):
        pass
  
    def _encryptkey(self):
        pass
    
    def go(self):
        # do it, backup and encrypt what you should.
 
        self._prebackup()
        self._backup()
        self._postbackup()
        
        self._preencrypt()
        self._encrypt()
        self._postencrypt()

# sub-class the Backup for using the Standard Library and stuff, don't encrypt
class stdBackup(Backup):
    
    def __init__(self, config):
        self.config = config
        
        if self.config['temppath'] == None:
            raise Exception('No temppath setting')
        
        if self.config['filespec'] == None:
            raise Exception('No Filespec setting')
            
    def temppath(self):
        return self.config['temppath']
        
    def filespec(self):
        return self.config['filespec']
        
    # override the necessary methods to get us to just zip up the file, don't encrypt for now.
    def _backup(self):
        self.zipFilename = self.temppath() + "temp.zip"
        zf = zipfile.ZipFile(self.zipFilename,"w",zipfile.ZIP_DEFLATED)
        regex = re.compile( self.filespec() )

        # get all the files that match regex and are on our system, and put them in the zip file
        # we'll do the root of whatever drive we are on now, but eventually, we'll have to do all drives.
        # we can use a generator for all the drives in our backup set.
        
        for root,dirs,files in os.walk("/"):
            for f in files:
                if regex.match(f):
                    if root == "/" :
# need to change to use os.path.fullpath
                        zf.write(root + f)
                    else:
                        zf.write(root + "/" + f)
                        
        zf.close()

class encryptedBackup(stdBackup):

    def __init__(self, config):
        super(encryptedBackup, self).__init__(config)

        # we just need a dict of stuff to store.
        self.localstuff = {}
        
        # generate our own symetrical key for Simplecrypt
        self.localstuff['encryptkey'] = str(uuid.uuid4() )

#        # make sure we have the clientkey out there
#        if self.config['clientkey']==None:
#            raise Exception('No clientkey found')

    def _encryptkey(self):
        return self.localstuff['encryptkey']

    def _encrypt(self):
        # encrypt the zipfile.
        self.encFilename = self.temppath() + "temp.enc"

        s = simplecrypt.SimpleCrypt(self._encryptkey() )
        fo = open(self.encFilename,"wb")
        fi = open(self.zipFilename,"rb")
        
        # loop over the file and save to the encrypted version.
        for block in s.EncryptFile(fi):
            fo.write(block)

        fi.close()
        fo.close()
