# -*- coding: utf-8 -*-
#########################################################
# SERVICE : rpm.py                                      #
#           Accurate rpm counting using pigpio          #
#           Can a.i. be used for motor or fan           #
#           control                                     #
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
USPM = 60000000.0 # micro seconds per minute
WATCHDOG = 1000 # Milliseconds.
DEFGPIO = 17
DEFPPR = 2
DEFEDGE = True
DEFMOVAVSIZE = 0
DEFPULLUP = True
#########################################################

###################### FUNCTIONS ########################

#########################################################

#########################################################
# Class : rpm                                           #
#########################################################
class rpm(common):
    def __init__(self, piio, settings):
        self.piio = piio
        ppr = self.checkkeydef(settings, 'fan', 'RPMppr', DEFPPR)
        edge = self.checkkeydef(settings, 'fan', 'RPMedge', DEFEDGE)
        if edge:
            self.ppr = 2*ppr
        else:
            self.ppr = ppr
        self.period = 0
        self.prevtick = 0
        self.movavsize = self.checkkeydef(settings, 'fan', 'RPMfiltersize', DEFMOVAVSIZE)
        self.movavlist = []
        self.callback = None
        self.maxrpm = 0
        
        if ifinstalled and self.piio:
            gpio = self.checkkeydef(settings, 'fan', 'RPMgpio', DEFGPIO)
            self.piio.set_mode(gpio,pigpio.INPUT)
            pullup = self.checkkeydef(settings, 'fan', 'RPMpullup', DEFPULLUP)
            if pullup:
                self.piio.set_pull_up_down(gpio, pigpio.PUD_UP)
            else:
                self.piio.set_pull_up_down(gpio, pigpio.PUD_OFF)
            if edge:
                cbedge = pigpio.EITHER_EDGE
            else:
                cbedge = pigpio.RISING_EDGE
            self.callback = self.piio.callback(gpio, cbedge, self._callbackfunction)
            self.piio.set_watchdog(gpio, WATCHDOG)

    def __del__(self):
        pass
    
    def __str__(self):
        return "{:.2f} RPM".format(self.get())
    
    def __repr__(self):
        return "{:.2f}".format(self.get())
    
    def get(self):
        # returns RPM
        retrpm = 0.0
        if self.period:
            retrpm = USPM/(self.period*self.ppr)
            if self.maxrpm > 0 and retrpm > self.maxrpm:
                retrpm = 0.0
        return retrpm
    
    def setmax(self, maxrpm):
        self.maxrpm = maxrpm
        
    def _callbackfunction(self, gpio, level, tick):
        # tick in microseconds
        if level == 2: # Watchdog timeout.
            self.prevtick = 0
            self.period = self._movav(0)
        else: # Rising edge or falling edge.
            # If not self.edge, no callback on falling edge
            if self.prevtick:
                rawperiod = pigpio.tickDiff(self.prevtick, tick)
                self.period = self._movav(rawperiod)
            self.prevtick = tick     
            
    def _movav(self, period):
        movavperiod = 0
        if self.movavsize < 2:
            movavperiod = period
        else:
            if period == 0:
                self.movavlist.clear()
                movavperiod = period
            else:
                if len(self.movavlist) >= self.movavsize:
                    self.movavlist.pop(0)
                self.movavlist.append(period)
                movavperiod = sum(self.movavlist)/len(self.movavlist)     
        return movavperiod
        

######################### MAIN ##########################
if __name__ == "__main__":
    pass
