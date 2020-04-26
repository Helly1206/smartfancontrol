# -*- coding: utf-8 -*-
#########################################################
# SERVICE : tempctrl.py                                 #
#           Controls the temperature with fan, 3 modes: #
#           * on/ off control                           #
#           * linear control                            #
#           * PI control                                #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################
from common.common import common
from control.onoff import onoff
from control.linear import linear
from control.pid import pid
from threading import Thread, Event, Lock
from common.stdin import stdin
from common.monitor import monitor
#########################################################

####################### GLOBALS #########################
TEMPCTRL_NONE    = 0
TEMPCTRL_ONOFF   = 1
TEMPCTRL_LINEAR  = 2
TEMPCTRL_PI      = 3
TEMPONDEFAULT    = 55
TEMPHYSTDEFAULT  = 5
FANSTARTDEFAULT  = 20
TEMPSTARTDEFAULT = 45
TEMPFULLDEFUALT  = 65
LINSTEPSDEFUALT  = 2.5
TFREQDEFAULT     = 1
TPDEFAULT        = 10
TIDEFAULT        = 1
IDLE_SLEEP       = 1
#########################################################

###################### FUNCTIONS ########################

#########################################################
"""
<control> contains settings related to the temperature controller.
<mode> is the mode used to control the temperature loop. Default is LINEAR. 
ONOFF: Only on/ off control is used, if this mode is selected, on/off control will also be used to
       control the fan.
LINEAR: If the temperature is within the linear range, the fan speed will increase linear with a
    	temperature increase.
PI: PI temperature control is used.
<TempOn> The temperature to switch the fan on. Default is 55 Celcius. Only used in ONOFF mode.
         If Farenheit is selected, then this temperature is in Farenheit.
<TempHyst> The temperature hysteresis to switch the fan off again. Default is 5 Celcius.
           Only used in ONOFF mode. If Farenheit is selected, then this temperature is in Farenheit.
<TempStart> The temperature to start the fan controller. Default is 45 Celcius. 
            Only used in LINEAR and PI mode. If Farenheit is selected, then this temperature is in Farenheit.
<TempFull> The temperature on which the fan controller should run full speed. Default is 65 Celcius. 
           Only used in LINEAR and PI mode. If Farenheit is selected, then this temperature is in Farenheit.
<LinSteps> The temperature steps/ hysteresis. To provent oscillating on small temperature changes. 
           Default is 2.5 Celcius. Only used in LINEAR mode. If Farenheit is selected, then this temperature is in Farenheit.
<Frequency> The frequency of the temperature control loop in Hz. default is 1.
<Pgain> The P gain of the temperature control loop. Default is 10. Only used in PI mode.
<Igain> The I gain of the temperature control loop. Default is 1. Only used in PI mode.
"""


