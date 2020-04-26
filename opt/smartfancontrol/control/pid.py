# -*- coding: utf-8 -*-
#########################################################
# SERVICE : pid.py                                      #
#           Implements a PID control loop               #
#           (original by http://ivmech.github.io/ivPID) #
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
# Class : pid                                           #
#########################################################
class pid(object):
    def __init__(self):
        #Initialize everything to 0, use updatesettings for that
        self.Kp = 1.0
        self.Ki = 0.0
        self.Kd = 0.0

        self.sample_time = 1.0
        self.current_time = time()
        self.last_time = self.current_time
        self.direction = 0
        self.sign = 1
        self.outputmin = 0.0
        self.outputmax = 100.0
        self.setpoint = 40.0
        self.windup_guard = 20.0
        
        self.clear()

    def __del__(self):
        pass
    
    def clear(self):
        #Clears PID computations and coefficients
        self.PTerm = 0.0
        self.ITerm = 0.0
        self.DTerm = 0.0
        self.last_error = 0.0

        # Windup Guard
        self.int_error = 0.0

        self.output = 0.0
        
        self.current_time = time()
        self.last_time = self.current_time
        
        return self.output
        
    def updateSettings(self, Kp = 1.0, Ki = 0.0, Kd = 0.0, frequency = 1.0, direction = 0, sign = 1, outputmin = 0.0, outputmax = 100.0, windup = 20.0, setpoint = 40.0):
        """Determines how aggressively the PID reacts to the current error with setting Proportional Gain"""
        self.Kp = Kp
        """Determines how aggressively the PID reacts to the current error with setting Integral Gain"""
        self.Ki = Ki
        """Determines how aggressively the PID reacts to the current error with setting Derivative Gain"""
        self.Kd = Kd

        """Direction sets the relevant 'error' sign of the PID loop. Sometimes only one direction makes sense, e.g. in heating or cooling
        -1 is only negative direction, 0 is both directions, +1 is only positive direction
        Integrator will be reset and output will be set to 0 if the error sign is at the wrong direction.
        """
        self.direction = direction
        """Sign can invert the sign of the error signal for inverted PID controllers"""
        self.sign = sign
        """Determines the minumum output of the PID loop, to overcome required minimum startup power issues"""
        self.outputmin = outputmin
        """Determines the maximum output of the PID loop, if at maximum, the integrator will not be updated"""
        self.outputmax = outputmax
        
        """PID that should be updated at a regular interval.
        Based on a pre-determined sample time, the PID decides if it should compute or return immediately.
        """
        self.sample_time = 1/frequency
        """Integral windup, also known as integrator windup or reset windup,
        refers to the situation in a PID feedback controller where
        a large change in setpoint occurs (say a positive change)
        and the integral terms accumulates a significant error
        during the rise (windup), thus overshooting and continuing
        to increase as this accumulated error is unwound
        (offset by errors in the other direction).
        The specific problem is the excess overshooting.
        """
        self.windup_guard = windup
        """This is the required setpoint for the PID controller"""
        self.setpoint = setpoint
        
        self.clear()
    
    def updateCommand(self, setpoint = 40.0):
        self.setpoint = setpoint
    
    def update(self, feedback_value, current_time=None):
        """Calculates PID value for given reference feedback
        .. math::
            u(t) = K_p e(t) + K_i \int_{0}^{t} e(t)dt + K_d {de}/{dt}
        """
        
        self.current_time = current_time if current_time is not None else time()
        delta_time = self.current_time - self.last_time

        if delta_time >= self.sample_time:
            error = (self.setpoint - feedback_value) * self.sign
            delta_error = error - self.last_error
            
            self.PTerm = self.Kp * error
            self.ITerm += error * delta_time

            if self.ITerm < -self.windup_guard:
                self.ITerm = -self.windup_guard
            elif self.ITerm > self.windup_guard:
                self.ITerm = self.windup_guard

            self.DTerm = 0.0
            if delta_time > 0:
                self.DTerm = delta_error / delta_time

            # Remember last time and last error for next calculation
            self.last_time = self.current_time
            self.last_error = error

            self.output = self.PTerm + (self.Ki * self.ITerm) + (self.Kd * self.DTerm)
            if self.output > self.outputmax:
                self.output = self.outputmax
            elif self.output < self.outputmin:
                self.output = self.outputmin
                
            # Update for direction, if < 0 then reset
            if self.direction * error < 0:
                self.ITerm = 0.0
                self.output = self.outputmin
                
            #print("s:",self.setpoint,",f:",feedback_value,",e:",error,",P:",self.PTerm,",I:",self.Ki*self.ITerm,",D:",self.Kd*self.DTerm,",O:",self.output)
        return self.output
        
######################### MAIN ##########################
if __name__ == "__main__":
    pass
