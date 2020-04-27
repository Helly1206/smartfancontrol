#!/usr/bin/python3

# -*- coding: utf-8 -*-
#########################################################
# SCRIPT : smartfancontrol.py                           #
#          Controls a raspberry PI temperature with a   #
#          fan                                          #
#          I. Helwegen 2020                             #
#########################################################

####################### IMPORTS #########################
import sys
import os
try:
    import pigpio
    ifinstalled = True                     
except ImportError:
    ifinstalled = False
import signal
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from getopt import getopt, GetoptError
import logging
import logging.handlers
import locale
from threading import Lock, Event
from common.common import common
from common.alarm import alarm
from hardware.fanoutput import fanoutput
from hardware.rpm import rpm
from hardware.temp import temp
from engine.fanctrl import fanctrl
from engine.tempctrl import tempctrl
#########################################################

####################### GLOBALS #########################
VERSION          = "0.81"
XML_FILENAME     = "smartfancontrol.xml"
LOG_FILENAME     = "smartfancontrol.log"
LOG_MAXSIZE      = 100*1024*1024
ENCODING         = 'utf-8'
MODE_RUN         = 0
MODE_MANUALCAL   = 1
MODE_TEMP        = 2
MODE_FAN         = 3
MODE_AUTOTUNEFAN = 4
MODE_DETERMINE   = 5
#########################################################

###################### FUNCTIONS ########################

