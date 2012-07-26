import win32service
import win32serviceutil
import win32event
import servicemanager

import sys
import os


class BackupService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BackupService"
    _svc_display_name_ = "Backup Service for desktops"
    _svc_deps_ = ["EventLog"]


    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.isAlive = False
        self.pythonlog = None       # pointer to log

    def log(self, msg):
        servicemanager.LogInfoMsg(str(msg))

    def event_log(self, msg):
        servicemanager.LogInfoMsg(str(msg))

    def SvcStop(self):
        # tell Service Manager we are trying to stop (required)
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        self.log('Stoping service %s' % self._svc_name_)
        self.isAlive = False
        self.pythonlog.debug("isalive = %s" % self.isAlive)

        # set the event to call
        self.pythonlog.debug("setting hWaitStop")
        win32event.SetEvent(self.hWaitStop)
        self.pythonlog.debug("hWaitStop set")

    def SvcDoRun(self):
        # Write a 'started' event to the event log... (not required)
        #win32evtlogutil.ReportEvent(self._svc_name_,
        #    servicemanager.PYS_SERVICE_STARTED,
        #    0,
        #    servicemanager.EVENTLOG_INFORMATION_TYPE,
        #    (self._svc_name_, '')
        #)

        self.log("Starting %s" % self._svc_name_)
        self.isAlive = True

        # this is the start of our code for the agent client for Backup Service.
        # we had to put stuff here, since the curdir gets all screwed up when run normally, odd.

        from client.settingsmanager import settings
        from client.logger import log
        from client.torrent import cloud
        from client.tasker import Tasker
        from client.backupcloud import BackupFromCloud, BackupToCloud
        from client import utility 

        # try to put our logger on the class log variable
        self.pythonlog = log

        def sigStop():
            """
            Stop function for main scheuler loop
            """
            return not self.isAlive

        def BTC():
            BackupToCloud(cloud=c, settings=settings, stopfunc=sigStop)

        def BFC():
            BackupFromCloud(c, settings)

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
        
        c = cloud.Cloud(tracker_ip=settings["tracker_ip"],
                        torr_dir = td,
                        data_dir = dd,
                        session_dir = sd
                        )

        # main schedule queue.
        log.info("Starting agent")

        log.debug("Defining Tasker")
        s = Tasker(sigStop, int(settings["sigstop"] or 5) )  
        
        log.debug("adding BTC")
        s.addtask(BTC, int(settings["btctime"] or 0) )
        
        log.debug("adding BFC")
        s.addtask(BFC, int(settings["bfctime"] or 0) )

        # start our cloud()
        log.info("Starting the cloud")
        c.start()

        log.info("Starting the Tasks")
        log.debug("queue list : %s" % (s.runtasks.queue) )
        s.run()
        # when this returns, the tasker has been stopped, i.e. the service stopped.
        log.info("Tasks stopped")
        
        log.info("Stopping the cloud")
        c.stop()    # when this exists, then I guess we've stopped the service?
        log.info("cloud stopped")

        self.log("%s Stopped" % self._svc_name_)

if __name__ == '__main__':
    # determine how we run?
    if servicemanager.RunningAsService:
        # if we are a service, see if we are running bare, or with python as our caller?
        if "python.exe" in sys.executable.lower():
            BackupService._exe_name_ = sys.executable
            BackupService._exe_args_ = '"' + os.path.abspath(sys.argv[0]) + '"'
            BackupService._path = os.path.dirname(sys.argv[0])
        else:
            # otherwise, we could have been complied by pyinstaller.
            BackupService._exe_name_ = sys.executable
            BackupService._path = os.path.dirname(sys.executable)
    
    if len(sys.argv)==1:
        servicemanager.Initialize()

        servicemanager.PrepareToHostSingle(BackupService)

        # Now ask the service manager to fire things up for us...
        servicemanager.StartServiceCtrlDispatcher()

    else:
        win32serviceutil.HandleCommandLine(BackupService)    
    
    
    #win32serviceutil.HandleCommandLine(bService)