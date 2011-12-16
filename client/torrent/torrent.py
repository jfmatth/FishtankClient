"""
torrent classes for tbackup

add to python path for libtorrent: 
set PYTHONPATH=C:\TorrentBackup\misc\clients\tbackup\bin\python\Lib\site-packages

# Cloud Example
import torrent
import sys
c = torrent.Cloud()
c.put("c:/torrent/files/AcrobatPro_10_Web_WWEFD.zip")

# Download torrent(s)
c = torrent.Cloud("c:/torrentdir", "c:/filesdir", "10.0.0.1:8000")
c.get_torrents_by_id(1)
c.get_torrents_by_id([1, 2])

# Get files by torr name
c.get_files_by_torr_name("AcrobatPro_10_Web_WWEFD.zip.torrent")



# TorrentMetaInfo example
import torrent
ti = torrent.TorrentMetaInfo("c:/torrent", "c:/torrent/files", "10.0.0.1:8000", "ct.py")
ti = torrent.TorrentMetaInfo("c:/torrent", "c:/torrent/files", "10.0.0.1:8000", "My Documents.zip")
ti = torrent.TorrentMetaInfo("c:/torrent", "c:/torrent/files", "10.0.0.1:8000", "AcrobatPro_10_Web_WWEFD.zip")

# How to use the Torrent class
import torrent
t=torrent.Torrent(ti)
t.create_torrent()
t.has_torrent()
t.upload_torrent()
t.serve_torrent()
t.is_seed()


# adding torrents to a session
tf = lt.bdecode(open(f, 'rb').read())
info = lt.torrent_info(tf)
atp["resume_data"] = open(os.path.join(torr_path, info.name() + '.fastresume').read()
atp["ti"] = info
atp["save_path"] = torr_path
atp["storage_mode"] = lt.storage_mode_t.storage_mode_sparse
atp["paused"] = False
atp["auto_managed"] = True
atp["duplicate_is_error"] = True
h = session.add_torrent(atp)
# use h handle to check on torrent



# Helpful libtorrent stuff
import libtorrent as lt
s = lt.session()
s.listen_on(9999,9999)
ti = lt.torrent_info("C:/torrent/AcrobatPro_10_Web_WWEFD.zip.torrent")
h = s.add_torrent({"ti": ti, "save_path": "C:/torrent/files"})
h.is_valid()
h.is_seed()

# Setting up and reading from a HTTP connection
conn = httplib.HTTPConnection("10.0.0.1:8000")
conn.request("GET", "/backup/check")
result = conn.getresponse()
data = result.read()
data
"""

import os
import glob
import sys
import logging
import socket
import libtorrent as lt
import httplib, urllib2, mimetypes

# setup 'ma logging
logging.basicConfig(level=logging.DEBUG)
h = logging.StreamHandler()
f = logging.Formatter("%(levelname)s %(funcName)s %(lineno)d")
h.setFormatter(f)

log = logging.getLogger("torrent.py")
log.addHandler(h)
log.setLevel(logging.DEBUG)

DEBUG = 1

