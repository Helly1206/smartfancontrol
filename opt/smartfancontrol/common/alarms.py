# -*- coding: utf-8 -*-
#########################################################
# SERVICE : alarms.py                                   #
#           Class containing alarm data                 #
#                                                       #
#           I. Helwegen 2020                            #
#########################################################

#########################################################
# Class : alarms                                        #
#########################################################
class alarms:
    #Alarm constants. No alarm should alway be 0!!!
    ALARM_NONE          = 0
    ALARM_TEMPNONE      = 1
    ALARM_TEMPHIGH      = 2
    ALARM_TEMPCRIT      = 3
    ALARM_FANNOTRUNNING = 4
    ALARM_FANNOTMAXRPM  = 5
    ALARM_FANNORPMMODE  = 6
    ALARM_FANCALSTALL   = 7

    #alarmdata: prio, short_string, long_string
    alarmdata = {ALARM_NONE          : (  0,"Ok"              ,"No Alarm"),
                 ALARM_TEMPNONE      : ( 80,"No temperature"  ,"No temperature measured"),
                 ALARM_TEMPHIGH      : ( 90,"High temp"       ,"High temperature reached"),
                 ALARM_TEMPCRIT      : (100,"Critical temp"   ,"Critical temperature reached"),
                 ALARM_FANNOTRUNNING : ( 70,"Fan stalled"     ,"Fan is not running/ stalled"),
                 ALARM_FANNOTMAXRPM  : ( 50,"Fan low RPM"     ,"Fan cannot reach maximum RPM"),
                 ALARM_FANNORPMMODE  : ( 10,"Fan No RPM"      ,"Fan alarm monitoring only possible in RPM mode"),
                 ALARM_FANCALSTALL   : ( 60,"Fan stalled cal" ,"Fan is not running/ stalled during calibration")}

######################### MAIN ##########################
if __name__ == "__main__":
    pass
