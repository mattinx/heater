#!/usr/bin/python
"""Heater control main application"""

import time
import wiringpi2
import w1therm


# Default setpoint (in C) in event nothing exists in the control file
DEFAULT_SETPOINT = 25.0

# Minimum duration between heater on/off cycle (seconds)
MIN_DURATION = 15

# Temperature hysteresis value - temp will be kept at +/- this
TEMP_HYST = 0.5

# Switch from high to low when temperature is within this value of setpoint
HIGHLOW_THRESH = 1.5

# Heater GPIO pin for HIGH element
GPIO_HIGH = 5

# Heater GPIO pin for LOW element and FAN
GPIO_LOW = 4

# ID of sensors
sensorids = ['28-000006db9c2a']


class Heater(object):
    """Class to represent two element heater"""
    def __init__(self, lowpin, highpin):
        self.__lowpin = lowpin
        self.__highpin = highpin
        wiringpi2.pinMode(lowpin, 1)
        wiringpi2.pinMode(highpin, 1)
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
        temperature = -999
    return temperature


def setup():
    """Configure hardware"""
    wiringpi2.wiringPiSetup()


def main():
    """ Main loop"""
    sensors = []
    for sid in sensorids:
        sensor = w1therm.OWTemp(sid)
        sensors.append(sensor)

    if len(sensors) == 0:
        print "No temperature sensors defined"
        exit(1)

    setpoint = DEFAULT_SETPOINT
    temphyst = TEMP_HYST
    hilowthresh = HIGHLOW_THRESH
    heater = Heater(GPIO_LOW, GPIO_HIGH)

    print "Target temperature: %fC" % setpoint

    try:
        while True:
            startcheck = time.time()
            templist = []
            for a in range(0, 9):  # pylint: disable=unused-variable
                gt = gettemp(sensors)
                if gt != -999:
                    templist.append(gettemp(sensors))
                    time.sleep(1)
            if len(templist) == 0:
                print "Error getting temperature for all attempts"
                heater.off()
                time.sleep(MIN_DURATION)
                continue
            print "Temperatures: ", templist
            templist.sort()
            temp = templist[len(templist)/2]
            print "Median temperature: %f" % temp

            if temp < (setpoint - temphyst) and not heater.is_on():
                if (setpoint - temp) > hilowthresh:
                    heater.high()
                else:
                    heater.low()
            elif temp > (setpoint + temphyst) and heater.is_on():
                heater.off()

            delay = time.time() - (startcheck + MIN_DURATION)
            if delay > 0:
                print "Next check in %d seconds" % (delay)
                time.sleep(delay)
    except:
        raise
    finally:
        heater.off()

if __name__ == "__main__":
    setup()
    main()
