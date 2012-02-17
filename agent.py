""" agent.py - our backup agent 
"""

from client.settingsmanager import settings
from client.logger import log
from client.torrent import cloud
from client.tasker import Tasker
from backuptest import BackupFromCloud, BackupToCloud

import os


c = cloud.Cloud(tracker_ip=settings["tracker_ip"],
                torr_dir = settings["cloud_meta"],
                data_dir = settings["cloud_files"],
                session_dir = settings["cloud_meta"]
                )

def sigStop():
    """
    returns True if a stop signal was found, in this case, a file in the temp directory for now.
    """
    log.info("Should I stop?")
    if os.path.exists("C:/temp/stop.txt"):
        os.remove("C:/temp/stop.txt")
        log.info("stopping")
        return True
    else:
        return False

def BTC():
    log.info("BTC")
    BackupToCloud(c, settings)

def BFC():
    log.info("BFC")
    BackupFromCloud(c, settings)

if __name__== "__main__":
    # main schedule queue.
    log.info("Starting agent")
    
    #load our execution queue.
#    Tasks.enter(0,1, checkStop, ())
#    Tasks.enter(10, 1, BTC, () )
#    Tasks.enter(20, 1, BFC, () )
    
    s = Tasker(sigStop, 10)
    s.addtask(BTC, 60)
    s.addtask(BFC, 45)
    
    # start our cloud()
    log.info("Starting the cloud")
    c.start()
        
    log.debug("Starting the Tasks")


#    Tasks.run()
    s.run()
    
    log.debug("shutting down cloud")
    c.stop()
    
    