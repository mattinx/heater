#!/usr/bin/python
"""Heater control main application"""
# pylint: disable=line-too-long

import json
import os
import sys
import time
import wiringpi2

import w1therm

###
# Default settings
###

settings = dict()

# Default setpoint (in C) in event nothing exists in the control file
settings['setpoint'] = 25.0

# Minimum duration between heater on/off cycle (seconds)
settings['minduration'] = 15

# Temperature hysteresis value - temp will be kept at +/- this
settings['temphyst'] = 0.5

# Switch from high to low when temperature is within this value of setpoint
settings['highlowthresh'] = 1.5

# Startup state for heater: automantic, continuous (to TEMP_MAX), or off
# Valid settings: auto, cont, off
settings['run'] = 'auto'

# Use heater on automatic high/low, high only, or low only
# Valid settings: auto, high, low
settings['elements'] = 'auto'

###
# End default settings
###

###
# System configuration
###

# Heater GPIO pin for HIGH element
GPIO_HIGH = 5

# Heater GPIO pin for LOW element and FAN
GPIO_LOW = 4

# ID of sensors
sensorids = ['28-000006db9c2a']

# Path to status file
STATUS_FILE = '/dev/shm/heater-status'

# Path to control file
CONTROL_FILE = '/dev/shm/heater-control'

# Minimum temperature for setpoint
TEMP_MIN = 0

# Maximum temperature for setpoing
TEMP_MAX = 30

# Absolute minimum duration that heater to be turned on for
MIN_DURATION = 5

###
# End system configuration
###


class Heater(object):
    """Class to represent two element heater"""
    def __init__(self, lowpin, highpin):
        self.__lowpin = lowpin
        self.__highpin = highpin
        wiringpi2.pinMode(lowpin, 1)
        wiringpi2.pinMode(highpin, 1)
        self.__state = 'undefined'
        self.setstate('off')

    def getstate(self):
        """Accessor for state"""
        return self.__state

    def setstate(self, state):
        """Modifier for state"""
        s = str(state).lower()
        print "Set heater: %s" % s
        if s == "0" or s == "off":
            wiringpi2.digitalWrite(self.__highpin, 0)
            wiringpi2.digitalWrite(self.__lowpin, 0)
            self.__state = 'off'
        elif s == "1" or s == "lo" or s == "low":
            wiringpi2.digitalWrite(self.__highpin, 0)
            wiringpi2.digitalWrite(self.__lowpin, 1)
            self.__state = 'low'
        elif s == "2" or s == "hi" or s == "high" or s == "on":
            wiringpi2.digitalWrite(self.__highpin, 1)
            wiringpi2.digitalWrite(self.__lowpin, 1)
            self.__state = 'high'
        return

    def is_on(self):
        """Return bool to represent if heater is on"""
        if self.__state == "off":
            return False
        else:
            return True

    def high(self):
        """Turn heater on high"""
        self.setstate("high")

    def low(self):
        """Turn heater on low"""
        self.setstate("low")

    def off(self):
        """Turn off heater"""
        self.setstate("off")


def gettemp(sensorlist):
    """Get average temperature from sensors"""
    temps = []
    for s in sensorlist:
        t = s.gettemp()
        if t is not None:
            temps.append(t)
    temperature = 0
    for t in temps:
        temperature = temperature + t
    if len(temps) > 0:
        temperature = float(temperature) / len(temps)
    else:
        temperature = None
    return temperature


def getmediantemp(sensors, attempts):
    """
    Query every sensor in sensors attempts times
    Return the median temperature
    """
    print "Begin temperature check"
    templist = []
    for a in range(0, attempts):  # pylint: disable=unused-variable
        gt = gettemp(sensors)
        if gt is not None:
            templist.append(gettemp(sensors))
            time.sleep(1)
    if len(templist) == 0:
        print "Error getting temperature for all attempts"
        return None
    print "Temperatures: ", templist
    templist.sort()
    temp = templist[len(templist)/2]
    print "Median temperature: %f" % temp
    return temp


def writestate(heater, temp):
    """Dump current status to file"""
    state = dict()
    if temp is None:
        state['temperature'] = -999
    else:
        state['temperature'] = temp
    state['run'] = settings['run']
    state['heater'] = heater.getstate()
    try:
        fd = open(STATUS_FILE, "w")
        json.dump(state, fd)
        fd.write('\n')
        fd.close()
    except IOError:
        print "Error writing status file"


def writesettings():
    """Dump current settings to file"""
    try:
        fd = open(CONTROL_FILE, "w")
        json.dump(settings, fd)
        fd.write('\n')
        fd.close()
    except IOError:
        print "Error writing control file"


