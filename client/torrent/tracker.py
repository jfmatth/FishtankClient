import httplib
import urllib2 
import mimetypes
import logging
import os

# setup 'ma logging
#log = logging.getLogger("cloud.tracker")

from client.logger import log

class Tracker(object):
    """
    The tracker class is responsible for talking to the real Tracker.
    """
    
    def __init__(self, tracker="10.0.0.1:8000", 
                 announce_url="/backup/announce", 
                 check_url="/backup/check/?info_hash=", 
                 upload_url="/backup/upload/", 
                 download_url="/backup/download/"):
        """
        
        Parameters
        tracker: IP:PORT string 
        announce_url: URL on Tracker to announce to
        check_url: URL to check info hash of torrents, to see if they're being stored
        upload_url: URL to upload torrents to
        download_url: URL to download torrents from  
        """

        # tracker
        self.tracker_ip = tracker

        # tracker URL fields
        self.announce_url = announce_url
        self.check_url = check_url
        self.upload_url = upload_url
        self.download_url = download_url
        
        # Values specific to posting data in upload_torrent()
        self.post_file_path = "file_path"
        self.post_fields = [("submit", "ok")]
        self.headers = {"Content-type": "application/octet-stream", "Accept": "text/plain"}
        #headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        
        
    ##########################################################
    # Upload torrent to the tracker
    ##########################################################
    
    def has_torrent(self, ti):
        """
        Check if the torrent is on the tracker.
        
        Parameter
        TorrentMetaInfo object
        
        Returns
        True if found, False if not found
        """
        
        log.debug("Checking for torrent on tracker.")
        
        # Calculate info hash
        #info = lt.torrent_info(self.ti.torr_name)
        #self.ti.info_hash=info.info_hash()
        torr_check_url = self.check_url + str(ti.info_hash)
        
        # check with tracker to see if it has this info_hash
        try:
            conn = httplib.HTTPConnection(self.tracker_ip)
            conn.request("GET", torr_check_url)
            result = conn.getresponse()
        except socket.error, e:
            print e
            print "Could not contact the tracker!  Please ensure that it's been started."
            sys.exit(1)
        except Exception, e:
            print e
            print "Unknown Error.  Exiting."
            sys.exit(1)
            
        data = result.read()
        log.debug("Finished checking for torrent: %s" % data)
        conn.close()
        
        if "not found" in data:
            return False
        else:
            return True
        

    def has_backup_file(self, file=""):
        """
        Description
        Check if a backed up file is already on the tracker, using the info hash value.
        
        Arguments
        file: Backup file to torrentize, and then check on tracker.
        
        Returns
        True if backup file exists on the tracker.
        """
        
        # We need the file to exist
        if os.path.exists(file):
            return self.has_torrent(lt.torrent_info(file).info_hash())
        elif os.path.exists(self.file_save_path + "/" + file):
            if DEBUG: logging.debug("path to file: %s\n" % os.path.join(self.file_save_path, file))
            return self.has_torrent(lt.torrent_info(os.path.join(self.file_save_path, file).info_hash()))
        else:
            if DEBUG: logging.debug("path to file does not exist: %s\n" % file)
            return False
        
    def upload_torrent(self, ti):
        """
        POST a torrent to the tracker, if it doesn't already exist
        
        Arguments
        torrent_file: torrent file to upload
        
        Returns
        True if the torrent uploads correctly, false otherwise.
        """
        
        log.debug("Uploading torrent to tracker.")
        
        # If the torrent exists already, don't re-upload it.
        if self.has_torrent(ti):
            log.debug("Torrent already exists.  Will not upload.")
            return True
        
        # Setup our POST values
        fields = self.post_fields
        files = [(self.post_file_path, os.path.basename(ti.torr_name), open(ti.torr_name, "rb").read())]
                    
        content_type, body = self.encode_multipart_formdata(fields, files)
        headers = {'Content-Type': content_type }
        r = urllib2.Request("http://%s%s" % (self.tracker_ip, self.upload_url), body, headers)
        res = urllib2.urlopen(r).read()
    
        if "uploaded correctly" in res:
            return True
        else:
            return False

    def encode_multipart_formdata(self, fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % self.get_content_type(filename))
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body
    
    def get_content_type(self, filename):
        """
        Helper function for encode_multipart_formdata.  Returns mimetype.
        """
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    
    ##########################################################
    # Serve Files / Download torrents from tracker 
    ##########################################################
    
    def download_torrent(self, torr_hash, torr_path):
        """
        Description: Download a torrent from the tracker.
        """        
        
        # this bit of nastiness gives us the filename from the HTTP headers
        try:
            u = urllib2.urlopen("http://" + self.tracker_ip + self.download_url + str(torr_hash))
            torr_short_name = u.headers.getheaders("Content-disposition")[0].split("=")[1]
        except:
            log.debug("Failed to read file from %s" %  self.tracker_ip)
            return ""

        # assuming we have the filename of the torrent...
        if torr_short_name:
            torr_name = torr_path + "/" + torr_short_name
            
            log.debug("torrent shortname: %s\n" % torr_name)
            
            # Write it out to file
            try:
                f = open(torr_name, "wb")
                f.write(u.read())
                u.close()
                f.close()
            except:
                log.debug("Could not open file for writing.")
                return ""
            else:
                return torr_name
        else:
            log.debug("Could not get torrent name from tracker.")
            return ""     