class Tracker(object):
    def __init__(self, tracker="10.0.0.1:8000", announce_url="/backup/announce", check_url="/backup/check/?info_hash=", upload_url="/backup/upload/", download_url="/backup/download/"):
        """
        Description: Tracker class.
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
        Description: Check if the torrent is on the tracker.
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
        Description: Check if a backed up file is already on the tracker, using the
                    info hash value.
        
        Arguments: Backup file to torrentize, and then check on tracker.
        
        Returns: True if backup file exists on the tracker.
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
        Description: POST a torrent to the tracker, if it doesn't already exist
        
        Arguments:
        torrent_file: torrent file to upload
        
        Returns: True if the torrent uploads correctly, false otherwise.
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
    
    def download_torrent(self, torr_id, torr_path):
        """
        Description: Download a torrent from the tracker.
        """
        
        # this bit of nastiness gives us the filename from the HTTP headers
        try:
            u = urllib2.urlopen("http://" + self.tracker_ip + self.download_url + str(torr_id))
            torr_short_name = u.headers.getheaders("Content-disposition")[0].split("=")[1]
        except Exception, e:
            print e, "\nFailed to read file from", self.tracker_ip

        # assuming we have the filename of the torrent...
        if torr_short_name:
            torr_name = torr_path + "/" + torr_short_name
            
            # Write it out to file
            try:
                f = open(torr_name, "wb")
                f.write(u.read())
                u.close()
                f.close()
            except:
                return ""
            else:
                return torr_name
        else:
            return ""     


class CreateTorrent(object):
    """
    Description: The torrent class provides for the creation of new torrents, given a file to torrentize.  A torrent may be checked
    against the tracker to see if it has already been uploaded.  Torrents that are not on the tracker are
    uploaded.
    """
    
    ##########################################################
    # Create/load a new torrent
    ##########################################################
    
    def __init__(self, ti):
        """
        Description: Create a Torrent, given a TorrentMetaInfo Object.  Assumes a valid TorrentMetaInfo object.
        """
        
        # Initialize our only variable -- A TorrentMetaInfo object.
        self.ti = ti

    def create(self, tracker_ip):
        """
        Description: Creates a new torrent.
        """
        
        log.debug("Creating new torrent file, setting tracker to: %s" % tracker_ip)
        
        # Set the name of our torrent
        self.ti.torr_name = self.ti.torr_path + "/" + self.name_torrent(self.ti.file_name)                      
        
        # Create a storage object, and add the file which will be torrentized
        file_st = lt.file_storage()
        lt.add_files(file_st, self.ti.file_name)
               
        # Create the torrent
        try:
            torr = lt.create_torrent(file_st, self.ti.piece_size)
            torr.add_tracker("http://" + tracker_ip.tracker_ip + tracker_ip.announce_url)
            torr.set_comment(self.ti.comments)
            torr.set_creator(self.ti.creator)
            lt.set_piece_hashes(torr, os.path.dirname(self.ti.file_name))
        except:
            log.exception("Failed to create torrent")
            raise
        
        # Write to file
        try:
            f = open(self.ti.torr_name, "wb")
            f.write(lt.bencode(torr.generate()))
            f.close()
        except:
            raise
        
        # get the info_hash before returning
        self.ti.info      = lt.torrent_info(self.ti.torr_name)
        self.ti.info_hash = self.ti.info.info_hash()
        
        log.debug("New torrent details: %s" % self.ti)
        
        # Return the TorrentMetaInfo Object
        return self.ti
        
    
    def name_torrent(self, backup_file):
        """
        Description: Helper function which names a torrent based on the name of the backup_file which has been passed.
        
        Arguments: backup_file: A string containing the name of the backup file.
        
        Returns: A string containing the basename for the new torrent.
        """
        
        #file_base = os.path.basename(backup_file)
        #return file_base.split(".")[0] + ".torrent"
        return str(os.path.basename(backup_file)) + ".torrent"
    
#    def load_torrent(self, torr_path):
#        """
#        Description: Load an existing torrent from file.  Presumably to check it against the tracker.
#       """
#       
#        self.info = lt.torrent_info(self.torr_path)
#        self.ti = TorrentMetaInfo(self, torr_save_path, file_save_path, tracker, backup_file = None, torr_file = None)
#        
#        self.info_hash=self.info.info_hash()
#        self.torr_check = Torrent.check_url + "/?info_hash=" + str(self.info_hash)


    ##########################################################
    # Various getters and setters and helpers -- will probably 
    # eliminate most of these.  some may need to be moved to 
    # other classes
    ##########################################################
        
    def add_storage(self):
        lt.add_files(self.files, self.file)
    
    def set_comment(self, comment):
        self.comment = comment
    
    def get_comment(self):
        return self.comment    

    def set_creator(self, creator):
        self.creator = creator

    def get_creator(self):
        return self.creator
    
    def set_priv(self, priv):
        self.priv = priv
        
    def get_priv(self):
        return self.priv
    
    def is_seed(self):
        """
        Just tell us if we're seeding the torrent in the session.
        """
        if self.torr_session:
            return self.torr_session.is_seed()
        else:
            return False
        
        
