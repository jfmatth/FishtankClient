import requests
import urllib
import os
import zipfile

from Crypto.PublicKey import RSA

from client.logger import log
from client import encrypt

class Restore:
    
    cloud = None
    settings = None

    restoreurl = None 
    
    def __init__(self):
        pass

    def _privatekey(self):
        """
        this is a method because maybe we have a way to store the private key on the server if it's not found here?
        """
        return self.settings['.privatekey']

    def _tempdir(self):
        return os.path.normpath(self.settings['.installdir'] + self.settings['temppath'] )

    def _clouddir(self):
        return os.path.normpath(self.settings['.installdir'] + self.settings['cloud_files'] )


    def _restorefiles(self, 
                     hash=None,
                     files=None, ):
        """
        Restores a list of files(filelist) from a particular infohash (hash)
        
        hash is the infohash of what to restore
        files is a dict of {'key': encrypted key, 'zipfile': zipfilename, 'files': [list of file tuples (filename, id)] }
        
        Backups are encrypted with a uuid4 key, the key is encrypted with the clients public key, and the encrypted key string is 
        in uni-code, that needs to be encoded so a string comes back. 
        """
        assert not hash == None
        assert not files == None

        # Get the backupkey that encrypted the zip we need from the cloud
        rsakey = RSA.importKey(self._privatekey() ) 
        backupkey = rsakey.decrypt( urllib.unquote( files['key'].encode() ) )
        log.debug("backup key for zip is %s" % backupkey)

        # Get this infohash from the cloud first, decrypt and put in temp directory
        try:
            log.debug("cloud.get (%s)" % hash)
            self.cloud.get(hash)
            
            # we have the file, now decrypt and put into temp directory
            encrypt.decrypt_file(backupkey,
                                 self._clouddir() + "\\" + files['zipfile'],
                                 self._tempdir() +  "\\" + files['zipfile'],
                                )

            # open the zip
            zf = zipfile.ZipFile(self._tempdir() +  "\\" + files['zipfile'])

            # loop through all the files for this restore
            for f in files['files']:
                # f is a tuple (filename, id from DB), so break it out for rest of loop
                fr = f[0]  # fr = File to Restore
                fid = f[1] # fid = file ID

                log.debug("restore file %s" % fr)
                try:
                    # turns out zip files are a PITA!!!
                    # they don't use \\, but /, they strip off the drive letter AND, don't use a leading /, crazy
                    # so we have to massage the filename to get.
                    infoname = os.path.splitdrive(fr)[1].replace("\\","/")[1:]
                      
                    restoreinfo = zf.getinfo(infoname)
                    log.debug("found file in zip")
    
                    # now that we have the info, lets read it to a destination.
                    restore = open(fr,'wb')
                    restore.write( zf.read(infoname) )
                    restore.close()
                    log.debug("File restored")

                    postdata = {"file":fid, "status":"complete"}
                    req = requests.post(self.restoreurl,data=postdata)
                    
                except:
                    postdata = {"file":fid, "status":"fail"}
                    req = requests.post(self.restoreurl,data=postdata)
                
            zf.close()
            
            log.debug("Remove temp zip file.")
            os.remove( self._tempdir() +  "\\" + files['zipfile'] )

        except:
            log.exception("error in getting cloud file")
    
    def check(self):
        """
        Check if there are any restores for this client, and execute them
        """
        assert not self.settings == None
        assert not self.cloud == None
        
        self.restoreurl = "http://" + self.settings["tracker_ip"] + "/manager/restore/" + self.settings[".guid"] + "/"
        
        log.debug("checking for any restores")
        # check if there are any restores
        req = requests.get(self.restoreurl)
        
        if req.status_code == 200:
            # we have something to restore
            log.debug("Found something to restore")
        
            try:
                restoredict = req.json
                wholeid = restoredict["id"]
    
                # update job status with "restoring"
                log.debug( "Restoring for job %s" % wholeid )

                for x in restoredict['restores']:
                    self._restorefiles( hash=x, files=restoredict['restores'][x] )

                # update job as completed.
                log.debug("Job complete")
                postdata = {"restore":wholeid, 'status':'complete'}
                req = requests.post(self.restoreurl, data=postdata)
        
            except:
                log.exception("error restoring")
                raise
        
        else:
            log.debug("none found")
            # don't really care what else we got - FOR NOW.
            pass    
    


    



