#!/usr/bin/python
"""Heater control main application"""
# pylint: disable=line-too-long

import json
import wiringpi

###
# System configuration
###

# GPIO pin for ON button
GPIO_BTN_ON = 23

# GPIO pin for OFF button
GPIO_BTN_OFF = 21

# GPIO pin for heater status LED
GPIO_LED_ONOFF = 29

# Path to status file
STATUS_FILE = '/dev/shm/heater-status'

# Path to control file
CONTROL_FILE = '/dev/shm/heater-control'

# Group and permissions for the control file
CONTROL_GROUP = 'www-data'
CONTROL_PERMS = 0666

###
# End system configuration
###


def setup():
    """Configure hardware"""
    wiringpi.wiringPiSetup()
    wiringpi.pinMode(GPIO_BTN_ON, 0)  # Set as input
    wiringpi.pullUpDnControl(GPIO_BTN_ON, 2)  # Pull-up
    wiringpi.pinMode(GPIO_BTN_OFF, 0)
    wiringpi.pullUpDnControl(GPIO_BTN_OFF, 2)
    wiringpi.pinMode(GPIO_LED_ONOFF, 1)  # Set as output
    wiringpi.digitalWrite(GPIO_LED_ONOFF, 0)


def getheatersettings():
    """Read settings from file"""
    default = {"highlowthresh": 0.75,
               "temphyst": 0.33,
               "elements": "auto",
               "run": "off",
               "setpoint": 20.0,
               "minduration": 15}
    try:
        fd = open(CONTROL_FILE, "r")
        settings = json.load(fd)
        fd.close()
    except IOError:
        print "Error reading control file"
        return default
    except ValueError:
        print "Error parsing json from control file"
        return default
    return settings


def saveheatersettings(settings):
    """Save settings to file"""
    try:
        fd = open(CONTROL_FILE, "w")
        json.dump(settings, fd)
        fd.close()
    except IOError:
        print "Error writing control file"
        return False
    return True


def getheaterstate():
    """Read status from file"""
    default = {"heater": "off",
               "setpoint": 21.0,
               "run": "auto",
               "temperature": -999}
    try:
        fd = open(STATUS_FILE, "r")
        state = json.load(fd)
        fd.close()
    except IOError:
        print "Error reading state file"
        return default
    except ValueError:
        print "Error parsing json from state file"
        return default
    return state


def main():
    """ Main loop"""
    setup()
    btn = {'on': 1, 'off': 1}
    count = 0
    while True:
        state = getheaterstate()
        settings = getheatersettings()
        btn['on'] = wiringpi.digitalRead(GPIO_BTN_ON)
        btn['off'] = wiringpi.digitalRead(GPIO_BTN_OFF)
        if btn['off'] == 0:
            print "Turn off..."
            settings['run'] = "off"
            saveheatersettings(settings)
        elif btn['on'] == 0:
            print "Turn on..."
            settings['run'] = "auto"
            saveheatersettings(settings)
        if settings['run'] == state['run']:
            if settings['run'] == "off":
                wiringpi.digitalWrite(GPIO_LED_ONOFF, 0)
            else:
                wiringpi.digitalWrite(GPIO_LED_ONOFF, 1)
        else:
            if settings['run'] == "off":
                if count < 4:
                    wiringpi.digitalWrite(GPIO_LED_ONOFF, 1)
                else:
                    wiringpi.digitalWrite(GPIO_LED_ONOFF, 0)
            else:
                if count < 12:
                    wiringpi.digitalWrite(GPIO_LED_ONOFF, 1)
                else:
                    wiringpi.digitalWrite(GPIO_LED_ONOFF, 0)
        count = (count + 1) % 20
        wiringpi.delay(50)

if __name__ == "__main__":
    main()
