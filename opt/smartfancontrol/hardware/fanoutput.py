# -*- coding: utf-8 -*-
#########################################################
# SERVICE : fanoutput.py                                #
#           Fan output signal depending on mode         #
#                                                       #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################
from common.common import common
from hardware.pwm import pwm
from hardware.power import power
#########################################################

####################### GLOBALS #########################

#########################################################

###################### FUNCTIONS ########################

#########################################################

#########################################################
# Class : fanoutput                                     #
#########################################################
class fanoutput(common):
    def __init__(self, piio, settings):
        mode = self.checkkey(settings, 'fan', 'mode')
        if mode:
            if mode.lower() != 'onoff':
                self.pwm = pwm(piio, settings)
            else:
                self.pwm = None
        self.power = power(piio, settings)
        self.ispowered = False

    def __del__(self):
        del self.power
        del self.pwm
    
    def __str__(self):
        fanoutstr = "-"
        if self.pwm:
            fanoutstr = str(self.pwm)
        else:
            fanoutstr = str(self.power)
        return fanoutstr
    
    def __repr__(self):
        fanoutstr = "-"
        if self.pwm:
            fanoutstr = repr(self.pwm)
        else:
            fanoutstr = repr(self.power)
        return fanoutstr
    
    def set(self, level):
        poweron = level > 0
        if poweron != self.ispowered:
            self.power.set(poweron)
            self.ispowered = poweron
        if self.pwm:
            self.pwm.set(level)
    
    def get(self):
        level = 0
        if self.pwm:
            level = self.pwm.get()
        else:
            level = self.power.get()
        return level
    
    def exit(self):
        self.power.exit()
        self.pwm.exit()

######################### MAIN ##########################
if __name__ == "__main__":
    pass
