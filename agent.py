""" agent.py - our backup agent to test the cloud from command line.
"""

from client.settingsmanager import settings
from client.logger import log
from client.torrent import cloud
from client.tasker import Tasker
from client.backupcloud import BackupFromCloud, BackupToCloud
from client.utility import validate_settings

import os

def sigStop():
    """
    returns True if a stop signal was found, in this case, a file in the temp directory for now.
    """
    log.debug("Should I stop?")
    if os.path.exists("C:/temp/stop.txt"):
        os.remove("C:/temp/stop.txt")
        log.info("stopping")
        return True
    else:
        return False

def BTC():
    BackupToCloud(cloud=c, settings=settings, fast=True)

def BFC():
    BackupFromCloud(cloud=c, settings=settings)

if __name__== "__main__":
    log.info("Starting agent")

    insdir = settings['.installdir']
    td = os.path.normpath(insdir + settings['cloud_meta'] )
    dd = os.path.normpath(insdir + settings['cloud_files'] ) 
    sd = os.path.normpath(insdir + settings['cloud_meta'] )
    
    log.info('td = %s' % td)
    log.info('dd = %s' % dd)
    log.info('sd = %s' % sd)
    
    c = cloud.Cloud(tracker_ip=settings["tracker_ip"],
                    torr_dir = td, 
                    data_dir = dd,
                    session_dir = sd,
                    )

    # main schedule queue.
    s = Tasker(sigStop, 5)
    s.addtask(BFC, 15)
    s.addtask(BTC, 160)
    

    # start our cloud()
    log.info("Starting the cloud")
    c.start()
        
    log.debug("Starting the Tasks")
    s.run()
    
    log.debug("shutting down cloud")
    c.stop()
