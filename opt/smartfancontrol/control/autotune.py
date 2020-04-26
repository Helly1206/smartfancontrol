# -*- coding: utf-8 -*-
#########################################################
# SERVICE : autotune.py                                 #
#           (Auto) tunes a PID control loop             #
#                                                       #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################
from time import time
from math import pow, sqrt
from common.common import common
from common.stdin import stdin
#########################################################

####################### GLOBALS #########################
STEP_SLEEP  = 0.01
LIN_SLEEP   = 5
STEP_LENGTH = 5
GAINMAX     = 1000
#########################################################

###################### FUNCTIONS ########################

#########################################################

#########################################################
# Class : autotune                                      #
#########################################################
class autotune(common):
    def __init__(self, fanctrl):
        self.fanctrl = fanctrl

    def __del__(self):
        pass

    def measurestep(self, value = None):
        if value == None:
            stdinput = stdin("", exitevent = self.fanctrl.exitevent, mutex=self.fanctrl.mutex, displaylater = False, background = False)
            print("Enter PWM value for step response")
            inptxt = "Enter PWM: "
            inp = stdinput.input(inptxt)
            if inp:
                value = self.fanctrl.gettype(inp, False)
                if value == None:
                    print("Invalid input!")
                    del stdinput
                    return None
            del stdinput
        print("Measuring fan step response (PWM = {:.2f}%)".format(value))
        self.fanctrl.fanoutput.set(0)
        self.fanctrl.exitevent.wait(2*LIN_SLEEP)
        tm = []
        rpm = []
        self.fanctrl.fanoutput.set(value)
        starttime = time()
        nowtime = starttime
        while nowtime-starttime <= STEP_LENGTH and not self.fanctrl.exitevent.is_set():
            self.fanctrl.exitevent.wait(STEP_SLEEP)
            nowtime = time()
            nowrpm = self.fanctrl.rpm.get()
            tm.append(nowtime-starttime)
            rpm.append(nowrpm)
        self.fanctrl.fanoutput.set(0)
        print("Finished measuring fan step response")
        return (tm, rpm)
    
    def plotstep(self, sr):
        print("Fan step response plot")
        stdinput = stdin()
        stdinput.eprint("Time [ms]\tRPM [1/min]")
        for i in range(0, len(sr[0])):
            stdinput.eprint("{:.2f}\t{:.2f}".format(sr[0][i],sr[1][i]))
        
        del stdinput
        print("Finished fan step response plot")
        return
    
    def plotlinear(self):
        print("Fan linear plot")
        stdinput = stdin()
        value = 0
        step = 5
        stdinput.eprint("Linear step: " + str(step))
        stdinput.eprint("PWM [%]\tRPM [1/min]")
        while value <= 100:
            self.fanctrl.fanoutput.set(value)
            self.fanctrl.exitevent.wait(LIN_SLEEP)
            nowrpm = self.fanctrl.rpm.get()
            stdinput.eprint("{:.2f}\t{:.2f}".format(value,nowrpm))
            value += step
        del stdinput
        print("Finished fan linear plot")
        return
    
    def calcparams(self, sr, sp):
        if len(sr[1]) > 0:
            maxval = max(sr[1])
            if sp > 0:
                Kpl = maxval/sp
            else:
                Kpl = 1
            max063 = 0.63*maxval
            #print("Max:",maxval,", Kpl:",Kpl,", max063:", max063)
            if len(sr[0]) > 0:
                tv = sr[0][[ n for n,i in enumerate(sr[1]) if i > 10][0]]
                t063 = sr[0][[ n for n,i in enumerate(sr[1]) if i >= max063][0]]
            else:
                tv = 1
                t063 = 2
            t = t063 - tv
            #print("tv:",tv,", t063:",t063, ",t:",t)
            if tv > 0:
                Ktot = 0.9 * t / tv
            else:
                Ktot = 0
            if Kpl > 0:
                Kp = Ktot / Kpl
            else:
                Kp = 0
            ti = 3.3 * tv
            if ti > 0:
                Ki = Kp / ti
            else:
                Ki = 0
            #print("Ktot:",Ktot,", Kp:",Kp,", ti:",ti,", Ki:", Ki)
        else:
            Kp = 0
            Ki = 0
        
        return Kp, Ki
    
    
    #calc mean square error
    #1. r = nowrpm - value
    #2. r^2
    #3. add up all r^2 (make a list and sum it afterwards)
    #4. devide by n-1 (n is number of items in the list)
    #5. take the square root of it
    #6. lower number is better fit (<1% of mean RPM, so also count mean RPM)
    def testPID(self, Kp, Ki):
        print("Test PID parameters")
        self.fanctrl.start(Kp = Kp, Ki = Ki)
        stdinput = stdin()
        value = 0
        step = 500 # check pwm < 1, don't count
        nowpwm = 0
        rpms = []
        r2 = []
        while nowpwm < 100 and not self.fanctrl.exitevent.is_set():
            self.fanctrl.set(value)
            self.fanctrl.exitevent.wait(LIN_SLEEP)
            nowrpm = self.fanctrl.rpm.get()
            nowpwm = self.fanctrl.fanoutput.get()
            if (nowpwm>1.0) and (nowpwm<99.0):
                rpms.append(value)
                r2.append(pow(nowrpm - value,2))
                #print("{:.2f}\t{:.2f}\t{:.2f}".format(value,nowrpm,pow(nowrpm - value,2)))
            value += step
        if len(r2) > 1:
            r = sqrt(sum(r2)/(len(r2)-1))
        else:
            r = 1
        if len(rpms) > 0:
            avg = sum(rpms)/len(rpms)
        else:
            avg = 1
        perc = 100*r/avg
        #print(r,avg,perc)
        self.fanctrl.stop()
        self.fanctrl.exitevent.wait(LIN_SLEEP/5)
        print("Finished test PID parameters")
        return perc
    
    def tune(self):
        sp = 50
        exit = False
        Ok = False
        ans = 'n'
        auto = True
        stdinput = stdin("", exitevent = self.fanctrl.exitevent)
        while not exit and not self.fanctrl.exitevent.is_set():
            correctResults = False
            while not correctResults and not self.fanctrl.exitevent.is_set():
                if auto:
                    Kp = 0
                    Ki = 0
                    sr = self.measurestep(sp)
                    if sr:
                        #self.plotstep(sr)
                        Kp, Ki = self.calcparams(sr, sp)    
                print("Results: Pgain = {:.3f}, Igain = {:.3f}".format(Kp, Ki))
                if (Kp == 0 or Kp > GAINMAX or Ki == 0 or Ki > GAINMAX) and not self.fanctrl.exitevent.is_set():
                    correctResults = stdinput.yn_choice("Incorrect autotuning results. Try again?", 'y')
                else:
                    correctResults = True
            if correctResults:
                r = self.testPID(Kp, Ki)
                Ok = r < 1
                print("RMS error = {:.2f}%, Ok (< 1% is Ok): {}".format(r, Ok))
            if not self.fanctrl.exitevent.is_set():
                ans = 'n' if Ok else 'y'    
                exit = not stdinput.yn_choice("Retry tuning?", ans)
            else:
                exit = True
            if not exit and not self.fanctrl.exitevent.is_set():
                auto, Kp, Ki, sp = self._tuneMenu(stdinput, Kp, Ki, sp)
        if not self.fanctrl.exitevent.is_set():
            ans = 'Y' if Ok else 'n'
            Ok = stdinput.yn_choice("Store results?", ans)
        del stdinput
        if self.fanctrl.exitevent.is_set():    
            Ok = False
            Kp = 0
            Ki = 0
        return Ok, round(Kp, 3), round(Ki, 3)
    
    def _tuneMenu(self, stdinput, Kp, Ki, sp):
        auto = True
        print("Enter option:")
        print("1: autotune again with current setpoint")
        print("2: change PWM setpoint and autotune (PWM = {:.2f}%)".format(sp))
        print("3: change parameters and test (Pgain = {:.3f}, Igain = {:.3f})".format(Kp, Ki))
        choice = stdinput.inputchar("Enter choice: (1/2/3)")
        if choice == '2':
            inp = stdinput.input("Enter new PWM setpoint: ")
            if inp:
                value = self.gettype(inp, False)
                if value != None:
                    if value > 0:
                        sp = value
                else:
                    print("Invalid input, let's autotune again!")
        elif choice == '3':
            inp = stdinput.input("Enter new Pgain: ")
            if inp:
                value = self.gettype(inp, False)
                if value != None:
                    Kp = value
                    auto = False
                else:
                    print("Invalid input, keep current value!")
            inp = stdinput.input("Enter new Igain: ")
            if inp:
                value = self.gettype(inp, False)
                if value != None:
                    Ki = value
                    auto = False
                else:
                    print("Invalid input, keep current value!")
        return auto, Kp, Ki, sp
                            
######################### MAIN ##########################
if __name__ == "__main__":
    pass
