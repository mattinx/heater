#!/usr/bin/python
"""Heater control main application"""

import time
import wiringpi2
import w1therm


# Default setpoint (in C) in event nothing exists in the control file
DEFAULT_SETPOINT = 21

# Minimum duration between heater on/off cycle (seconds)
MIN_DURATION = 30

# Heater GPIO pin for HIGH element
GPIO_HIGH = 6

# Heater GPIO pin for LOW element and FAN
GPIO_LOW = 6

# ID of sensors
sensorids = ['28-000005e2fdc3']


class Heater(object):
    """Class to represent two element heater"""
    def __init__(self, lowpin, highpin):
        self.__lowpin = lowpin
        self.__highpin = highpin
        wiringpi2.pinMode(lowpin, 1)
        wiringpi2.pinMode(highpin, 1)
        self.__state = 'off'
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
            wiringpi2.digitalWrite(self.__lowpin, 0)
            self.__state = 'low'
        elif s == "2" or s == "hi" or s == "high" or s == "on":
            wiringpi2.digitalWrite(self.__highpin, 0)
            wiringpi2.digitalWrite(self.__lowpin, 0)
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
        """Tuen off heater"""
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
        temperature = -999
    return temperature

wiringpi2.wiringPiSetupGpio()

sensors = []
for sid in sensorids:
    sensor = w1therm.OWTemp(sid)
    sensors.append(sensor)

if len(sensors) == 0:
    print "No temperature sensors defined"
    exit(1)

setpoint = DEFAULT_SETPOINT
heater = Heater(GPIO_LOW, GPIO_HIGH)

lastcheck = time.time()
while True:
    templist = []
    for a in range(0, 9):
        gt = gettemp(sensors)
        if gt != -999:
            templist.append(gettemp(sensors))
            time.sleep(1)
    if len(templist) == 0:
        print "Error getting temperature for all attempts"
        heater.off()
        time.sleep(MIN_DURATION)
        continue
    templist.sort()
    temp = templist[len(templist)/2]
    print "Temperatures: ", templist
    print "Average temperature: %f" % temp

    if temp < setpoint and not heater.is_on():
        if (setpoint - temp) > 1:
            heater.high()
        else:
            heater.low()
    elif temp > setpoint and heater.is_on():
        heater.off()

    delay = time.time() - (lastcheck + MIN_DURATION)
    if delay > 0:
        time.sleep(delay)