class TorrentMetaInfo(object):
    """
    Metainfo class used by Torrent to store information about the torrent.  TorrentMetaInfo objects are passed
    to the Torrent class.
    """
    
    def __init__(self, torr_save_path, file_save_path, tracker, backup_file = None, torr_file = None):
        """
        You must define a path where the torrent is saved, where the data files are saved, a tracker,
        and an optional torrent file.  The torrent file is given if we are getting files from the
        tracker.  If we are putting files, this should be None.
        """
        
        log.debug("Initializing TorrentMetaInfo: %s %s %s %s %s" %(torr_save_path, file_save_path, tracker, backup_file, torr_file))
        
        # values defined by this class
        self.torr_path = self.valid_dir(torr_save_path)
        self.file_path = self.valid_dir(file_save_path)
        self.torr_name = self.valid_file(str(self.torr_path) + "/" + str(torr_file))
        self.file_name = self.valid_file(str(self.file_path) + "/" + str(backup_file))
        
        # Values that are filled in later, or that are optional.
        self.piece_size = 1048576                         # Default piece size.  Set this higher.
        self.priv = False                               # Private torrent?
        self.peer_id = ""
        self.comments = ""
        self.creator = ""
        
        # set the info_hash if we're given a torrent to start with
        if self.torr_name:
            self.info = lt.torrent_info(self.torr_name)
            self.info_hash = self.info.info_hash() 
        
        # set tracker
        self.tracker = tracker 
        
    def valid_dir(self, dir):
        """
        Check if we have a valid directory, or raise an exception.
        """
        if dir and os.path.isdir(dir):
            return dir.rstrip("/").rstrip("\\")  # path where torrent will be stored, strip trailing slashes
        else:
            raise Exception("Did not specify a valid directory.")
        
    def valid_file(self, path_to_torrent):
        """
        Check if a torrent file exists as a file.
        """
        
        if file and os.path.isfile(path_to_torrent):
            return path_to_torrent
        else:
            return None

    def __str__(self):
        return self.torr_name

    def get_info(self):
        return self.info
    
    def get_fpath(self):
        return self.file_path

    def set_peer_id(self, peer_id):
        self.peer_id = peer_id
        
    def set_piece_size(self, piece_size):
        self.piece_size = piece_size
        
    def set_priv(self, priv):
        self.priv = priv
        
    def set_comments(self, comments):
        self.comments = comments
    
    def set_creator(self, creator):
        self.creator = creator
        
    def is_valid_torr(self):
        if self.torr_name:
            return True
        else:
            return False
    
    def is_valid_create_object(self):
        # we need all of the following to be a valid create object
        if self.torr_path and self.file_name and self.file_path:
            return True
        else:
            return False
        
