# -*- coding: utf-8 -*-
#########################################################
# SERVICE : linear.py                                   #
#           Implements a linear control loop            #
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
# Class : linear                                        #
#########################################################
class linear(object):
    def __init__(self):
        self.sample_time = 1.0
        self.outputmin = 0.0
        self.outputmax = 100.0
        self.startval = 40.0
        self.fullval = 60.0
        self.linsteps = 2.5
        
        self.clear()

    def __del__(self):
        pass
    
    def clear(self):
        #Clears computations and coefficients
        self.discrete_output_error = 0.0
        self.output = 0.0
        
        self.range = self.fullval - self.startval
        self.rc = (self.outputmax - self.outputmin) / self.range
        
        self.current_time = time()
        self.last_time = self.current_time
        
        return self.output
    
    def updateSettings(self, frequency = 1.0, outputmin = 0.0, outputmax = 100.0, startval = 40.0, fullval = 60.0, linsteps = 2.5):
        """Linear control that should be updated at a regular interval.
        Based on a pre-determined sample time, the controller decides if it should compute or return immediately.
        """
        self.sample_time = 1/frequency
        """Determines the minumum output if switched off"""
        self.outputmin = outputmin
        """Determines the maximum output if switched on"""
        self.outputmax = outputmax
        """The value where linear control starts. Before this setpoint, output will be switched off"""
        self.startval = startval
        """The value where linear control ends. Beyond this setpoint, output will run to outputmax"""
        self.fullval = fullval
        """The linear steps in which the output will be increased"""
        self.linsteps = linsteps
        
        self.clear()
        
    def update(self, feedback_value, current_time=None):
        """Calculates linear value for given reference feedback
        """
        
        self.current_time = current_time if current_time is not None else time()
        delta_time = self.current_time - self.last_time

        if delta_time >= self.sample_time:
            error = feedback_value - self.startval
            discrete_error = self.linsteps * int(error/self.linsteps)
            if error < 0:
                self.output = 0.0
                self.discrete_output_error = discrete_error + self.linsteps * 0.5
            elif error < self.range + self.linsteps:
                if error > self.discrete_output_error + self.linsteps * 0.5:
                    # increase output accordingly
                    self.output = self.outputmin + self.rc * (discrete_error - self.linsteps)
                    self.discrete_output_error = discrete_error + self.linsteps * 0.5
                elif error < self.discrete_output_error - self.linsteps * 0.5:
                    # decrease output accordingly
                    self.output = self.outputmin + self.rc * discrete_error
                    self.discrete_output_error = discrete_error + self.linsteps * 0.5
                # else don't do anything
            else:
                self.output = self.outputmax
                self.discrete_output_error = discrete_error
                
        return self.output  

######################### MAIN ##########################
if __name__ == "__main__":
    pass
