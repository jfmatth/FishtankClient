""" agent.py - our backup agent to test the cloud from command line.
"""

from client.settingsmanager import settings
from client.logger import log
from client.torrent import cloud
from client.tasker import Tasker
from client import utility
from client.backupcloud import BackupFromCloud, BackupToCloud
from client import restore

import os

def sigStop():
    """
    returns True if a stop signal was found, in this case, a file in the temp directory for now.
    """
    if os.path.exists("C:/temp/stop.txt"):
        log.debug("stopping")
        return True
    else:
        return False

def BTC():
    BackupToCloud(cloud=c, settings=settings, stopfunc=sigStop)

def BFC():
    BackupFromCloud(cloud=c, settings=settings)

if __name__== "__main__":
    log.info("Starting agent")
    
    if os.path.exists("C:/temp/stop.txt"):
        os.remove("C:/temp/stop.txt")

    insdir = settings['.installdir']
    td = os.path.normpath(insdir + settings['cloud_meta'] )
    utility.check_dir(td)
    dd = os.path.normpath(insdir + settings['cloud_files'] )
    utility.check_dir(dd) 
    sd = os.path.normpath(insdir + settings['cloud_meta'] )
    
    # erase all files in our temp directory on startup.
    log.debug("Emptying the temp directory")
    tempdir = os.path.normpath(insdir + settings['temppath'] )
    utility.EmptyADir(tempdir)
    
    log.debug('td = %s' % td)
    log.debug('dd = %s' % dd)
    log.debug('sd = %s' % sd)
    
    c = cloud.Cloud(tracker_ip=settings["tracker_ip"],
                    torr_dir = td, 
                    data_dir = dd,
                    session_dir = sd,
                    )

    # moving to objects for scheduled things.
    r = restore.Restore(cloud=c, settings=settings)

    # main schedule queue.
    s = Tasker(sigStop, int(settings["sigstop"] or 5) )

    log.debug("adding BTC")
    s.addtask(BTC,int(settings["btctime"] or 0) ) 

    log.debug("adding BFC")
    s.addtask(BFC, int(settings["bfctime"] or 0) )

    log.debug("Adding RFC")
    s.addtask(r.check, int(settings["rfctime"] or 0) )

    # start our cloud()
    log.debug("Starting the cloud")
    c.start()

    log.debug("Starting the Tasks")
    log.debug("queue list : %s" % (s.runtasks.queue) )

    try:
        s.run()
    except:
        log.exception("Error from Tasker")
    
    log.debug("shutting down cloud")
    c.stop()
