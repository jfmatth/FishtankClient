""" agent.py - our backup agent 
"""

from client.settingsmanager import settings
from client.logger import log
from client.torrent import cloud

from backuptest import BackupFromCloud, BackupToCloud

import sched
import time
import os

# our psuedo scheduler.
Tasks = sched.scheduler(time.time, time.sleep)
c = cloud.Cloud(tracker_ip=settings["tracker_ip"],
                torr_dir = settings["cloud_meta"],
                data_dir = settings["cloud_files"],
                session_dir = settings["cloud_meta"]
                )

def sigStop():
    """ returns True if a stop signal was found, in this case, a file in the temp directory for now.
    """
    if os.path.exists("C:/temp/stop.txt"):
        os.remove("C:/temp/stop.txt")
        return True
    else:
        return False
    

def allStop():
    log.info("Stopping, killing all tasks in queue.")
    for x in Tasks.queue:
        Tasks.cancel(x)

def checkStop():
    """
    will kill the queue and stop all jobs if the stop Signal is found.
    """
    log.info("Checking stop")
    if sigStop():
        allStop()
    else:
        # put ourselves back on the queue
        Tasks.enter(5,1,checkStop, ()   )


def BTC():
    log.info("BTC")
    try:
        BackupToCloud(c, settings)
        Tasks.enter(180, 1, BTC, () )
    except:
        log.exception("something failed backing up")
        allStop()

def BFC():
    log.info("BFC")
    try:
        BackupFromCloud(c, settings)
        Tasks.enter(60,1, BFC, () )
    except:
        log.exception("something failed in BFC")
        allStop()


if __name__== "__main__":
    # main schedule queue.
    log.info("Starting agent")
    
    #load our execution queue.
    Tasks.enter(0,1, checkStop, ())
    Tasks.enter(10, 1, BTC, () )
    Tasks.enter(20, 1, BFC, () )
    
    # start our cloud()
    log.info("Starting the cloud")
    c.start()
        
    log.debug("Starting the Tasks")
    Tasks.run()
    
    log.debug("shutting down cloud")
    c.stop()
    
    