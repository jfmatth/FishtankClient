from client.libtorrent import libtorrent as lt
import logging
import os
from torrentmetainfo import TorrentMetaInfo

# setup 'ma logging
#log = logging.getLogger("cloud.createtorrent")

from client.logger import log

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
        Create a Torrent, given a TorrentMetaInfo Object.
        
        Parameter
        ti:  A TorrentMetaInfo object.
        """
        
        # Initialize our only variable -- A TorrentMetaInfo object.
        self.ti = ti

    def create(self, tracker_ip):
        """
        Description: Creates a new torrent.
        
        tracker_ip: The tracker IP:PORT string to use when creating the torrent.  Should match whatever tracker we're using for the cloud, obviously! :)
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
        Helper function which names a torrent based on the name of the backup_file which has been passed.
        
        Parameters 
        backup_file: A string containing the name of the backup file.
        
        Returns
        A string containing the basename for the new torrent.
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
    
    
    #  Eliminate?  This appears to refer to something that no longer exists in this class.
    def is_seed(self):
        """
        Just tell us if we're seeding the torrent in the session.
        """
        if self.torr_session:
            return self.torr_session.is_seed()
        else:
            return False