class Session(object):
    """
    Description: Handle serving of torrents to peers.
    """
    
    # Default values for serving a torrent
    to_port_default = 40000
    from_port_default = 40010
    
    def __init__(self, session_dir):
        self.session = None
        self.session_dir = session_dir
        self.handles = []
        self.alerts = []
    
    def register(self, callback):
        """
        Register our callback function.
        """
        if hasattr(callback, '__call__'):
            self.callback = callback
        else:
            raise Exception("Object %s not callable." % str(callback))
        
    def __check_callback(self):
        # need to call register() first
        if not self.callback:
            raise Exception("Callback not specified.")
        
    def serve(self, ti, to_port=to_port_default, from_port=from_port_default):
        """
        Description: Create session.  Add torrent to session if it doesn't already exist.
        ti = TorrentMetaInfo object
        """
            
        log.debug("to_port: %s, from_port: %s" %(to_port, from_port))
        log.debug("file save path: %s, torr save path: %s\n" %(ti.file_path, ti.torr_path))
        
        self.__check_callback()
        
        if not ti.is_valid_torr():
            raise Exception("No torrent specified in TorrentMetaInfo")
        
        # start the session if it hasn't been already
        if not self.session:
            log.debug("No session exists, starting...")
            self.session = lt.session()
            self.session.listen_on(to_port, from_port)
            
        # check if we're serving this torrent, and if not, add it to the session
        th = self.session.find_torrent(ti.info_hash)
        if not th.is_valid():
            log.debug("Adding Torrent to session")
            
            td = {}
            ti.info = lt.torrent_info(ti.torr_name)
            try:
                td["resume_data"] = open(ti.torr_path + "/" + ti.info.name() + '.fastresume', 'rb').read()
            except:
                pass
            td["ti"] = ti.info
            td["save_path"] = ti.get_fpath()
            td["auto_managed"] = True
            td["duplicate_is_error"] = True
            td["paused"] = False
            
            handle = self.session.add_torrent(td)
            self.handles.append(handle)
        else:
            log.debug("Torrent exists in session.")
            #handle = th


        # wait for seeding to complete before returning.  Check callback at each pass.
        log.debug("Seeding torrent.")
        while True:
            if not self.callback():
                return False
            
            if handle.is_seed():
                return True
            
    def serve_all_torrents(self, torr_dir, data_dir, tracker_ip, ext):
        """
        Look in our torrent directory and attempt to serve all torrents that exist there.
        """

        for f in glob.glob(torr_dir + "/*." + str(ext)):
            log.debug("torr_dir: %s, f: %s" %(torr_dir, f))
            ti = TorrentMetaInfo(torr_dir, data_dir, tracker_ip, torr_file=os.path.basename(f))
            self.serve(ti)
            
    def save_session(self):
        
        # loop through our handles and write out fast resume data
        for h in handles:
            if h.is_valid() and h.has_metadata():
                data = lt.bencode(h.write_resume_data())
                open(os.path.join(options.save_path, h.get_torrent_info().name() + '.fastresume'), 'wb').write(data)
        
        # save session settings here
    
    def load_session(self):
        # resume out old settings here...
        
        
        
        # load up our torrents.  right now let's just look in our local directory.
        # eventually, we may want something else to determine what is being served...
        for f in glob.glob(torr_dir + "/*." + str(ext)):
            log.debug("torr_dir: %s, f: %s" %(torr_dir, f))
            ti = TorrentMetaInfo(torr_dir, data_dir, tracker_ip, torr_file=os.path.basename(f))
            self.serve(ti)
        
        pass
        
