from client.libtorrent import libtorrent as lt
from client.settingsmanager import settings
import glob
import os
import time
import logging
import anydbm
import sys
import random
from torrentmetainfo import TorrentMetaInfo
#from settingsmanager import *

# setup 'ma logging
#log = logging.getLogger("cloud.session")

from client.logger import log

class Session(object):
    """
    Handle serving of torrents to peers.
    """
    
    def __init__(self, 
                 session_dir, 
                 db_name,
                 ):
        self.session = None
        self.session_dir = session_dir
        self.torr_db = os.path.join(session_dir, db_name)
        self.db = None                 # pointer to our torrent DB
        self.handles = []
        self.alerts = []
        self.max_upload = 0
        self.max_download = 0
        
        # Randomly generated before serving
        self.to_port = -1
        self.from_port = -1
    
    def register(self, callback):
        """
        Register our callback function.
        """
        if hasattr(callback, '__call__'):
            self.callback = callback
        else:
            raise Exception("Object %s not callable." % str(callback))
        
    def _check_callback(self):
        """
        A callback is required for this class.  It must be registered before a session
        can be started.  This performs a simple check.
        """
        # need to call register() first
        if not self.callback:
            raise Exception("Callback not specified.")
        
    def configure_rates(self, rate="med"):
        """
        Set our max upload and download rates.
        """
        
        if rate == "high":
            self.max_download = 2**30
            self.max_upload = 2**30
        elif rate == "med":
            self.max_download = 2**20
            self.max_upload = 2**20
        elif rate == "low":
            self.max_download = 2** 15
            self.max_upload = 2 ** 15
        else:
            # Unlimited is the default!
            self.max_download = 0
            self.max_upload = 0
        
        # if the session already exists, just change it on the fly...
        if self.session:
            log.debug("Setting upload and download rates...")
            self.session.set_upload_rate_limit(self.max_upload)
            self.session.set_download_rate_limit(self.max_download)
            
    def show_rates(self):
        """
        Show our global upload and download rates.
        """
        if self.session:
            log.info("Upload Rate Limit: %d" % self.session.upload_rate_limit())
            log.info("Download Rate Limit: %d" % self.session.download_rate_limit())
            log.info("Upload Rate Limit (Local): %d" % self.session.local_upload_rate_limit())
            log.info("Download Rate Limit (Local): %d" % self.session.local_download_rate_limit())
        
    def _set_max_download(self, max_download):
        self.max_download = max_download
        
    def _set_max_upload(self, max_upload):
        self.max_upload = max_upload
        
        
    def add_suffix(self, val):
        prefix = ['B', 'kB', 'MB', 'GB', 'TB']
        for i in range(len(prefix)):
            if abs(val) < 1000:
                if i == 0:
                    return '%5.3g%s' % (val, prefix[i])
                else:
                    return '%4.3g%s' % (val, prefix[i])
            val /= 1000
    
        return '%6.3gPB' % val

        
    def _configure_session(self):
        """
        This starts our session using any parameters that we've set -- ports, upload/download
        rates, etc.
        """
        self.session = lt.session()
        peerid = settings["_peerid"]
        self.session.set_peer_id(lt.big_number(peerid))
        
        # Grab a random port, and take 10 in sequence.
        self.from_port = random.randint(35000,55000)
        self.to_port = self.from_port + 10
        self.session.listen_on(self.to_port, self.from_port)
        
        self.session.set_upload_rate_limit(self.max_upload)
        self.session.set_download_rate_limit(self.max_download)
        self._configure_session_settings()
        
        log.debug("Serving on ports %s-%s" % (self.from_port, self.to_port))
        
    def _configure_session_settings(self):
        """
        Configure session settings.  More can be added later...
        """
        s_settings = self.session.settings()
        s_settings.ignore_limits_on_local_network = False
        self.session.set_settings(s_settings)
        

    def serve(self, ti):
        """
        Create session.  Add torrent to session if it doesn't already exist.
        
        Parameters
        ti: TorrentMetaInfo object
        """
        
        log.info("Serving torrent %s from %s" % (ti.file_path, ti.torr_path))

        self._check_callback()
        
        if not ti.is_valid_torr():
            log.debug("No torrent specified in TorrentMetaInfo")
            return False
        
        # start the session if it hasn't been already
        if not self.session:
            log.debug("No session exists, starting...")
            self._configure_session()
            
        # check if we're serving this torrent, and if not, add it to the session
        th = self.session.find_torrent(ti.info_hash)
        if not th.is_valid():
            log.debug("Adding Torrent to session")
            
            td = {}
            ti.info = lt.torrent_info(ti.torr_name)
            try:
                #td["resume_data"] = open(ti.torr_path + "/" + ti.info.name() + '.fastresume', 'rb').read()
                td["resume_data"] = open(self.session_dir + "/" + ti.info.name() + '.fastresume', 'rb').read()
                log.debug("Torrent resume data found... loading")
            except:
                pass
            td["ti"] = ti.info
            td["save_path"] = ti.get_fpath()
            td["auto_managed"] = False
            td["duplicate_is_error"] = True
            td["paused"] = False
            
            handle = self.session.add_torrent(td)
            
            # torrent states
            states = ['queued', 'checking','download metadata', 'download', 'finished', 'seeding', 'allocating', 'checking fastresume']
            
            # wait for seeding to complete before returning.  Check callback at each pass.
            log.debug("Seeding torrent.")
            while True:
                if not self.callback():
                    return False
                
                torr_status = handle.status()
                out = '%s ' % handle.get_torrent_info().name()[:40] + ' '
                out += '%s ' % states[torr_status.state] + ' '
                out += '%2.0f%% ' % (torr_status.progress * 100) + ' '
                out += 'download %s/s (%s)' % (self.add_suffix(torr_status.download_rate), 
                                               self.add_suffix(torr_status.total_download))
                log.debug(out)
                time.sleep(1)
                
                
                if handle.is_seed():
                    # append to handles if we seed the torrent
                    self.handles.append(handle)
                    
                    # We're seeding the torrent, so start tracking nit.
                    info_hash = str(handle.info_hash())
                    file_name = str(handle.name())
                    self.stor_torr(info_hash, file_name)
                    
                    return True
            
        else:
            log.debug("Torrent exists in session.")
            return True
    
    def unserve_all(self):
        """
        Stop serving a torrent by info hash, or by TI.  Prefer info_hash over TI.
        """
        
        log.debug("Unserving all torrent.")  
        
        # apparently we can remove from a list we're iterating over if it's reversed?...
        for handle in reversed(self.handles):
            try:
                self.session.remove_torrent(handle)
            except RuntimeError:
                log.warning("Attempted to remove non-existent torrent from session.")
            else:
                log.debug("Torrent removed from session!")    
            
            self.handles.remove(handle)

        
    def unserve(self, info_hash=None, ti=None):
        """
        Stop serving a torrent by info hash, or by TI.  Prefer info_hash over TI.
        """
        
        log.debug("Unserve torrent.")
        
        if info_hash:
            ih = info_hash
        elif ti: 
            ih = str(ti.info_hash)
        else:
            log.debug("Cannot unserve a torrent without a valid hash or TorrentMetaInfo object.")
            return False
        
        for handle in self.handles:
            if info_hash == str(handle.info_hash):
                self.session.remove_torrent(handle) # unserve
                self.handles.remove(handle)         # remove from our list of handles
                return True
                
        return False
    
    def serving(self):
        """
        Return a list of tuples with the info hash and name of all torrents being
        served.
        """
        vals = []
        for h in self.handles:
            vals.append( (h.name(), str(h.info_hash())) )
        
        return vals
            

    def serve_torrent_by_hash(self, torr_hash_l, torr_dir, data_dir, tracker_ip, ext):
        """
        Serve up a torrent, given its info hash or a list of info hashes
        torr_hash_l: Single torrent hash (string), or a list of torrent hashes.
        torr_dir: Directory where torrents are kept. (string)
        data_dir: Directory where torrent data is stored. (string)
        tracker_ip: tracker IP and port in the format <ip:port> (string)
        ext: file extensions to look for (string, default: "torrent")
        """
        
        flag = 0
        
        # if we're given a list, serve up all torrents that exist in our torrent directory
        if hasattr(torr_hash_l, '__iter__'):
            # loop through all torrents files...
            for f in glob.glob(torr_dir + "/*" + str(ext)):
                log.debug("torr_dir: %s, f: %s" %(torr_dir, f))
                ti = TorrentMetaInfo(torr_dir, data_dir, tracker_ip, torr_file=os.path.basename(f))
                # ...and compare them against the list of info hashes we've been passed.
                for t in torr_hash_l:
                    if str(ti.info_hash) == str(t):
                        log.debug("Serving info hash: %s\n" % str(t))
                        self.serve(ti)
        # if we're given a single hash, just serve up that torrent
        else:
            for f in glob.glob(torr_dir + "/*" + str(ext)):
                log.debug("torr_dir: %s, f: %s" %(torr_dir, f))
                ti = TorrentMetaInfo(torr_dir, data_dir, tracker_ip, torr_file=os.path.basename(f))
                if str(ti.info_hash) == str(torr_hash_l):
                    log.debug("Serving info hash: %s\n" % str(torr_hash_l))
                    self.serve(ti)
        
        
            
    def serve_all_torrents(self, torr_dir, data_dir, tracker_ip, ext):
        """
        Look in our torrent directory and attempt to serve all torrents that exist there.
        """

        for f in glob.glob(torr_dir + "/*." + str(ext)):
            log.debug("torr_dir: %s, f: %s" %(torr_dir, f))
            ti = TorrentMetaInfo(torr_dir, data_dir, tracker_ip, torr_file=os.path.basename(f))
            self.serve(ti)
            
            
    #
    # Database functions
    #        
    
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
        
    def pause(self):
        """Check if the session object exists, and pause it if so. """
        if self.session:
            self.session.pause()
            return True
        else:
            return False
        
    def save_session(self):
        """
        Save a session's state into fast resume data
        """
        
        # pause the session
        self.pause()
        
        # loop through our handles and write out fast resume data
        for h in self.handles:
            if h.is_valid() and h.has_metadata():
                data = lt.bencode(h.write_resume_data())
                open(os.path.join(self.session_dir, h.get_torrent_info().name() + '.fastresume'), 'wb').write(data)
        
        # save session settings here
    
    # incomplete
    def load_session(self, torr_dir, data_dir, tracker_ip, ext):
        """
        Load a session from a saved state.
        """
        # resume out old settings here...
        try:
            self.db = anydbm.open(self.torr_db, 'c')
        except:
            return False
        
        for info_hash, filename in self.db.iteritems():
            log.debug("Loading... %s %s..." % (info_hash, filename,))
            print os.path.join(torr_dir, filename+ext)
            ti = TorrentMetaInfo(torr_dir, data_dir, tracker_ip, filename, str(filename+ext))
            
            log.debug("Is valid?: %s" % ti.is_valid_torr())
            
            log.debug("info_hash1: %s" % info_hash)
            log.debug("info_hash2: %s" % str(ti.info_hash))
            
            if not ti.is_valid_torr():
                log.debug("Torrent invalid: %s, %s." % (info_hash, filename, ))
                self.unstor_torr(info_hash)
            else:
                self.serve(ti)
                
        self.db.close()
        return True