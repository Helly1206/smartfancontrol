# -*- coding: utf-8 -*-
#########################################################
# SERVICE : calibrate.py                                #
#           Calibrates fan by measuring maximum RPM     #
#           or minimum PWM to start running             #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################
from common.common import common
from common.stdin import stdin
from datetime import datetime, timedelta
from threading import Timer
from time import sleep
#########################################################

####################### GLOBALS #########################
AUTOCALSETUPTIME = 5 # seconds
DEFAULTMANUALSTARTPERC = 30
MANUALPWMDELTA = 5
MAXPWM = 100
MINPWM = 0
DEFRECAL = 7
#########################################################

###################### FUNCTIONS ########################

#########################################################

#########################################################
# Class : calibrate                                     #
#########################################################
class calibrate(common):
    def __init__(self, rpm, fanoutput, mutex, settings, logger, exitevent, autocal = True):
        self.fanoutput = fanoutput
        self.rpm = rpm
        self.mutex = mutex
        self.logger = logger
        self.exitevent = exitevent
        common.__init__(self, self.logger)
        mode = self.checkkey(settings, 'fan', 'mode')
        if mode:
            self.auto = mode.lower() == 'rpm' and autocal
        else:
            self.auto = autocal
        self.recalibrate =  self.checkkeydef(settings, 'fan', 'recalibrate', DEFRECAL)            
        self.valuemin = 0 # if auto, calibration is always on max RPM, otherwise min PWM
        self.valuemax = 0
        self.timer = None
        
        self.calpwm = self.checkkeydef(settings, 'fan', 'PWMcalibrated', DEFAULTMANUALSTARTPERC)
        if self.calpwm <= 0:
            self.calpwm = 1.0 # minimum PWM value to keep the fan running
               
        if self.auto:
            self.autoCalibrate()
        else:
            self.valuemin = self.calpwm

    def __del__(self):
        pass
    
    def terminate(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
    
    def get(self):
        return self.valuemin, self.valuemax
    
    def autoCalibrate(self):
        self.logi("Auto calibrating")
        self.mutex.acquire()
        self.fanoutput.set(MAXPWM)
        self.exitevent.wait(AUTOCALSETUPTIME)
        if not self.exitevent.is_set():
            self.valuemax = self.rpm.get()
            self.fanoutput.set(self.calpwm)
            self.exitevent.wait(AUTOCALSETUPTIME)
        if not self.exitevent.is_set():
            self.valuemin = self.rpm.get()
            self.fanoutput.set(MINPWM)
            self.logi("Auto calibration finished, minimum RPM: {:.3f}, maximum RPM: {:.3f}".format(self.valuemin, self.valuemax))
            self.logi("Schedule for next auto calibration in {} days at 12:00 PM".format(self.recalibrate))
            self.rpm.setmax(self.valuemax*1.2)
        if not self.exitevent.is_set():
            #schedule next calibration
            if self.timer:
                self.timer.cancel()
                self.timer = None
            now=datetime.today()
            nextcal=now.replace(day=now.day, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=self.recalibrate)
            deltacalsecs=(nextcal-now).total_seconds()
            self.timer = Timer(deltacalsecs, self.autoCalibrate)
            self.timer.start()
        self.mutex.release()
    
    def manualCalibrate(self):
        print("Manual calibration")
        self.mutex.acquire()
        pwmlevel = MINPWM-MANUALPWMDELTA
        choice = False
        stdinput = stdin("", exitevent = self.exitevent)
        while not choice and pwmlevel<MAXPWM and not self.exitevent.is_set():
            pwmlevel += MANUALPWMDELTA
            self.fanoutput.set(pwmlevel)
            choice = stdinput.yn_choice("Is the fan running? (PWM = {})".format(pwmlevel), 'n')
        
        if not self.exitevent.is_set():
            self.valuemin = pwmlevel
            self.fanoutput.set(MINPWM)
            self.mutex.release()
            print("Manual calibration finished, minimum PWM: {}".format(self.valuemin))
            
        return self.valuemin
        
######################### MAIN ##########################
if __name__ == "__main__":
    pass
