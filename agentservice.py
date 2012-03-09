import win32service
import win32serviceutil
import win32event
import win32evtlogutil
import win32traceutil
import servicemanager
import sys
import os

class bService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BackupService"
    _svc_display_name_ = "Backup Service for desktops"
    _svc_deps_ = ["EventLog"]

    isAlive = True

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def log(self, msg):
        servicemanager.LogInfoMsg(str(msg))

    def SvcStop(self):
        # tell Service Manager we are trying to stop (required)
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # set the event to call
        win32event.SetEvent(self.hWaitStop)

        self.log('Stoping service %s' % self._svc_name_)
        self.isAlive = False

    def SvcDoRun(self):
        # Write a 'started' event to the event log... (not required)
        win32evtlogutil.ReportEvent(self._svc_name_,
            servicemanager.PYS_SERVICE_STARTED,
            0,
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            (self._svc_name_, '')
        )

        self.log("Starting %s" % self._svc_name_)
        self.isAlive = True

        # this is the start of our code for the agent client for Backup Service.
        # we had to put stuff here, since the curdir gets all screwed up when run normally, odd.

        # start us up in the right directory.
        os.chdir(os.path.dirname(__file__))

        from client.settingsmanager import settings
        from client.logger import log
        from client.torrent import cloud
        from client.tasker import Tasker
        from backuptest import BackupFromCloud, BackupToCloud

        def BTC():
            log.info("BTC")
            BackupToCloud(c, settings)

        def BFC():
            log.info("BFC")
            BackupFromCloud(c, settings)

        def sigStop():
            """
            Stop function for main scheuler loop
            """
            return not self.isAlive

        c = cloud.Cloud(tracker_ip=settings["tracker_ip"],
                        torr_dir = settings["cloud_meta"],
                        data_dir = settings["cloud_files"],
                        session_dir = settings["cloud_meta"]
                        )

        # main schedule queue.
        log.info("Starting agent")

        s = Tasker(sigStop, 1)  # we should check ourselves every second?

        s.addtask(BTC, 60)
        s.addtask(BFC, 45)

        # start our cloud()
        log.info("Starting the cloud")
        c.start()

        log.debug("Starting the Tasks")
        s.run()

        log.debug("Stopping the cloud")
        c.stop()    # when this exists, then I guess we've stopped the service?
        log.debug("cloud stopped")

        win32event.WaitForSingleObject(self.hWaitStop,win32event.INFINITE)

        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        return

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(bService)