""" agent.py - our backup agent to test the cloud from command line.
"""

from client.settingsmanager import settings
from client.logger import log
from client.torrent import cloud
from client.tasker import Tasker
from client.BackupCloud import BackupFromCloud, BackupToCloud
from client.utility import validate_settings

import os

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
    BackupToCloud(cloud=c, settings=settings, fast=True)

def BFC():
    log.info("BFC")
    BackupFromCloud(c, settings)

if __name__== "__main__":

    validate_settings(settings)  # raises exception if issue.

    c = cloud.Cloud(tracker_ip=settings["tracker_ip"],
                    torr_dir = settings["cloud_meta"],
                    data_dir = settings["cloud_files"],
                    session_dir = settings["cloud_meta"]
                    )

    # main schedule queue.
    log.info("Starting agent")
    
    s = Tasker(sigStop, 5)
    s.addtask(BTC, 10)
    s.addtask(BFC, 45)

    # start our cloud()
    log.info("Starting the cloud")
    c.start()
        
    log.debug("Starting the Tasks")

    s.run()
    
    log.debug("shutting down cloud")
    c.stop()
