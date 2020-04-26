# -*- coding: utf-8 -*-
#########################################################
# SERVICE : onoff.py                                    #
#           Implements an onoff control loop            #
#                                                       #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################
from time import time
#########################################################

####################### GLOBALS #########################

#########################################################

###################### FUNCTIONS ########################

#########################################################

#########################################################
# Class : onoff                                         #
#########################################################
class onoff(object):
    def __init__(self):
        self.sample_time = 1.0
        self.outputmin = 0.0
        self.outputmax = 100.0
        self.hysteresis = 5.0
        self.setpoint = 40.0
        
        self.clear()

    def __del__(self):
        pass
    
    def clear(self):
        #Clears computations and coefficients
        self.output = 0.0
        
        self.current_time = time()
        self.last_time = self.current_time
        
        return self.output
    
    def updateSettings(self, frequency = 1.0, outputmin = 0.0, outputmax = 100.0, hysteresis = 5.0, setpoint = 40.0):
        """On/off control that should be updated at a regular interval.
        Based on a pre-determined sample time, the controller decides if it should compute or return immediately.
        """
        self.sample_time = 1/frequency
        """Determines the minumum output if switched off"""
        self.outputmin = outputmin
        """Determines the maximum output if switched on"""
        self.outputmax = outputmax
        """The hysteresis before switching off if on"""
        self.hysteresis = hysteresis
        """The setpoint. Will switch on at setpoint, will switch off at setpoint-hysteresis"""
        self.setpoint = setpoint
        
        self.clear()
        
    def update(self, feedback_value, current_time=None):
        """Calculates ONOFF value for given reference feedback
        """
        
        self.current_time = current_time if current_time is not None else time()
        delta_time = self.current_time - self.last_time

        if delta_time >= self.sample_time:
            if feedback_value > self.setpoint:
                self.output = self.outputmax
            elif feedback_value < self.setpoint - self.hysteresis:
                self.output = self.outputmin
                
        return self.output        

######################### MAIN ##########################
if __name__ == "__main__":
    pass
