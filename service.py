import win32service
import win32serviceutil
import win32event
import win32traceutil	
import win32evtlogutil
import servicemanager
import sys
import os
import time

import logging

class myservice(win32serviceutil.ServiceFramework):
    _svc_name_ = "aTestService"
    _svc_display_name_ = "A Test Python Service"
    _exe_name_ = sys.executable
    _exe_args_ = '"' + os.path.abspath(sys.argv[0]) + '"'

    def __init__(self, args):
        self.isAlive = True
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def event_log(self, msg):
        servicemanager.LogInfoMsg(str(msg))

    def SvcStop(self):
        # tell Service Manager we are trying to stop (required)
        self.event_log("stopping")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # set the event to call
        win32event.SetEvent(self.hWaitStop)

        self.event_log("Stopped")

    def SvcDoRun(self):
        import logging
    
        self.event_log("Starting %s" % self._svc_name_)
    
        ############ IF LOGGING IS COMMENTED OUT, THE ERROR GOES AWAY################
        win32event.WaitForSingleObject(self.hWaitStop,win32event.INFINITE)

if __name__ == '__main__':
    if len(sys.argv)==1:
        servicemanager.Initialize()
        #servicemanager.Initialize('backup service', None)

        servicemanager.PrepareToHostSingle(myservice)

        # Now ask the service manager to fire things up for us...
        servicemanager.StartServiceCtrlDispatcher()

    else:
        win32serviceutil.HandleCommandLine(myservice)