def updatesettings():
    """Read control file and apply any changes to settings"""
    try:
        fd = open(CONTROL_FILE, "r")
        newsettings = json.load(fd)
        fd.close()
    except IOError:
        print "Error reading control file"
        writesettings()
        return
    try:
        setpoint = float(newsettings['setpoint'])
        minduration = int(newsettings['minduration'])
        temphyst = float(newsettings['temphyst'])
        highlowthresh = float(newsettings['highlowthresh'])
        run = str(newsettings['run']).lower()
        elements = str(newsettings['elements']).lower()
    except ValueError:
        print "Error parsing control file"
        return

    needwrite = False
    if(setpoint < TEMP_MIN):
        print "Setpoint %f too low, setting to min: %f" % (setpoint, TEMP_MIN)
        setpoint = TEMP_MIN
        needwrite = True
    elif(setpoint > TEMP_MAX):
        print "Setpoint %f too high, setting to max: %f" % (setpoint, TEMP_MAX)
        setpoint = TEMP_MAX
        needwrite = True
    if(minduration < MIN_DURATION):
        print "Minimum duration %d too short, setting to min: %d" % (minduration, MIN_DURATION)  # noqa
        minduration = MIN_DURATION
        needwrite = True
    if(temphyst < 0):
        print "Negative hysterisis value %f is invalid, setting to 0" % (temphyst)  # noqa
        temphyst = 0
        needwrite = True
    if(highlowthresh < 0):
        print "Negative high/low threshold value %f is invalid, setting to 0" % (highlowthresh)  # noqa
        highlowthresh = 0
        needwrite = True
    if(run not in ['off', 'cont', 'auto']):
        print "Invalud run state: %s: Setting to off" % (run)
        run = 'off'
        needwrite = True
    if(elements not in ['auto', 'high', 'low']):
        print "Invalud elements state: %s: Setting to auto" % (elements)
        elements = 'auto'
        needwrite = True

    settings['setpoint'] = setpoint
    settings['setpoint'] = setpoint
    settings['minduration'] = minduration
    settings['temphyst'] = temphyst
    settings['highlowthresh'] = highlowthresh
    settings['run'] = run
    settings['elements'] = elements

    if needwrite:
        writesettings()

    return


def setup():
    """Configure hardware"""
    wiringpi2.wiringPiSetup()
    try:
        if not os.access(CONTROL_FILE, os.F_OK):
            fd = open(CONTROL_FILE, "w")
            fd.close()
    except IOError:
        print "Error accessing control file: %s" % CONTROL_FILE
        sys.exit(1)
    writesettings()
    try:
        if not os.access(STATUS_FILE, os.F_OK):
            fd = open(STATUS_FILE, "w")
            fd.close()
    except IOError:
        print "Error accessing control file: %s" % CONTROL_FILE
        sys.exit(1)


def main():
    """ Main loop"""
    setup()

    sensors = []
    for sid in sensorids:
        sensor = w1therm.OWTemp(sid)
        sensors.append(sensor)

    if len(sensors) == 0:
        print "No temperature sensors defined"
        exit(1)

    heater = Heater(GPIO_LOW, GPIO_HIGH)

    print "Target temperature: %fC" % settings['setpoint']
    temp = getmediantemp(sensors, 9)
    print "Current temperature: %fC" % temp
    if temp is None:
        temp = -999
    writestate(heater, temp)

    try:
        print "Starting main loop"
        while True:
            startcheck = time.time()

            updatesettings()

            if settings['run'] == "off":
                if heater.is_on():
                    heater.off()
                time.sleep(1)
                continue

            temp = getmediantemp(sensors, 9)
            if temp is None:
                heater.off()
            else:
                if settings['run'] == "auto":
                    temphyst = settings['temphyst']
                    setpoint = settings['setpoint']
                elif settings['run'] == "cont":
                    temphyst = 1
                    setpoint = TEMP_MAX - temphyst
                else:
                    # This shouldn't be reached during normal operation
                    time.sleep(1)
                    continue

                if (temp < (setpoint - temphyst)) and not heater.is_on():
                    if (settings['elements'] == 'high') or (
                            (settings['elements'] == "auto") and (
                                (setpoint - temp) > settings['highlowthresh']
                                )):
                        heater.high()
                    else:
                        heater.low()
                elif (temp > (setpoint + temphyst)) and heater.is_on():
                    heater.off()

            writestate(heater, temp)

            print "Check took %d seconds" % (time.time() - startcheck)
            delay = settings['minduration'] - (time.time() - startcheck)
            if delay > 0:
                print "Next check in %d seconds" % (delay)
                time.sleep(delay)
    except:
        raise
    finally:
        heater.off()
        writestate(heater, temp)

if __name__ == "__main__":
    main()
