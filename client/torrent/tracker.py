import httplib
import urllib2 
import urllib
import mimetypes
import logging
import os
import socket
import sys
from django.core import serializers
import json

# setup 'ma logging
#log = logging.getLogger("cloud.tracker")

from client.logger import log

class Tracker(object):
    """
    The tracker class is responsible for talking to the real Tracker.
    """
    
    def __init__(self, 
                 tracker="10.0.0.1:8000", 
                 announce_url="/backup/announce", 
                 checkt_url="/backup/check/?info_hash=", 
                 upload_url="/backup/upload/", 
                 download_url="/backup/download/",
                 checku_url="/backup/check/?uuid=",
                 status_url="/backup/status/",
                 attachedtorrs_url="/backup/attachedtorrs",
                 detachtorrs_url="/backup/detachtorrs",
                 ):
        """
        
        Parameters
        tracker: IP:PORT string 
        announce_url: URL on Tracker to announce to
        checkt_url: URL to check info hash of torrents, to see if they're being stored
        checku_url: URL to check uuid of backups, to see if they exist
        upload_url: URL to upload torrents to
        download_url: URL to download torrents from
        status_url: URL to change the start/stop status of a client
        """

        # tracker
        self.tracker_ip = tracker

        # tracker URL fields
        self.announce_url = announce_url
        self.checkt_url = checkt_url
        self.checku_url = checku_url
        self.upload_url = upload_url
        self.download_url = download_url
        self.status_url = status_url
        self.attachedtorrs_url = attachedtorrs_url
        self.detachtorrs_url = detachtorrs_url
        
        # Values specific to posting data in upload_torrent()
        self.post_file_path = "file_path"
        self.post_fields = [("submit", "ok")]
        self.headers = {"Content-type": "application/octet-stream", "Accept": "text/plain"}
        #headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        
        
    ##########################################################
    # Upload torrent to the tracker
    ##########################################################
    
    def update_client_status(self, guid, status):
        """
        Update the status of the client with <guid> to <status> (start/stop)
        """
        url = ("%s?%s" %(self.status_url, urllib.urlencode(
                                                           {'guid': guid,
                                                            'status': status,
                                                            }
                                                           )
                         )
               )
        
        return self.send_url(url)
        
    
    def has_torrent(self, ti):
        """
        Check if a torrent exists on the tracker
        """
        
        ihash_on_tracker = self.send_url(self.checkt_url + str(ti.info_hash))
        if "found" in ihash_on_tracker:
            log.debug("Torrent info hash %s found on tracker." % ti.info_hash)
            return False
        else: 
            return True
        
    def has_uuid(self, ti):
        """
        Check if a uuid exists on the tracker
        """
        uuid_on_tracker = self.send_url(self.checku_url + str(ti.file_uuid))
        if "not found" in uuid_on_tracker:
            log.debug("UUID %s not found on tracker." % ti.file_uuid)
            return False
        else:
            return True
    
    def can_upload(self, ti):
        """
        Tells us if we can upload the torrent.  Check two conditions.
        1) is torrent already on tracker?  if true, return false
        2) is backup on the tracker?  if false return true
        
        Parameter
        TorrentMetaInfo object
        
        Returns
        True if we can upload, otherwise false.
        """
        
        log.debug("Checking if we can upload the torrent...")
               
        # Check for the torrent on the tracker.  if it already exists,
        # we don't need to upload.
        if self.has_torrent(ti):
            return False
        
        # Check if the backup's uuid exists on tracker.  if it doesn't,
        # we shouldn't upload.
        if not self.has_uuid(ti):
            return False
            
        return True
    
        
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
        if not self.can_upload(ti):
            log.debug("Not uploading.")
            return True
        
        # Setup our POST values
        fields = self.post_fields
        fields.append(("uuid", ti.file_uuid))
        files = [(self.post_file_path, os.path.basename(ti.torr_name), open(ti.torr_name, "rb").read())]
                    
        content_type, body = self.encode_multipart_formdata(fields, files)
        headers = {'Content-Type': content_type }
        r = urllib2.Request("http://%s%s" % (self.tracker_ip, self.upload_url), body, headers)
        res = urllib2.urlopen(r).read()
    
        if "uploaded correctly" in res:
            return True
        else:
            return False


    def send_url(self, url):
        """
        Generic function to check URL and pass back the output.
        """
        
        # check with tracker to see if it has this info_hash
        try:
            conn = httplib.HTTPConnection(self.tracker_ip)
            conn.request("GET", url)
            result = conn.getresponse()
        except socket.error, e:
            log.warning("Could not contact the tracker!  Please ensure that it's been started.")
            sys.exit(1)
        except Exception, e:
            log.critical("Unknown Error.  Exiting.")
            sys.exit(1)
            
        data = result.read()
        conn.close()
        
        return data
        
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

    def get_attachedtors(self, my_guid):
        """
        Get a list of torrents associated with a guid, from the tracker.
        """        
        
        torrents_on_tracker = self.send_url(self.attachedtorrs_url + "/" + str(my_guid))
        torrents_on_tracker = json.loads(torrents_on_tracker)
        
        if "not found" in torrents_on_tracker:
            log.debug("Can't get torrents.  GUID %s not found on tracker." % my_guid)
            return []
        else:
            return torrents_on_tracker
        
    def detachtors(self, my_guid, torrent_list):
        """
        Takes a list of torrents and sends them to the tracker to disassociate from the client.
        """
        
        #params = urllib.urlencode(json.dumps({"torrents": torrent_list}))
        #params = json.dumps("thisisatest") #{"torrents": "thisisatest"})
        tl_serialized = json.dumps(torrent_list)
        params = urllib.urlencode({"torrents": tl_serialized})
        url = "http://" + self.tracker_ip + self.detachtorrs_url + "/" + str(my_guid)
        #headers = {'Content-Type': 'application/json'}
        
        response = urllib2.urlopen(url=url, data=params)
        data = response.read()
        response.close()
        return data    
    
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
