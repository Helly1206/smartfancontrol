# -*- coding: utf-8 -*-
#########################################################
# SERVICE : fanctrl.py                                  #
#           Controls the fan RPM, 3 modes:              #
#           * on/ off control                           #
#           * PWM control (linear from start level)     #
#           * RPM control (PI controller)               #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################
from common.common import common
from common.stdin import stdin
from control.pid import pid
from threading import Thread, Event
from control.autotune import autotune
from engine.calibrate import calibrate
#########################################################

####################### GLOBALS #########################
FANCTRL_NONE  = 0
FANCTRL_ONOFF = 1
FANCTRL_PWM   = 2
FANCTRL_RPM   = 3
FREQDEFAULT   = 10
PDEFAULT      = 10
IDEFAULT      = 1
MANUAL_SLEEP  = 1
DEFAULTCALPWM = 30
FANDEBUG      = False
#########################################################

###################### FUNCTIONS ########################

#########################################################
"""
<mode> is the mode used to control the fan. Default is RPM. 
    ONOFF: Only on/ off control is used
    PWM: PWM control is used, with no RPM feedback (for fans that don't have this option)
         Manual calibration is required
    RPM: PWM control with RPM feedback is used. Calibration is performed automatically
                
<Frequency> The frequency of the fan control loop in Hz. default is 10.
<Pgain> The P gain of the fan control loop. Default is 10. Only used in RPM mode.
<Igain> The I gain of the fan control loop. Default is 1. Only used in RPM mode.
"""
#########################################################
# Class : fanctrl                                       #
#########################################################
class fanctrl(Thread, common):
    def __init__(self, rpm, fanoutput, mutex, settings, alarm, logger, exitevent, autocal):
        self.fanoutput = fanoutput
        self.rpm = rpm
        self.mutex = mutex
        self.alarm = alarm
        self.logger = logger
        self.exitevent = exitevent
        self.runthread = Event()
        self.runthread.clear()
        common.__init__(self, self.logger)
        self.mode = FANCTRL_NONE
        self.pid = None
        self.calibrate = None
        mode = self.checkkey(settings, 'fan', 'mode')
        if mode:
            if mode.lower() == "rpm":
                self.mode = FANCTRL_RPM
                self.pid = pid()
                self.frequency = self.checkkeydef(settings, 'fan', 'Frequency', FREQDEFAULT)
                self.pgain = self.checkkeydef(settings, 'fan', 'Pgain', PDEFAULT)
                self.igain = self.checkkeydef(settings, 'fan', 'Igain', IDEFAULT) 
            elif mode.lower() == "pwm":
                self.mode = FANCTRL_PWM
            else:
                self.mode = FANCTRL_ONOFF
        else:
            self.mode = FANCTRL_ONOFF
        self.calpwm = self.checkkeydef(settings, 'fan', 'PWMcalibrated', DEFAULTCALPWM)
        self.rpmcmd = 0.0
        self.calibrate = calibrate(self.rpm, self.fanoutput, self.mutex, settings, self.logger, self.exitevent, autocal)
        Thread.__init__(self)
        Thread.start(self)
        
    def __del__(self):
        del self.calibrate
        del self.pid
        
    def __str__(self):
        fanstr = "-"
        if self.mode == FANCTRL_RPM:
            fanstr = "{} [{}]".format(self.rpm, self.fanoutput)
        else: # PWM/ ONOFF
            fanstr = self.fanoutput
        return fanstr
    
    def __repr__(self):
        fanstr = "-"
        if self.mode == FANCTRL_RPM:
            fanstr = "{!r}, {!r}".format(self.rpm, self.fanoutput)
        else: # PWM/ ONOFF
            fanstr = "0.00, {!r}".format(self.fanoutput)
        return fanstr
        
    def start(self, Kp = -100000, Ki = -100000):
        if self.mode == FANCTRL_RPM:
            if Kp == -100000:
                Kp = self.pgain
            if Ki == -100000:
                Ki = self.igain
            if Ki == 0:
                windup = 100.0
            else:
                windup = 100.0/Ki
            self.mutex.acquire()
            self.pid.updateSettings(Kp = Kp, Ki = Ki, Kd = 0.0, frequency = self.frequency*2, 
                                    direction = 0, sign = 1, outputmin = 0.001, outputmax = 100.0, windup = windup, 
                                    setpoint = 0)
            self.mutex.release()
        self.runthread.set()
        
    def stop(self):
        self.runthread.clear()
    
    def exit(self):
        self.calibrate.terminate()
        self.exitevent.set()
        
    def manualCalibrate(self):
        return self.calibrate.manualCalibrate()
        
    def run(self):
        try:
            #thread only needs to run in rpm mode
            if self.mode == FANCTRL_RPM:
                stime = 1/self.frequency
                while not self.exitevent.is_set():
                    if self.runthread.is_set():
                        self.logi("Fan mode: RPM (control started) @ {} Hz".format(self.frequency))
                        self.pid.clear()
                        while not self.exitevent.is_set() and self.runthread.is_set():
                            self.mutex.acquire()
                            if self.rpmcmd == 0:
                                self.fanoutput.set(0)
                                self.pid.clear()
                            else:
                                self.fanoutput.set(self.pid.update(self.rpm.get()))
                            self.getalarm()
                            self.mutex.release()
                            self.exitevent.wait(stime)
                        self.fanoutput.set(0)
                        self.logi("Fan mode: RPM (control finished)")
                    else:
                        self.exitevent.wait(MANUAL_SLEEP)
            elif self.mode == FANCTRL_PWM:
                self.logi("Fan mode: PWM")
            else:
                self.logi("Fan mode: ONOFF")
        except Exception as e:
            self.logger.exception(e)
            
    def set(self, value):
        self.mutex.acquire()
        if self.mode == FANCTRL_RPM:
            self.rpmcmd = float(value)
            self.pid.updateCommand(self.rpmcmd)
        elif self.mode == FANCTRL_ONOFF:
            if value:
                self.fanoutput.set(100.0)
            else:
                self.fanoutput.set(0.0)
        else:
            self.fanoutput.set(float(value))
        self.mutex.release()
        
    def get(self):
        value = 0
        if self.mode == FANCTRL_RPM:
            value = self.rpm.get()
        else:
            value = self.fanoutput.get()
        return value
        
    def min(self):
        minval = 0
        if self.mode == FANCTRL_RPM:
            minval = self.calibrate.get()[0]
            if FANDEBUG:
                minval = 750
        elif self.mode == FANCTRL_PWM:
            minval = self.calpwm
        else:
            minval = 0
        return minval
    
    def max(self):
        maxval = 0
        if self.mode == FANCTRL_RPM:
            maxval = self.calibrate.get()[1]
            if FANDEBUG:
                maxval = 4500
        else:
            maxval = 100.0
        return maxval
            
    def manual(self):
        self.exitevent.wait(MANUAL_SLEEP)
        print("Manual fan control")
        print("Enter value to update for inputfield")
        inptxt = ""
        if self.mode == FANCTRL_RPM:
            inptxt = "Enter RPM: "
        elif self.mode == FANCTRL_PWM:
            inptxt = "Enter PWM: "
        else:
            inptxt = "Enter ONOFF: "
        stdinput = stdin(inptxt, exitevent = self.exitevent, mutex=self.mutex, displaylater = True, background = True)
        while not self.exitevent.is_set():   
            self.mutex.acquire()
            if self.mode == FANCTRL_RPM:
                print("RPM: {:.3f}, PWM: {:.3f}, RPMcmd: {:.3f}\r".format(self.rpm.get(), self.fanoutput.get(), self.rpmcmd))
            elif self.mode == FANCTRL_ONOFF:
                print("RPM: {:.3f}, ON: {}\r".format(self.rpm.get(), self.fanoutput.get()>0))
            else:
                print("RPM: {:.3f}, PWM: {:.3f}\r".format(self.rpm.get(), self.fanoutput.get()))
            self.mutex.release()
            
            inp = stdinput.getinput()
            if inp:
                value = self.gettype(inp, False)
                if value != None:
                    self.set(value)
                else:
                    print("Invalid input!")
                stdinput = stdin(inptxt, exitevent = self.exitevent, mutex=self.mutex, displaylater = True, background = True)
            else: 
                self.exitevent.wait(MANUAL_SLEEP)
        print("Finished manual fan control")
        return
    
    def RPMautotune(self):
        self.exitevent.wait(MANUAL_SLEEP)
        inptxt = ""
        if self.mode == FANCTRL_RPM:
            print("Autotuning")
        elif self.mode == FANCTRL_PWM:
            print("No autotuning in PWM mode possible")
            return False, 0, 0
        else:
            print("No autotuning in ON/ OFF mode possible")
            return False, 0, 0
        piautotune = autotune(self)
        rv = piautotune.tune()
        del piautotune
        print("Finished autotuning")
        return rv
    
    def getalarm(self):
        if self.mode == FANCTRL_RPM:
            if self.calibrate.get()[0] <= 0.0 and self.calibrate.get()[1] <= 0.0 and not FANDEBUG:
                if not self.alarm.get(self.alarm.ALARM_FANCALSTALL):
                    self.alarm.set(self.alarm.ALARM_FANCALSTALL)
                    self.alarm.reset(self.alarm.ALARM_FANNOTRUNNING)
                    self.alarm.reset(self.alarm.ALARM_FANNORPMMODE)
                    self.alarm.reset(self.alarm.ALARM_FANNOTMAXRPM)
                    self.loge(self.alarm)    
                return self.alarm.ALARM_FANCALSTALL
            elif self.rpmcmd > 0.0 and self.rpm.get() <= 0.0:
                if self.alarm.timerGet():
                    if not self.alarm.get(self.alarm.ALARM_FANNOTRUNNING):
                        self.alarm.set(self.alarm.ALARM_FANNOTRUNNING)
                        self.alarm.reset(self.alarm.ALARM_FANNORPMMODE)
                        self.alarm.reset(self.alarm.ALARM_FANNOTMAXRPM)
                        self.alarm.reset(self.alarm.ALARM_FANCALSTALL)
                        self.loge(self.alarm)    
                    return self.alarm.ALARM_FANNOTRUNNING
                else:
                    return self.alarm.ALARM_NONE
            elif self.fanoutput.get() >= 100.0 and self.rpm.get() <= self.max()*0.97:
                if self.alarm.timerGet():
                    if not self.alarm.get(self.alarm.ALARM_FANNOTMAXRPM):
                        self.alarm.set(self.alarm.ALARM_FANNOTMAXRPM)
                        self.alarm.reset(self.alarm.ALARM_FANNORPMMODE)
                        self.alarm.reset(self.alarm.ALARM_FANNOTRUNNING)
                        self.alarm.reset(self.alarm.ALARM_FANCALSTALL)
                        self.loge(self.alarm)    
                    return self.alarm.ALARM_FANNOTMAXRPM
                else:
                    return self.alarm.ALARM_NONE
            else:
                self.alarm.timerReset()
                self.alarm.reset(self.alarm.ALARM_FANNOTRUNNING)
                self.alarm.reset(self.alarm.ALARM_FANNORPMMODE)
                self.alarm.reset(self.alarm.ALARM_FANNOTMAXRPM) 
                self.alarm.reset(self.alarm.ALARM_FANCALSTALL)
                return self.alarm.ALARM_NONE
        else: 
            if not self.alarm.get(self.alarm.ALARM_FANNORPMMODE):
                self.alarm.set(self.alarm.ALARM_FANNORPMMODE)
                self.alarm.reset(self.alarm.ALARM_FANNOTRUNNING)
                self.alarm.reset(self.alarm.ALARM_FANNOTMAXRPM)
                self.alarm.reset(self.alarm.ALARM_FANCALSTALL)
                self.logw(self.alarm)
            return self.alarm.ALARM_FANNORPMMODE
                 

######################### MAIN ##########################
if __name__ == "__main__":
    pass
