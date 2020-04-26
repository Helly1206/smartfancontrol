# -*- coding: utf-8 -*-
#########################################################
# SERVICE : monitor.py                                  #
#           Monitor smartfancontrol in /var/run or      #
#           commandline                                 #
#                                                       #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################
from threading import Thread, Event
import os
#########################################################

####################### GLOBALS #########################
UPDATEFREQ = 1
RUNFILE = "/run/smartfancontrol"
#########################################################

###################### FUNCTIONS ########################

#########################################################

#########################################################
# Class : monitor                                       #
#########################################################
class monitor(Thread):
    def __init__(self, fanctrl, temp, mutex, alarm, logger, exitevent, monstatus):
        self.fanctrl = fanctrl
        self.temp = temp
        self.alarm = alarm
        self.logger = logger
        self.exitevent = exitevent
        self.runthread = Event()
        self.runthread.clear()
        self.mutex = mutex
        self.monstatus = monstatus
        self.monok = self.monCheck()
        Thread.__init__(self)
        Thread.start(self)
    
    def __del__(self):
        pass
    
    def start(self):
        self.runthread.set()
        
    def stop(self):
        self.runthread.clear()
    
    def exit(self):
        self.exitevent.set()
        
    def run(self):
        try:
            while not self.exitevent.is_set():
                if self.runthread.is_set():
                    self.mutex.acquire()
                    self.monTerm()
                    self.monRun()
                    self.mutex.release()
                    self.exitevent.wait(UPDATEFREQ)
                else:
                    self.exitevent.wait(UPDATEFREQ)
        except Exception as e:
            self.logger.exception(e)
    
    #current temp, fan on/off/PWM/RPM, alarm
    def monTerm(self):
        if self.monstatus:
            print("Temp: {}, Fan: {}, Alarm: {!r}".format(self.temp, self.fanctrl, self.alarm))
    
    def monCheck(self):
        return os.access(os.path.dirname(RUNFILE), os.W_OK)
      
    def monRun(self):
        if self.monok:
            filestr = "{!r}, {!r}, {!r}\n".format(self.temp, self.fanctrl, self.alarm)
            with open(RUNFILE, 'w') as monfile:
                monfile.write(filestr)

######################### MAIN ##########################
if __name__ == "__main__":
    pass
