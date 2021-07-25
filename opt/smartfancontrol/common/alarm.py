# -*- coding: utf-8 -*-
#########################################################
# SERVICE : alarm.py                                    #
#           Handles smartfancontrol alarms              #
#                                                       #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################
from threading import Timer, Lock, Event
from common.alarms import alarms

#########################################################

####################### GLOBALS #########################

#########################################################

###################### FUNCTIONS ########################

#########################################################

#########################################################
# Class : alarm                                         #
#########################################################
class alarm(alarms):
    def __init__(self, delay = 5):
        self.alarms = []
        self.delay=delay
        self.timer = None
        self.timerBusy = Event()
        self.timerBusy.clear()
        self.timerQ = Event()
        self.timerQ.clear()
        self.mutex = Lock()
    
    def __del__(self):
        self.mutex.acquire()
        if self.timerBusy and self.timer:
            self.timer.cancel()
        self.mutex.release()
        del self.timerBusy
        del self.timerQ
        del self.mutex
        del self.timer
        del self.alarms
    
    def __str__(self):
        return self.printlast()
    
    def __repr__(self):
        return self.printlastshort()
    
    def set(self, alm):
        self.alarms.insert(0, alm)
    
    def get(self, alm):
        return self._posAlarm(alm) >= 0
    
    def reset(self, alm):
        posalm = self._posAlarm(alm)
        if posalm >= 0:
            self.alarms.pop(posalm)
            return True
        else:    
            return False
    
    def resetall(self):
        self.alarms.clear()
    
    def getall(self):
        return self.alarms
    
    def getprio(self):
        prio = 0
        prioalm = 0
        for alm in self.alarms:
            almprio = self.alarmdata[alm][0]
            if almprio > prio:
                prio = almprio
                prioalm = alm
        return prioalm
        
    def getlast(self):
        if len(self.alarms) > 0:
            return self.alarms[0]
        else:
            return 0
    
    def print(self, alm):
        return self.alarmdata[alm][2]
    
    def printshort(self, alm):
        return self.alarmdata[alm][1]
    
    def printall(self):
        prntall = ""
        first = True
        if len(self.alarms)>0:
            for alm in self.alarms:
                if not first:
                    prntall += "\n"
                prntall += self.alarmdata[alm][2]
                first = False
        else:
            prntall = self.print(0)
        return prntall
    
    def printprio(self):
        prio = self.getprio()
        return self.print(prio)
    
    def printlast(self):
        prnt = ""
        if len(self.alarms)>0:
            prnt = self.print(self.alarms[0])
        else:
            prnt = self.print(0)
        return prnt
    
    def printlastshort(self):
        prnt = ""
        if len(self.alarms)>0:
            prnt = self.printshort(self.alarms[0])
        else:
            prnt = self.printshort(0)
        return prnt
    
    def _posAlarm(self, alm):
        PosAlm = -1
        try:
            PosAlm = self.alarms.index(alm)
        except:
            pass
        return PosAlm
    
    def timerGet(self):
        self.mutex.acquire()
        if not self.timerBusy.isSet() and not self.timer:
            self.timer = Timer(self.delay, self._timercallback)
            self.timer.start()
            self.timerBusy.set()
            self.timerQ.clear()
        self.mutex.release()
        return self.timerQ.isSet()
    
    def timerClear(self):
        self.mutex.acquire()
        if self.timerBusy.isSet() and self.timer:
            self.timer.cancel()
            self.timer = None
        self.timerBusy.clear()
        self.timerQ.clear()
        self.mutex.release()
    
    def timerReset(self):
        if self.timerBusy.isSet():
            self.timerClear()
        
    def _timercallback(self):
        self.timerQ.set()

######################### MAIN ##########################
if __name__ == "__main__":
    pass
