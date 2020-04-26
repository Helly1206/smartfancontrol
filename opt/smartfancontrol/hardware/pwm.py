# -*- coding: utf-8 -*-
#########################################################
# SERVICE : pwm.py                                      #
#           Hardware pwm handling using pigpio          #
#           Can a.i. be used for motor, fan or          #
#           temperature control                         #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################
from common.common import common
try:
    import pigpio
    ifinstalled = True                     
except ImportError:
    ifinstalled = False
#########################################################

####################### GLOBALS #########################
HWPWMFACTOR = 10000.0
MAXPERC = 100.0
DEFGPIO = 18
DEFFREQ = 10000
DEFINVERT = False
#########################################################

###################### FUNCTIONS ########################

#########################################################

#########################################################
# Class : pwm                                           #
#########################################################
class pwm(common):
    def __init__(self, piio, settings):
        self.piio = piio
        self.gpio = self.checkkeydef(settings, 'fan', 'PWMgpio', DEFGPIO)
        self.frequency = self.checkkeydef(settings, 'fan', 'PWMfrequency', DEFFREQ)
        self.invert = self.checkkeydef(settings, 'fan', 'PWMinvert', DEFINVERT)
        self.currpwm = 0
        
        if ifinstalled and self.piio:
            self.piio.set_mode(self.gpio,pigpio.ALT5)
            self.set(0)
            #self.piio.write(self.gpio, 0)

    def __del__(self):
        pass
    
    def __str__(self):
        return "{:.1f}% PWM".format(self.get())
    
    def __repr__(self):
        return "{:.1f}".format(self.get())
    
    def set(self, level):
        if ifinstalled and self.piio:
            if level < 0:
                level = 0
            elif level > 100:
                level = 100
            if self.invert:
                self.currpwm = round((MAXPERC - level)*HWPWMFACTOR)
            else:
                self.currpwm = round(level*HWPWMFACTOR)
            self.piio.hardware_PWM(self.gpio, self.frequency, self.currpwm)
    
    def get(self):
        level = 0
        if self.invert:
            level = MAXPERC - (self.currpwm/HWPWMFACTOR)
        else:
            level = self.currpwm/HWPWMFACTOR
        return level
    
    def exit(self):
        if ifinstalled and self.piio:
            self.piio.write(self.gpio, 0)

######################### MAIN ##########################
if __name__ == "__main__":
    pass
