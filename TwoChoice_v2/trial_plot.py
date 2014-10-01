# Plot behavioral results versus trial

import numpy as np, glob
import ArduFSM
import ArduFSM.plot2
import time
import matplotlib.pyplot as plt


# Most recent file
#filename = sorted(glob.glob('ardulines.*'))[-1]
filename = 'out.log'

# Read it
with file(filename) as fi:
    lines = fi.readlines()

# initiate plotter object
plotter = ArduFSM.plot2.PlotterWithServoThrow(
    pos_near=1150, pos_delta=25, servo_throw=1)

# initiate the graphics
plotter.init_handles()

# update once
plotter.update(filename)

# update forever
plotter.update_till_interrupt(filename, interval=1)

