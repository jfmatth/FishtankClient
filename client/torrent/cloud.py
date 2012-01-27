"""
torrent classes for tbackup

add to python path for libtorrent: 
set PYTHONPATH=C:\TorrentBackup\misc\clients\tbackup\bin\python\Lib\site-packages
set PYTHONPATH=C:\FishtankClient\client\libtorrent
set PYTHONPATH=Y:\client\libtorrent

# Cloud Example
import cloud
c = cloud.Cloud('c:/torrent', 'c:/torrent/files', '10.0.0.1:8000')
c.put("AcrobatPro_10_Web_WWEFD.zip")

# Download torrent(s)
import cloud
c = Cloud("c:/torrentdir", "c:/filesdir", "10.0.0.1:8000")
c.get("0b36cb9ed4ce43c50f9df4a9f9790818cadaddb2")


# OTHER NOTES
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

# LIBTORRENT NOTES
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
#import logging # replaced with logger import below
from client.logger import log
from tracker import Tracker
from torrentmetainfo import TorrentMetaInfo
from session import Session
from createtorrent import CreateTorrent
from client.settingsmanager import settings
import anydbm

# setup 'ma logging
#DEBUG_LVL = logging.DEBUG

#logging.basicConfig(level=DEBUG_LVL)
#h = logging.StreamHandler()
#f = logging.Formatter("%(levelname)s %(funcName)s %(lineno)d")
#h.setFormatter(f)

#log = logging.getLogger("cloud.py")
#log.addHandler(h)
#log.setLevel(DEBUG_LVL)



class Cloud(object):
    """
    Put or get a file from the Cloud.  This class maintains the session, which includes all files that we're serving up to other clients.
    
    This class is reponsible for "put"-ting and "get"-ting files to and from the cloud.
    """
    
    def __init__(self, 
                 torr_dir="c:/torrent", 
                 data_dir="c:/torrent/files", 
                 tracker_ip="10.0.0.1:8000", 
                 callback=lambda: ".", 
                 session_dir="c:/torrent", 
                 db_name="torrent.db", 
                 ext=".torrent",
                 rate=None):
        """
        Initialize class.
        
        Parameters
        torr_dir: Location for torrent meta data files
        data_dir: Location for data files
        tracker_ip: IP:PORT string of tracker
        callback: option function which will be called while attempting to seed torrents.
        torr_db: Name of anydbm database where we save what we're serving.
        rate: low | med | high | unlimited
        """        
        
        self.callback = callback
        self.data_dir = data_dir
        self.torr_dir = torr_dir
        self.ext = ext
        
        self.torr_db = os.path.join(session_dir, db_name)
        self.db = None                 # pointer to our torrent DB
        
        # setup our tracker
        self.my_tracker = Tracker(tracker_ip)
        
        # setup our session
        self.session = Session(session_dir, db_name)
        self.session.register(self.callback)
        self.session.configure_rates(rate)
            
    def put(self, backup_file):
        """
        Put files to the tracker, given an encrypted ZIP archive, and then serve them.
        
        Parameters
        backup_file: Takes either a full path, or the basename (assumes a directory of self.data_dir in the latter case)
        """
        
        log.debug("backup_file = %s, data_dir = %s, torr_dir = %s, tracker = %s" % (backup_file, self.data_dir, self.torr_dir, self.my_tracker.tracker_ip))        
        
        # setup our TorrentMetaInfo object and create a torrent
        ti = TorrentMetaInfo(self.torr_dir, 
                             self.data_dir, 
                             self.my_tracker.tracker_ip, 
                             os.path.basename(backup_file),
                             )
        
        # Make the torrent file and save new TorrentMetaInfo object with torrent name
        if ti.is_valid_create_object():        
            t=CreateTorrent(ti)
            ti = t.create(self.my_tracker)
        else:
            raise Exception("TorrentMetaInfo object is not valid for CreateTorrent.")
        
        # Upload torrent to tracker.  Return false if the upload fails.
        if not self.my_tracker.upload_torrent(ti):
            log.debug("Failed to upload torrent to tracker.")
            return False

        # Serve the torrent
        return self.session.serve(ti)
    
    def get(self, torr_hash_l):
        """
        Pass a torrent info hash, download files for torrent.
        
        Parameters
        torr_hash_l: Either a string or a list.  Right now, it only takes a single info hash of the torrent to pull down from the tracker.  The
                        data files associated with the torrent are then downloaded from the cloud.
        """
                
        if self._get_torrents(torr_hash_l):
            self._get_files(torr_hash_l)
            return True
        else:
            return False
            
    def _get_files(self, torr_hash_l):
        """
        Download our files, given a torrent's info hash (string) or a list of torrent info hashes (strings).  Used by the get() function to pull down data
        files from the cloud.
        
        Parameters
        torr_hash_l: string, or list of strings 
        """
        self.session.serve_torrent_by_hash(torr_hash_l, 
                                           self.torr_dir, 
                                           self.data_dir, 
                                           self.my_tracker.tracker_ip, 
                                           self.ext)
    
    # deprecated?
    def serve_torrents(self):
        """
        Serve up all torrents in our torr directory.  Does not take any parameters, simply checks for all torrents
        in our torrent meta data directory, and serves them.
        """
        self.session.serve_all_torrents(self.torr_dir, 
                                        self.data_dir, 
                                        self.my_tracker.tracker_ip, 
                                        self.ext)
               
    def _get_torrents(self, torr_hash_l):
        """
        Pull a torrent down from the tracker by ID.
        
        Parameter 
        torr_hash_l: list or string of info hashes of torrents to download from the tracker.
        """
        
        flag = 0
        
        if hasattr(torr_hash_l, '__iter__'):
            for t in torr_hash_l:
                torr_loc = self.my_tracker.download_torrent(t, self.torr_dir)
                if not torr_loc:
                    log.debug("Multiple Torr ID's: unable to get torrent location.")
                    flag = 1
        else:
            torr_loc = self.my_tracker.download_torrent(torr_hash_l, self.torr_dir)
            if not torr_loc:
                log.debug("Single ID: unable to get torrent location.")
                flag = 1
                
        if flag:
            return False
        else:
            return True
    
    # deprecated?
    def get_files_by_torr_name(self, torr_name_l):
        """
        Download files given a torrent file name.  This function will likely be going away as it's not part of our workflow at the moment.
        
        Parameters
        torr_name_l: string or list of torrent info hashes
        """
        # setup our TorrentMetaInfo object and create a torrent
        
        if hasattr(torr_name_l, '__iter__'):
            for t in torr_name_l:  
                ti = TorrentMetaInfo(self.torr_dir, self.data_dir, self.my_tracker.tracker_ip, torr_file=t)
                self.session.serve(ti)
        else:
            ti = TorrentMetaInfo(self.torr_dir, self.data_dir, self.my_tracker.tracker_ip, torr_file=torr_name_l)
            self.session.serve(ti)
    
    def del_torrent(self, ih):
        """
        Given an info hash, delete a torrent locally
        """
        
        try:
            self.db = anydbm.open(self.torr_db, 'c')
        except:
            return False
        
        for info_hash, filename in self.db.iteritems():
            if info_hash == ih:
                self.unstor_torr(ih)
                if self.session.unserve(info_hash=ih):
                    log.debug("Torrent unserved.")
                else:
                    log.debug("Failed to unserve torrent.")
                return True    
                
        self.db.close()
        return False
    
    ###########################################
    # Start/Stop Cloud
    ###########################################    
        
    # incomplete
    def stop(self):
        """
        Save a session's state
        """
        
        # loop through our handles and write out fast resume data
        for h in handles:
            if h.is_valid() and h.has_metadata():
                data = lt.bencode(h.write_resume_data())
                open(os.path.join(options.save_path, h.get_torrent_info().name() + '.fastresume'), 'wb').write(data)
        
        # save session settings here
    
    def start(self):
        """
        Start the cloud from a saved state
        """
        
        if self.serving():
            log.debug("Cloud already started.")
            return False
        
        # Open our database, and grind through it.
        try:
            self.db = anydbm.open(self.torr_db, 'c')
        except:
            return False
        
        flag = 0
        
        for info_hash, filename in self.db.iteritems():
            log.debug("Loading... %s %s..." % (info_hash, filename,))
            print os.path.join(self.torr_dir, filename+self.ext)
            ti = TorrentMetaInfo(self.torr_dir, self.data_dir, self.my_tracker.tracker_ip, filename, str(filename+self.ext))
            
            # if we have it, and the tracker has it, serve it
            if not ti.is_valid_torr():
                log.debug("Torrent invalid: %s, %s." % (info_hash, filename, ))
                self.unstor_torr(info_hash)
            elif not self.my_tracker.has_torrent(ti):
                log.debug("Torrent does not exist on tracker: %s, %s." % (str(ti.info_hash), filename, ))
                self.unstor_torr(info_hash)
            else:
                self.session.serve(ti)
                flag = 1                # serve at least one torrent...
                
        self.db.close()
        if flag:
            return True
        else:
            log.debug("Nothing in the database to serve.")
            return False
    
    def is_serving(self):
        """
        Tells us if the cloud is serving any files.
        """
        if len(self.session.handles) > 0:
            return True
        else:
            return False
        
    def serving(self):
        """
        return a list of torrents we're currently serving
        """
        pass
    
    
    ###########################################
    # Database functions
    ###########################################        
    
    def stor_torr(self, info_hash, torr_name):
        """
        Store torrents we're serving in the database.  If it's already in our database, just
        ignore it.  Pairs are stored as key => infohash, value=>torr_name
        
        Parameters
        torr_name: file name of torrent (string)
        info_hash: info hash of torrent (string)
        """
        self.db = anydbm.open(self.torr_db, 'c')
        if not self.db.has_key(info_hash):
            self.db[info_hash] = torr_name
            log.debug("info_hash %s, torr_name: %s" % (info_hash, torr_name,))
        self.db.close()
        
    def unstor_torr(self, info_hash):
        """
        Delete a torrent from our database.
        
        Parameters
        info_hash: info hash of torrent to delete
        
        Returns
        True if deleted.
        False if not deleted, or failure.
        """
        try:
            self.db = anydbm.open(self.torr_db, 'w')
        except:
            log.debug("Failed opening database for key removal.")
            return False
        else:
            try:
                del self.db[info_hash]
            except:
                log.debug("Failed removing key.")
                return False
            else:
                return True

    def show_db(self):
        """
        Enumerate all values in our db
        """
        self.db = anydbm.open(self.torr_db, 'c')
        for info_hash, filename in self.db.iteritems():
            print info_hash, " ", filename
        self.db.close()
        