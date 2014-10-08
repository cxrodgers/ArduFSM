# Plot behavioral results versus trial

import numpy as np, glob, pandas
import ArduFSM
import ArduFSM.plot2
import time
import matplotlib.pyplot as plt


# Load trial types that were used from disk]
trial_types = pandas.read_pickle('trial_types_2stppos')


# Most recent file
#filename = sorted(glob.glob('ardulines.*'))[-1]
filename = 'out.log'

# Read it
with file(filename) as fi:
    lines = fi.readlines()

# initiate plotter object
plotter = ArduFSM.plot2.PlotterWithServoThrow(trial_types)

# initiate the graphics
plotter.init_handles()

# update once
plotter.update(filename)

# update forever
plotter.update_till_interrupt(filename, interval=1)

