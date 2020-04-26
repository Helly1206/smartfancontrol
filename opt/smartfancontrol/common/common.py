# -*- coding: utf-8 -*-
#########################################################
# SERVICE : common.py                                   #
#           Common functions for smartfancontrol        #
#                                                       #
#           I. Helwegen 2020                            #
#########################################################

####################### IMPORTS #########################


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
# Class : common                                        #
#########################################################
class common(object):
    def __init__(self, logger):
        self.logger = logger
    
    def __del__(self):
        pass
    
    def checkgroup(self, mydict, group):
        retval = None
        if group in mydict:
            retval = mydict[group]
        return retval
    
    def checkkey(self, mydict, group, key):
        retval = None
        if group in mydict:
            if key in mydict[group]:
                retval = mydict[group][key]
        return retval
    
    def checkkeydef(self, mydict, group, key, default):
        retval = self.checkkey(mydict, group, key)
        if not retval:
            retval = default
        return retval
    
    def gettype(self, text, txtype = True):
        try:
            retval = int(text)
        except:
            try:
                retval = float(text)
            except:
                if text:
                    if text.lower() == "false":
                        retval = False
                    elif text.lower() == "true":
                        retval = True
                    elif txtype:
                        retval = text
                    else:
                        retval = None
                else:
                    retval = None
                        
        return retval
    
    def settype(self, element):
        retval = ""
        if type(element) == bool:
            if element:
                retval = "true"
            else:
                retval = "false"
        elif element != None:
            retval = str(element)
        
        return retval
    
    
    def loge(self, txt):
        if self.logger:
            self.logger.error(txt)
        else:
            print("ERROR: "+txt)
    
    def logw(self, txt):
        if self.logger:
            self.logger.warning(txt)
        else:
            print("WARNING: "+txt)
            
    def logi(self, txt):
        if self.logger:
            self.logger.info(txt)
        else:
            print(txt)

######################### MAIN ##########################
if __name__ == "__main__":
    pass
