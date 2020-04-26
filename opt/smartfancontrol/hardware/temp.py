# -*- coding: utf-8 -*-
#########################################################
# SERVICE : temp.py                                     #
#           Measures the temperature from:              #
#           * CPU                                       #
#           * HDD                                       #
#           * external                                  #
#           (or function, average or maximum)           #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################
from common.common import common
from subprocess import Popen, PIPE
#########################################################

####################### GLOBALS #########################
MODE_MIN = -1
MODE_AVG = 0
MODE_MAX = 1

ALARM_NONE = 0
ALARM_HIGH = 10
ALARM_CRIT = 100

CPU_TEMP = "/sys/class/thermal/thermal_zone0/temp"
HDD_TEMP = ["smartctl", "-a"]
DEF_EXT_LOC = "/run/temp"
DEF_SHUTDOWN = ["shutdown", "-h", "now"]

MONITOR_SLEEP = 1

ABS_NULL = -273.15

#########################################################

###################### FUNCTIONS ########################

#########################################################

#########################################################
# Class : temp                                          #
#########################################################

"""
<temp> contains settings related to temperature input.
<cpu> Use CPU temperature input. Default is true.
<hdd> Use HDD temperature input. Default is empty. Enter HDD to measure here (/dev/sdx).
<ext> Use external temperature input. Default is empty. Enter temperature file here (/run/tempx).
<mode> is the mode used to read the temperature. Default is MAX. 
    MIN: Use the minimum temperature from all sensors used. 
    AVG: Use the average temperature from all sensors used.
    MAX: Use the maximum temperature from all sensors used.
<Farenheit> Display the temperature in Farenheit. Default is false (temperature is displayed in Celcius)
<AlarmHigh> Temperature to rise a temperature high alarm. Default is 65 Celcius. 
            If Farenheit is selected, then this temperature is in Farenheit.
<AlarmCrit> Temperature to rise a temperature critical alarm. Default is 80 Celcius. 
            If Farenheit is selected, then this temperature is in Farenheit.
<AlarmShutdown> Will the system shutdown at critical temperature. Default is true.
                Alternatively a file/scriptname can be entered here to execute when this alarm occurs.
"""