class Cloud(object):
    """
    Put or get a file from the Cloud.  This class maintains the session.
    """
    
    # default torrent extension
    ext = "torrent"
    
    def __init__(self, torr_dir="c:/torrent", data_dir="c:/torrent/files", tracker_ip="10.0.0.1:8000", callback=lambda: "."):        
        self.callback = callback
        self.data_dir = data_dir
        self.torr_dir = torr_dir
        self.my_tracker = Tracker(tracker_ip)
        
        self.session = Session(torr_dir)         # just put in the same directory as the torrents for now...
        self.session.register(self.callback)
            
    def put(self, backup_file):
        """
        Put files to the tracker, given an encrypted ZIP archive, and then serve them.
        """
        
        log.debug("backup_file = %s, data_dir = %s, torr_dir = %s, tracker = %s" % (backup_file, self.data_dir, self.torr_dir, self.my_tracker.tracker_ip))        
        
        # setup our TorrentMetaInfo object and create a torrent
        ti = TorrentMetaInfo(self.torr_dir, self.data_dir, self.my_tracker.tracker_ip, os.path.basename(backup_file))
        
        # Make the torrent file and save new TorrentMetaInfo object with torrent name
        if ti.is_valid_create_object():        
            t=CreateTorrent(ti)
            ti = t.create(self.my_tracker)
        else:
            raise Exception("TorrentMetaInfo object is not valid for CreateTorrent.")
        
        # Upload torrent to tracker.  Return false if the upload fails.
        if not self.my_tracker.upload_torrent(ti):
            return False

        # Serve the torrent
        return self.session.serve(ti)
    
    def get_torrents(self):
        """
        This function needs to talk to tracker -- tell tracker how much free space we have.  The tracker is responsible for determining
        what needs to be backed up, and it passes back the list of info_hashes that we should download.
        """
        
        # ask tracker what we need to download
        
        # tracker returns a list of torrent id's
        
        # download the torrents from the tracker, given the torrent id
        
        # Return a dictionary with the torrent name and associated info_hash   
        # for testing purposes, just list the first torrent on the tracker
        
        return {"ct.py.torrent": "ad39f34fb8a38936d566b345c8d54482c23731fa", "AcrobatPro_10_Web_WWEFD.zip.torrent": "0b36cb9ed4ce43c50f9df4a9f9790818cadaddb2"}    
    
    def get_files(self):
        """
        Get files from torrents stored locally.
        """
        
        log.debug("Starting downloads...")
        
        torrents = self.get_torrents()
        
        for filename,infohash in torrents.items():
            log.debug("grabbing torrent: %s, info hash: %s" %(filename, infohash))
            ti = TorrentMetaInfo(self.torr_dir, self.data_dir, self.my_tracker.tracker_ip, torr_file=filename)
            self.session.serve(ti)
        return
        
        
        #for ih in info_hash_l:        
        #    for f in glob.glob(torr_dir + "/*." + str(ext)):            
        #        info = lt.torrent_info(f)
        #        info_hash = info.info_hash()
        #        
        #        # if we find the 
        #        if str(ih) == str(info_hash):             
        #            ti = TorrentMetaInfo(torr_dir, data_dir, tracker_ip, torr_file=os.path.basename(f))
        #            self.__serve(ti)
        #
        #self.session.serve(ti)
        
    def serve_torrents(self):
        """
        Serve up all torrents in our torr directory.
        """
        self.session.serve_all_torrents(self.torr_dir, self.data_dir, self.my_tracker.tracker_ip, Cloud.ext)
    
    def get_files_by_torr_name(self, torr_name_l):
        """
        Download files given a torrent name
        """
        # setup our TorrentMetaInfo object and create a torrent
        
        if hasattr(torr_name_l, '__iter__'):
            for t in torr_name_l:  
                ti = TorrentMetaInfo(self.torr_dir, self.data_dir, self.my_tracker.tracker_ip, torr_file=t)
                self.session.serve(ti)
        else:
            ti = TorrentMetaInfo(self.torr_dir, self.data_dir, self.my_tracker.tracker_ip, torr_file=torr_name_l)
            self.session.serve(ti)
    
    def get_torrents_by_id(self, torr_id_l):
        """
        Description: Pull a torrent down from the tracker by ID.  Parameter is a list of torrent ID's.
        """
        
        flag = 0
        
        if hasattr(torr_id_l, '__iter__'):
            for t in torr_id_l:
                torr_loc = self.my_tracker.download_torrent(t, self.torr_dir)
                if not torr_loc:
                    flag = 1
        else:
            torr_loc = self.my_tracker.download_torrent(torr_id_l, self.torr_dir)
            if not torr_loc:
                flag = 1
                
        if flag:
            return False
        else:
            return True
    
    def del_torrent(self, info_hash):
        """
        Given an info hash, delete a torrent locally
        """
        
    def load_state(self):
        """
        Load the saved cloud state
        """
        
    def save_state(self):
        """
        Save the session state upon closing the cloud
        """
