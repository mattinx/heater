#!/usr/bin/python
"""Read heater status and update rrd"""

import json
import os
import rrdtool

###
# Settings
###

# Path to heater-status file
HEATER_STATUS = "/dev/shm/heater-status"

# Path to rrd
RRDPATH = "heater.rrd"


def setup():
    """Setup files"""
    if not os.access(RRDPATH, os.F_OK):
        print "Creating RRD"
        rrdtool.create(RRDPATH,
                       '--step', '1m',
                       'DS:temp:GAUGE:300:0:35',
                       'DS:setpoint:GAUGE:300:0:35',
                       'DS:heat:GAUGE:300:0:2',
                       'RRA:AVERAGE:0.5:1:1440',
                       'RRA:AVERAGE:0.5:15:672',
                       'RRA:AVERAGE:0.5:60:744',
                       'RRA:AVERAGE:0.5:1440:365')

def main():
    """Collect data and store in rrd"""
    state = json.load(open(HEATER_STATUS, "r"))
    if state['run'] != 'auto':
        setpoint = 'U'
    else:
        setpoint = state['setpoint']
    temp = state['temperature']
    if state['heater'] == "high":
        heat = 2
    elif state['heater'] == "low":
        heat = 1
    else:
        heat = 0
    rrddata = "N:%s:%s:%s" % (str(temp), str(setpoint), str(heat))
    print rrddata
    rrdtool.update(RRDPATH, rrddata)


if __name__ == "__main__":
    setup()
    main()
