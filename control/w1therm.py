#!/usr/bin/python
"""1-wire Temperature Sensor support"""

import random
import time


class OWTemp(object):
    """Represents a 1-wire temperature sensor and access"""
    def __init__(self, sensorid, dummy=False):
        self.__sensorid = sensorid
        self.__path = '/sys/bus/w1/devices/%s/w1_slave' % sensorid
        self.__lastcheck = 0.0
        self.__temp = 999.99
        self.__defaultunit = 'C'
        self.__registers = [0, 0, 0, 0, 0, 255, 0, 16, 0]
        self.__dummy = dummy

    def get_raw(self):
        """Get raw data from 1-wire data file"""
        try:
            fd = open(self.__path, "r")
            lines = fd.readlines()
            fd.close()
        except IOError:
            lines = None
        return lines

    def update(self):
        """Update temperature"""
        if self.__dummy:
            self.__temp = 16 + (random.random() * 10)
            return True
        lines = None
        retries = 10
        success = False
        while not success:
            retries = retries - 1
            if retries == 0:
                return False
            lines = self.get_raw()
            if lines is None or len(lines) < 2:
                print "Output too short"
                time.sleep(0.2)
                continue
            if lines[0].split()[-1] != 'YES':
                print "Bad CRC"
                time.sleep(0.2)
                continue
            regs = []
            for reg in lines[1].split()[0:9]:
                regs.append(int(reg, 16))
            t = lines[1].split('=')
            if t is None or len(t) > 2:
                print "Unable to split out temp"
                time.sleep(0.2)
                continue
            success = True
        self.__registers = regs
        self.__temp = float(t[1]) / 1000.00
        # print "Temperature: %f" % self.__temp
        return True

    def getid(self):
        """Returns 1-wire ID for this sensor"""
        return self.__sensorid

    def getpath(self):
        """Returns filesystem path used to access sensor"""
        return self.__path

    def gettemp(self, unit=None):
        """Return temperture"""
        if (time.time() - self.__lastcheck) > 0.5:
            self.update()
        if unit is None:
            unit = self.__defaultunit.upper()
        if str(unit).upper() == 'C':
            return self.__temp
        elif str(unit).upper() == 'F':
            return self.__temp * 9.0 / 5.0 + 32.0
        else:
            return None
