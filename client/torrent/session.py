import libtorrent as lt
import glob
import os
import time
import logging
import anydbm
from torrentmetainfo import TorrentMetaInfo

# setup 'ma logging
log = logging.getLogger("cloud.session")

class Session(object):
    """
    Handle serving of torrents to peers.
    """
    
    # Default values for serving a torrent
    to_port_default = 40000
    from_port_default = 40010
    
    def __init__(self, session_dir, torr_db):
        self.session = None
        self.session_dir = session_dir
        self.torr_db = torr_db
        self.db = None                 # pointer to our torrent DB
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
        Create session.  Add torrent to session if it doesn't already exist.
        
        Parameters
        ti: TorrentMetaInfo object
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
                out += 'download %s/s (%s)' % (torr_status.download_rate, torr_status.total_download)
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
            for f in glob.glob(torr_dir + "/*." + str(ext)):
                log.debug("torr_dir: %s, f: %s" %(torr_dir, f))
                ti = TorrentMetaInfo(torr_dir, data_dir, tracker_ip, torr_file=os.path.basename(f))
                # ...and compare them against the list of info hashes we've been passed.
                for t in torr_hash_l:
                    if str(ti.info_hash) == str(t):
                        log.debug("Serving info hash: %s\n" % str(t))
                        self.serve(ti)
        # if we're given a single hash, just serve up that torrent
        else:
            for f in glob.glob(torr_dir + "/*." + str(ext)):
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
            
            
    def stor_torr(self, torr_name, info_hash):
        """
        Store torrents we're serving in the database.  If it's already in our database, just
        ignore it.  Pairs are stored as key => infohash, value=>torr_name
        
        Parameters
        torr_name: file name of torrent (string)
        info_ash: info hash of torrent (string)
        """
        self.db = anydbm.open(self.torr_db, 'c')
        if not self.db.has_key(info_hash):
            self.db[info_hash] = torr_name
        self.db.close()
        
    def showdb(self):
        """
        Enumerate all values in our db
        """
        self.db = anydbm.open(self.torr_db, 'c')
        for k, v in self.db.iteritems():
            print k, " ", v
        self.db.close()
        
    # incomplete
    def save_session(self):
        """
        Save a session's state
        """
        
        # loop through our handles and write out fast resume data
        for h in handles:
            if h.is_valid() and h.has_metadata():
                data = lt.bencode(h.write_resume_data())
                open(os.path.join(options.save_path, h.get_torrent_info().name() + '.fastresume'), 'wb').write(data)
        
        # save session settings here
    
    # incomplete
    def load_session(self):
        """
        Load a session from a saved state.
        """
        # resume out old settings here...
        
        
        
        # load up our torrents.  right now let's just look in our local directory.
        # eventually, we may want something else to determine what is being served...
        for f in glob.glob(torr_dir + "/*." + str(ext)):
            log.debug("torr_dir: %s, f: %s" %(torr_dir, f))
            ti = TorrentMetaInfo(torr_dir, data_dir, tracker_ip, torr_file=os.path.basename(f))
            self.serve(ti)
        
        pass
