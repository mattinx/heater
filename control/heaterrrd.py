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
        rrdtool.create(RRDPATH,
                       '--step', '60',
                       '--no-overwrite',
                       'DS:temp:GAUGE:300:0:35',
                       'DS:setpoint:GAUGE:300:0:35',
                       'DS:heat:GAUGE:300:0:2',
                       'RRA:AVERAGE:0.5:1m:1d',
                       'RRA:AVERAGE:0.5:15m:1w',
                       'RRA:AVERAGE:0.5:1h:1M',
                       'RRA:AVERAGE:0.5:1d:1y')


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
    rrddata = "N:%f:%f:%d" % (temp, setpoint, heat)
    rrdtool.update(RRDPATH, rrddata)


if __name__ == "__main__":
    setup()
    main()