class temp(common):
    def __init__(self, settings, alarm, logger = None):
        self.alarm = alarm
        self.logger = logger
        common.__init__(self, self.logger)
        
        self.cpu = self.checkkey(settings,'temp','cpu')
        self.hdd = self.checkkey(settings,'temp','hdd')
        self.ext = self.checkkey(settings,'temp','ext')
        if self.ext:
            if type(self.ext) != str:
                self.ext = DEF_EXT_LOC

        mode = self.checkkey(settings,'temp','mode')
        if mode.lower() == 'min':
            self.mode = MODE_MIN
        elif mode.lower() == 'max':
            self.mode = MODE_MAX
        else:
            self.mode = MODE_AVG
            
        self.Farenheit = self.checkkey(settings,'temp','Farenheit')
        self.AlarmHigh = self.checkkey(settings,'temp','AlarmHigh')
        self.AlarmCrit = self.checkkey(settings,'temp','AlarmCrit')
        AlarmShutdown = self.checkkey(settings,'temp','AlarmShutdown')
        if AlarmShutdown:
            if type(AlarmShutdown) == str:
                self.AlarmShutdown = AlarmShutdown.split()
            else:
                self.AlarmShutdown = DEF_SHUTDOWN
        else:
            self.AlarmShutdown = None
        self.temperature = None
        self.curalarm = ALARM_NONE

    def __del__(self):
        pass
    
    def __str__(self):
        return self.print(self.temperature)
    
    def __repr__(self):
        tempstr = "-"
        if self.temperature:
            tempstr = "{:.1f}".format(self.temperature)
        return tempstr
    
    def print(self, temp):
        if not temp:
            if self.Farenheit:
                tempstr = "-'F"
            else:
                tempstr = "-'C"
        else:
            if self.Farenheit:
                tempstr = "{:.1f}'F".format(self.Celcius2Farenheit(temp))
            else:
                 tempstr = "{:.1f}'C".format(temp)
        return tempstr
    
    def update(self):
        Temp = []
        tCPU = self.GetCPUTemp()
        if tCPU:
            Temp.append(tCPU)
        tHDD = self.GetHDDTemp()
        if tHDD:
            Temp.append(tHDD)
        tEXT = self.GetEXTTemp()
        if tEXT:
            Temp.append(tEXT)
        if len(Temp) > 0:
            if self.mode == MODE_MIN:
                self.temperature = min(Temp)   
            elif self.mode == MODE_MAX:
                self.temperature = max(Temp)
            else:
                self.temperature = sum(Temp)/len(Temp)
        else:
            self.temperature = None
        
        return self.temperature, self.getalarm(), tCPU, tHDD, tEXT
    
    def get(self):
        if self.temperature:
            return self.temperature
        else:
            return ABS_NULL
    
    def monitor(self, exitevent):
        print("Monitoring temperature")
        while not exitevent.is_set():
            vals = self.update()
            print("{} [CPU: {}, HDD: {}, EXT: {}] {}".format(self.print(vals[0]), self.print(vals[2]), self.print(vals[3]), self.print(vals[4]), repr(self.alarm)))
            exitevent.wait(MONITOR_SLEEP)
        print("Finished monitoring temperature")
        return
    
    def getalarm(self):
        if self.temperature == None:
            if not self.alarm.get(self.alarm.ALARM_TEMPNONE):
                self.alarm.set(self.alarm.ALARM_TEMPNONE)
                self.alarm.reset(self.alarm.ALARM_TEMPHIGH)
                self.alarm.reset(self.alarm.ALARM_TEMPCRIT)
                self.loge(self.alarm)
            return self.alarm.ALARM_TEMPNONE
        elif self.temperature >= self.AlarmCrit:
            if not self.alarm.get(self.alarm.ALARM_TEMPCRIT):
                self.alarm.set(self.alarm.ALARM_TEMPCRIT)
                self.loge(self.alarm)
                if self.AlarmShutdown:
                    self.loge("Shutting down system")
                    try:
                        Popen(self.AlarmShutdown)
                    except:
                        self.loge("Shutdown failed, system may overheat !!!!!")
                else:
                    self.loge("No shutdown intended, system may overheat !!!!!")
            return self.alarm.ALARM_TEMPCRIT
        elif self.temperature >= self.AlarmHigh:
            if not self.alarm.get(self.alarm.ALARM_TEMPHIGH):
                self.alarm.set(self.alarm.ALARM_TEMPHIGH)
                self.alarm.reset(self.alarm.ALARM_TEMPCRIT)
                self.logw(self.alarm)
            return self.alarm.ALARM_TEMPHIGH
        else:
            self.alarm.reset(self.alarm.ALARM_TEMPNONE)
            self.alarm.reset(self.alarm.ALARM_TEMPHIGH)
            self.alarm.reset(self.alarm.ALARM_TEMPCRIT)
            return self.alarm.ALARM_NONE
    
    def GetCPUTemp(self):
        if self.cpu:
            try:
                with open(CPU_TEMP,"r") as f:
                    CPUTemp = float(f.read())/1000.0
                return CPUTemp
            except:
                return None
        else:
            return None    
        
    def GetHDDTemp(self):
        #sudo smartctl -A /dev/sda | grep Temperature_Celsius | awk '{print $10}'
        ####194 Temperature_Celsius     0x0022   117   107   000    Old_age   Always       -       30
        if self.hdd:
            try:
                HDDTemp = None
                for line in Popen(HDD_TEMP + [str(self.hdd)], stdout=PIPE).stdout.read().decode("utf-8").split('\n'):
                    if ('Temperature_Celsius' in line.split()) or ('Temperature_Internal' in line.split()) or ('Airflow_Temperature_Cel' in line.split()):
                        HDDTemp = float(line.split()[9])
                return HDDTemp
            except:
                return None
        else:
            return None
    
    def GetEXTTemp(self):
        if self.ext:
            try:
                with open(self.ext,"r") as f:
                    EXTTemp = float(f.read())
                return EXTTemp
            except:
                return None
        else:
            return None
        
    def Celcius2Farenheit(self, tempc):
        return tempc * 1.8 + 32

######################### MAIN ##########################
if __name__ == "__main__":
    pass
