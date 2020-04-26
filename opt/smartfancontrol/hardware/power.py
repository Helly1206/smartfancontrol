# -*- coding: utf-8 -*-
#########################################################
# SERVICE : power.py                                    #
#           Hardware power on/ off using pigpio         #
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
DEFGPIO   = 27
DEFINVERT = False
DEFON     = "ON"
DEFOFF    = "OFF"
#########################################################

###################### FUNCTIONS ########################

#########################################################

#########################################################
# Class : power                                         #
#########################################################
class power(common):
    def __init__(self, piio, settings):
        self.piio = piio
        self.gpio = self.checkkeydef(settings, 'fan', 'ONOFFgpio', DEFGPIO)
        self.invert = self.checkkeydef(settings, 'fan', 'ONOFFinvert', DEFINVERT)
        
        if ifinstalled and self.piio:
            self.piio.set_mode(self.gpio,pigpio.OUTPUT)
            self.piio.write(self.gpio, 0)

    def __del__(self):
        pass
    
    def __str__(self):
        pwrstr = DEFOFF
        if self.get():
            pwrstr = DEFON
        return "{}".format(pwrstr)
    
    def __repr__(self):
        pwrstr = "0"
        if self.get():
            pwrstr = "1"
        return pwrstr
    
    def set(self, value):
        if ifinstalled and self.piio:
            if self.invert:
                ivalue = not value
            else:
                ivalue = value
            self.piio.write(self.gpio, ivalue)
    
    def get(self):
        value = False
        if ifinstalled and self.piio:
            if self.invert:
                value = self.piio.read(self.gpio) == False
            else:
                value =self.piio.read(self.gpio) == True
        return value

    def exit(self):
        if ifinstalled and self.piio:
            self.piio.write(self.gpio, 0)    
    
######################### MAIN ##########################
if __name__ == "__main__":
    pass
