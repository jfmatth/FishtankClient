""" Tasker.py - A wrapper around the sched module to give us simple task scheduling
"""

import sched
import time

class Tasker(object):
        
    def __init__(self, stopfunc, stopdelay):
        if stopfunc==None or not hasattr(stopfunc, "__call__"):
            raise Exception("Must have a valid stop function")

        self.runtasks = sched.scheduler(time.time, time.sleep)  
        self._sigstop = stopfunc
        self._sigdelay = stopdelay
        self._stop = False

    def allStop(self):
        for x in self.runtasks.queue:
            self.runtasks.cancel(x)
   
    def checkStop(self):
        """
        will kill the queue and stop all jobs if the stop Signal is found.
        """
        if self._sigstop():
            self._stop = True
            
    def taskrun(self, thecall, delay):
        """
        this is what is called from the runtask scheduler to run the task at the time.  so it calls
        the thecall, and then reschedules itself to be run in delay time.
        """
        try:
            thecall()
            if self._stop:
                self.allStop()
            else:
                self.addtask(thecall, delay)
                
        except:
            self.allStop()

    def addtask(self, thecall, delay):
        """ 
        adds a task to the scheduler via the taskrun wrapper.
        """
        if delay > 0:
            self.runtasks.enter(delay, 1, self.taskrun, (thecall, delay) )

    def run(self):
        if len(self.runtasks.queue)== 0:
            return

        self._stop = False
        # ready to run, add our stop to the queue
        self.addtask(self.checkStop, self._sigdelay)
        self.runtasks.run()
        
        