#########################################################
# Class : SmartFanControl                               #
#########################################################
class SmartFanControl(common):
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_app)
        signal.signal(signal.SIGTERM, self.exit_app)
        self.exitevent = Event()
        self.exitevent.clear()
        self.logger = logging.getLogger('smartfancontrol')
        self.logger.setLevel(logging.INFO)
        # create file handler which logs even debug messages
        fh = logging.handlers.RotatingFileHandler(self.GetLogger(), maxBytes=LOG_MAXSIZE, backupCount=5)
        # create console handler with a higher log level
        ch = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        logging.captureWarnings(True)
        tmformat=("{} {}".format(locale.nl_langinfo(locale.D_FMT),locale.nl_langinfo(locale.T_FMT)))
        tmformat=tmformat.replace("%y", "%Y")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s', tmformat)
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        self.settings = {}
        self.alarm = alarm()
        
        common.__init__(self, self.logger)
        
        self.pi = None
        if ifinstalled:
            self.pi = pigpio.pi()
        self.mutex = Lock()
        self.fanoutput = None
        self.rpm = None
        self.temp = None
        self.fanctrl = None
        self.tempctrl = None

    def __del__(self):
        del self.tempctrl
        del self.fanctrl
        del self.temp
        del self.rpm
        del self.fanoutput
        del self.alarm
        if ifinstalled:
            self.pi.stop()
            del self.pi
        logging.shutdown()

    def run(self, argv):
        mode, monstatus = self.parseopts(argv)
        self.GetXML()
        if mode == MODE_MANUALCAL or mode == MODE_TEMP: # no auto calibration
            autocalibrate = False
        else:
            autocalibrate = True
        self.fanoutput = fanoutput(self.pi, self.settings)
        self.rpm = rpm(self.pi, self.settings)
        self.temp = temp(self.settings, self.alarm, self.logger)
        self.fanctrl = fanctrl(self.rpm, self.fanoutput, self.mutex, self.settings, self.alarm, self.logger, self.exitevent, autocalibrate)
        self.tempctrl = tempctrl(self.fanctrl, self.temp, self.settings, self.alarm, self.logger, self.exitevent, monstatus)
        
        if mode == MODE_MANUALCAL:
            self.settings['fan']['PWMcalibrated'] = self.fanctrl.manualCalibrate()
            self.updateXML()
            self.fanctrl.exit()
            self.fanoutput.exit()
            exit(2)
        elif mode == MODE_TEMP:
            self.temp.monitor(self.exitevent)
            self.fanctrl.exit()
            self.fanoutput.exit()
            exit(3)
        elif mode == MODE_FAN:
            self.fanctrl.start()
            self.fanctrl.manual()
            self.fanctrl.exit()
            self.fanoutput.exit()
            exit(4)
        elif mode == MODE_AUTOTUNEFAN:
            #self.fanctrl.start()
            Ok, Kp, Ki = self.fanctrl.RPMautotune()
            if Ok:
                self.settings['fan']['Pgain'] = Kp
                self.settings['fan']['Igain'] = Ki
                self.updateXML()
            self.fanctrl.exit()
            self.fanoutput.exit()
            exit(5)
        elif mode == MODE_DETERMINE:
            Ok, Kp, Ki = self.tempctrl.determine()
            if Ok:
                self.settings['control']['Pgain'] = Kp
                self.settings['control']['Igain'] = Ki
                self.updateXML()
            self.fanctrl.exit()
            self.fanoutput.exit()
            exit(5)
        
        self.logger.info("Starting SmartFanControl")

        if not self.exitevent.is_set():
            self.fanctrl.start()
            self.tempctrl.start()
            signal.pause()
        
        self.logger.info("SmartFanControl Ready")
        self.tempctrl.exit()
        self.fanctrl.exit()
        self.fanoutput.exit()        
        
    def parseopts(self, argv):
        mode = MODE_RUN
        monstatus = False
        self.title()
        try:
            opts, args = getopt(argv,"hvctfadm,",["help","version","cal","temp","fan","auto","dtrmn","mon"])
        except GetoptError:
            print("Enter 'smartfancontrol -h' for help")
            exit(2)
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print("Usage:")
                print("         smartfancontrol <args>")
                print("         -h, --help   : this help file")
                print("         -v, --version: print version information")
                print("         -c, --cal    : manually calibrate PWM level and exit")
                print("         -t, --temp   : Monitor temperature(s)")
                print("         -f, --fan    : Set fan PWM or RPM for testing")
                print("         -a, --auto   : Autotune fan PI controller (RPM control)")
                print("         -d, --dtrmn  : Determine temperature PI controller optimum parameters")
                print("         -m, --mon    : Monitor actual status in terminal")
                print("         <no argument>: run as daemon")
                exit()
            elif opt in ("-v", "--version"):
                print("Version: " + VERSION)
                exit()
            elif opt in ("-c", "--cal"):
                mode = MODE_MANUALCAL
            elif opt in ("-t", "--temp"):
                mode = MODE_TEMP
            elif opt in ("-f", "--fan"):
                mode = MODE_FAN
            elif opt in ("-a", "--auto"):
                mode = MODE_AUTOTUNEFAN
            elif opt in ("-d", "--dtrmn"):
                mode = MODE_DETERMINE
            elif opt in ("-m", "--mon"):
                monstatus = True
        return mode, monstatus
        
    def GetXML(self):
        XMLpath = self.getXMLpath()
        try:         
            tree = ET.parse(XMLpath)
            root = tree.getroot()
            self.settings = {}
        
            for child in root:
                childdict={}
                childname=child.tag
                for toy in child:
                    childdict[toy.tag]=self.gettype(toy.text)
                self.settings[childname]=childdict
                
        except Exception as e:
            self.logger.error("Error parsing xml file")
            self.logger.error("Check XML file syntax for errors")
            self.logger.exception(e)
            exit(1)
            
    def updateXML(self):
        settings = ET.Element('settings')
        comment = ET.Comment(self.getXMLcomment("settings"))
        settings.append(comment)
        for key, value in self.settings.items():
            child = ET.SubElement(settings, key)
            for key, value in value.items():
                toy = ET.SubElement(child, key)
                toy.text = self.settype(value)
        #print(self.prettify(settings))
    
        XMLpath = self.getXMLpath()
        with open(XMLpath, "w") as xml_file:
            xml_file.write(self.prettify(settings))
    
    def getXMLcomment(self, tag):
        comment = ""
        XMLpath = self.getXMLpath()
        with open(XMLpath, 'r') as xml_file:
            content = xml_file.read()
            xmltag = "<{}>".format(tag)
            xmlend = "</{}>".format(tag)
            begin = content.find(xmltag)
            end = content.find(xmlend)
            content = content[begin:end]
            cmttag = "<!--"
            cmtend = "-->"
            begin = content.find(cmttag)
            end = content.find(cmtend)
            if (begin > -1) and (end > -1):
                comment = content[begin+len(cmttag):end]
        return comment
    
    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(elem, ENCODING)
        reparsed = parseString(rough_string)
        return reparsed.toprettyxml(indent="\t").replace('<?xml version="1.0" ?>','<?xml version="1.0" encoding="%s"?>' % ENCODING)
    
    def getXMLpath(self):
        etcpath = "/etc/"
        XMLpath = ""
        # first look in etc
        if os.path.isfile(os.path.join(etcpath,XML_FILENAME)):
            XMLpath = os.path.join(etcpath,XML_FILENAME)
        else:
            # then look in home folder
            if os.path.isfile(os.path.join(os.path.expanduser('~'),XML_FILENAME)):
                XMLpath = os.path.join(os.path.expanduser('~'),XML_FILENAME)
            else:
                # look in local folder, hope we may write
                if os.path.isfile(os.path.join(".",XML_FILENAME)):
                    if os.access(os.path.join(".",XML_FILENAME), os.W_OK):
                        XMLpath = os.path.join(".",XML_FILENAME)
                    else:
                        self.logger.error("No write access to XML file")
                        exit(1)
                else:
                    self.logger.error("No XML file found")
                    exit(1)
        return XMLpath           
    
    def title(self):
        print("SmartFanControl fan and temperature control")
        print("Version: " + VERSION)
        print(" ")
    
    def GetLogger(self):
        logpath = "/var/log"
        LoggerPath = ""
        # first look in log path
        if os.path.exists(logpath):
            if os.access(logpath, os.W_OK):
                LoggerPath = os.path.join(logpath,LOG_FILENAME)
        if (not LoggerPath):
            # then look in home folder
            if os.access(os.path.expanduser('~'), os.W_OK):
                LoggerPath = os.path.join(os.path.expanduser('~'),LOG_FILENAME)
            else:
                print("Error opening logger, exit SmartFanControl")
                exit(1) 
        return (LoggerPath)
        
    def exit_app(self, signum, frame):
        self.exitevent.set()
#########################################################

######################### MAIN ##########################
if __name__ == "__main__":
    SmartFanControl().run(sys.argv[1:])