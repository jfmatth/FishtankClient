import os
import logging
import libtorrent as lt

# setup 'ma logging
log = logging.getLogger("cloud.torrentmetainfo")

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
        self.piece_size = 1048576                       # Default piece size.  Set this higher.
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
