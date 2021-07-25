SmartFanControl v0.8.4

SmartFanControl - keep it cool - service containing all in one fan and temperature control
=============== = ==== == ==== = ======= ========== === == === === === =========== =======

pigpio is used for IO to rapsberry pi 

This program can run as systemd service or as stand-alone program.
As systemd service it starts after pigpiod.

The service is completely configurable via smartfancontrol.xml, located in /etc/smartfancontrol.xml.

	This xml file describes the settings for smartfancontrol.
	
	Keep item names as they are, otherwise defaults will be used.

	The parameters can be modified, some parameters are only used in a specific mode:
	<settings> parent group containing settings.
 		<fan> contains settings related to fan control and RPM readout
			<mode> is the mode used to control the fan. Default is RPM. 
				ONOFF: Only on/ off control is used
				PWM: PWM control is used, with no RPM feedback (for fans that don't have this option)
					 Manual calibration is required
				RPM: PWM control with RPM feedback is used. Calibration is performed automatically
			<ONOFFgpio> The GPIO pin for ONOFF control. Defaults to GPIO 27. This pin is used to switch on or
						off the fan in PWM and RPM mode if connected in one of these modes.
			<ONOFFinvert> Invert the ONOFF signal required for some switching hardware. Default is false.
			<PWMcalibrated> is the calibrated PWM percentage where the fan starts running. Default is 30.
							Can be calibrated by runnning smartfancontrol with the argument -c or -cal.
                            Only used in PWM mode and to measure minimum value for autocalibration.
			<PWMgpio> The GPIO pin for PWM control. Defaults to GPIO 18. Take care a hardware PWM
					  compatible pin is chosen.
			<PWMfrequency> The hardware PWM frequency in Hz. Default is 10000.
			<PWMinvert> Invert the PWM signal required for some switching hardware. Default is false.
			<recalibrate> The number of days between automatic calibrations. Default is 7. A calibration 
						  will be performed n days after startup or previous calibration at 12:00 PM.
						  Only used in RPM mode.
			<RPMgpio> The GPIO pin for RPM readout. Defaults to GPIO 17. Only used in RPM mode.
			<RPMpullup> Use internal pullup for RPM GPIO pin. Default is true. Only used in RPM mode.
			<RPMppr> The number of RPM tacho pulses per revolution. Default is 2. Only used in RPM mode.
			<RPMedge> If true, both positive and negative edges are used for RPM measurement. Default is true.
                      Only used in RPM mode.
			<RPMfiltersize> If larger than 1, measured RPMs are filtered by an n-sized moving average filter
							Default is 0. Only used in RPM mode.
			<Frequency> The frequency of the fan control loop in Hz. default is 10.
			<Pgain> The P gain of the fan control loop. Default is 0.1. Only used in RPM mode.
			<Igain> The I gain of the fan control loop. Default is 0.2. Only used in RPM mode.

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

		<control> contains settings related to the temperature controller.
			<mode> is the mode used to control the temperature loop. Default is LINEAR. 
				ONOFF: Only on/ off control is used, if this mode is selected, on/off control will also be used to
					   control the fan.
				LINEAR: If the temperature is within the linear range, the fan speed will increase linear with a
						temperature increase.
				PI: PI temperature control is used.
			<TempOn> The temperature to switch the fan on. Default is 55 Celcius. Only used in ONOFF mode.
					 If Farenheit is selected, then this temperature is in Farenheit.
			<TempHyst> The temperature hysteresis to switch the fan off again. Default is 5 Celcius.
					   Only used in ONOFF mode. If Farenheit is selected, then this temperature is in Farenheit.
			<TempStart> The temperature to start the fan controller. Default is 45 Celcius. 
					    Only used in LINEAR and PI mode. If Farenheit is selected, then this temperature is in Farenheit.
			<TempFull> The temperature on which the fan controller should run full speed. Default is 65 Celcius. 
					   Only used in LINEAR and PI mode. If Farenheit is selected, then this temperature is in Farenheit.
			<LinSteps> The temperature steps/ hysteresis. To provent oscillating on small temperature changes. 
					   Default is 2.5 Celcius. Only used in LINEAR mode. If Farenheit is selected, then this temperature is in Farenheit.
			<Frequency> The frequency of the temperature control loop in Hz. default is 1.
			<Pgain> The P gain of the temperature control loop. Default is 10. Only used in PI mode.
			<Igain> The I gain of the temperature control loop. Default is 0.1. Only used in PI mode.

For testing and tuning the following command line parameters are available. Take care to stop the service before running commandline settings:
sudo systemctl stop smartfancontrol.service

Usage:
         smartfancontrol <args>
         -h, --help   : this help file
         -v, --version: print version information
         -c, --cal    : manually calibrate PWM level and exit
         -t, --temp   : Monitor temperature(s)
         -f, --fan    : Set fan PWM or RPM for testing
         -a, --auto   : Autotune fan PI controller (RPM control)
         -d, --dtrmn  : Determine temperature PI controller optimum parameters
         -m, --mon    : Monitor actual status in terminal
         <no argument>: run as daemon

That's all for now ...

Please send Comments and Bugreports to hellyrulez@home.nl