#########################################################
# Class : tempctrl                                      #
#########################################################
class tempctrl(Thread, common):
    def __init__(self, fanctrl, temp, settings, alarm, logger, exitevent, monstatus):
        self.fanctrl = fanctrl
        self.temp = temp
        self.alarm = alarm
        self.logger = logger
        self.exitevent = exitevent
        self.runthread = Event()
        self.runthread.clear()
        self.mutex = Lock()
        common.__init__(self, self.logger)
        self.mode = TEMPCTRL_NONE
        self.pid = None
        self.linear = None
        self.onoff = None
        self.frequency = self.checkkeydef(settings, 'control', 'Frequency', TFREQDEFAULT)
        self.tempstart = self.checkkeydef(settings, 'control', 'TempStart', TEMPSTARTDEFAULT)
        self.tempfull = self.checkkeydef(settings, 'control', 'TempFull', TEMPFULLDEFUALT)
        mode = self.checkkey(settings, 'control', 'mode')
        if mode:
            if mode.lower() == "pi":
                self.mode = TEMPCTRL_PI
                self.pid = pid()
                self.pgain = self.checkkeydef(settings, 'control', 'Pgain', TPDEFAULT)
                self.igain = self.checkkeydef(settings, 'control', 'Igain', TIDEFAULT)
            elif mode.lower() == "linear":
                self.mode = TEMPCTRL_LINEAR
                self.linear = linear()
                self.linsteps = self.checkkeydef(settings, 'control', 'LinSteps', LINSTEPSDEFUALT)
            else:
                self.mode = TEMPCTRL_ONOFF
                self.onoff = onoff()
                self.tempon = self.checkkeydef(settings, 'control', 'TempOn', TEMPONDEFAULT)
                self.temphyst = self.checkkeydef(settings, 'control', 'TempHyst', TEMPHYSTDEFAULT)
        else:
            self.mode = TEMPCTRL_ONOFF
            self.onoff = onoff()
            self.tempon = self.checkkeydef(settings, 'control', 'TempOn', TEMPONDEFAULT)
            self.temphyst = self.checkkeydef(settings, 'control', 'TempHyst', TEMPHYSTDEFAULT)
        self.monitor = monitor(fanctrl, temp, self.mutex, alarm, logger, exitevent, monstatus)
        Thread.__init__(self)
        Thread.start(self)

    def __del__(self):
        del self.monitor
        del self.onoff
        del self.linear
        del self.pid
    
    def start(self, Kp = -100000, Ki = -100000):
        if self.mode == TEMPCTRL_PI:
            if Kp == -100000:
                Kp = self.pgain
            if Ki == -100000:
                Ki = self.igain
            if Ki == 0:
                windup = self.fanctrl.max()
            else:
                windup = self.fanctrl.max()/Ki
            self.mutex.acquire()
            self.pid.updateSettings(Kp = Kp, Ki = Ki, Kd = 0.0, frequency = self.frequency*2, 
                                    direction = 1, sign = -1, outputmin = self.fanctrl.min(), outputmax = self.fanctrl.max(), windup = windup, 
                                    setpoint = self.tempstart)
            self.mutex.release()
        elif self.mode == TEMPCTRL_LINEAR:
            self.mutex.acquire()
            self.linear.updateSettings(frequency = self.frequency*2, outputmin = self.fanctrl.min(), outputmax = self.fanctrl.max(), 
                                       startval = self.tempstart, fullval = self.tempfull, linsteps = self.linsteps)
            self.mutex.release()
        else: # TEMPCTRL_ONOFF
            self.mutex.acquire()
            self.onoff.updateSettings(frequency = self.frequency*2, outputmin = self.fanctrl.min(), outputmax = self.fanctrl.max(), 
                                      hysteresis = self.temphyst, setpoint = self.tempon)
            self.mutex.release()
        self.runthread.set()
        self.monitor.start()
        
    def stop(self):
        self.monitor.stop()
        self.runthread.clear()
    
    def exit(self):
        self.monitor.exit()
        self.exitevent.set()
        
    def run(self):
        try:
            stime = 1/self.frequency
            while not self.exitevent.is_set():
                if self.runthread.is_set():
                    if self.mode == TEMPCTRL_PI:
                        self.logi("Temperature control: PI (control started) @ {} Hz".format(self.frequency))
                        self.pid.clear()
                        while not self.exitevent.is_set() and self.runthread.is_set():
                            self.mutex.acquire()
                            self.temp.update()
                            if self.temp.get() < self.tempstart:
                                self.fanctrl.set(0)
                                self.pid.clear()
                            elif self.temp.get() > self.tempfull:
                                self.fanctrl.set(self.fanctrl.max())
                                self.pid.clear()
                            else:
                                self.fanctrl.set(self.pid.update(self.temp.get()))
                            self.mutex.release()
                            self.exitevent.wait(stime)
                        self.fanctrl.set(0)
                        self.logi("Temperature control: PI (control finished)")        
                    elif self.mode == TEMPCTRL_LINEAR:
                        self.logi("Temperature control: LINEAR (control started) @ {} Hz".format(self.frequency))
                        self.linear.clear()
                        while not self.exitevent.is_set() and self.runthread.is_set():
                            self.mutex.acquire()
                            self.temp.update()
                            self.fanctrl.set(self.linear.update(self.temp.get()))
                            self.mutex.release()
                            self.exitevent.wait(stime)
                        self.fanctrl.set(0)
                        self.logi("Temperature control: LINEAR (control finished)")      
                    else:
                        self.logi("Temperature control: ONOFF (control started) @ {} Hz".format(self.frequency))
                        self.onoff.clear()
                        while not self.exitevent.is_set() and self.runthread.is_set():
                            self.mutex.acquire()
                            self.temp.update()
                            self.fanctrl.set(self.onoff.update(self.temp.get()))
                            self.mutex.release()
                            self.exitevent.wait(stime)
                        self.fanctrl.set(0)
                        self.logi("Temperature control: ONOFF (control finished)")      
                else:
                    self.exitevent.wait(IDLE_SLEEP)
        except Exception as e:
            self.logger.exception(e)        
            
    def determine(self):
        stdinput = stdin("", exitevent = self.fanctrl.exitevent)
        print("Determining Pgain and Igain")
        Kp = ((self.fanctrl.max() - self.fanctrl.min()) / (self.tempfull - self.tempstart)) * 0.9
        Ki = Kp*0.1/(150.0)
        print("Results: Pgain = {:.3f}, Igain = {:.3f}".format(Kp, Ki))
        Ok = stdinput.yn_choice("Store results?", "Y")
        return Ok, round(Kp, 3), round(Ki, 3)

######################### MAIN ##########################
if __name__ == "__main__":
    pass
