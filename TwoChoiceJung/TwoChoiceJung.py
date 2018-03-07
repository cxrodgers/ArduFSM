# Main script to run to run TwoChoice behavior
# Timings: set 'serial_timeout' in chatter, and 'timeout' in UI, to be low
# enough that the response is quick, but not so low that it takes up all the
# CPU power.
# Right now, it does this on each loop
# * Update chatter (timeout)
# * Update UI (timeout)
# * do other things, like reading logfile and setting next trial
# So, if the timeouts are too low, it spends a lot more time reading the
# logfile and there is more overhead overall.

import time
import json
import os
import sys
import os
import numpy as np, pandas
import my
import time
import curses
import matplotlib
matplotlib.rcParams['toolbar'] = 'None'
import matplotlib.pyplot as plt
import ArduFSM
from ArduFSM import TrialSpeak, TrialMatrix
from ArduFSM import trial_setter_ui
from ArduFSM import Scheduler
from ArduFSM import trial_setter
from ArduFSM import mainloop
import ParamsTable
import shutil

def move_figure(f, x, y):
    """Move figure's upper left corner to pixel (x, y)"""
    backend = matplotlib.get_backend()
    if backend == 'TkAgg':
        f.canvas.manager.window.wm_geometry("+%d+%d" % (x, y))
    elif backend == 'WXAgg':
        f.canvas.manager.window.SetPosition((x, y))
    else:
        # This works for QT and GTK
        # You can also use window.setGeometry
        f.canvas.manager.window.move(x, y)
    plt.show()

def get_trial_types(name, directory='~/dev/ArduFSM/stim_sets'):
    """Loads and returns the trial types file"""
    
    filename = os.path.join(os.path.expanduser(directory), name)
    try:
        trial_types = pandas.read_csv(filename)
    except IOError:
        raise ValueError("cannot find trial type file %s" % name)
    return trial_types

# Load the parameters file
with file('parameters.json') as fi:
    runner_params = json.load(fi)

# Check the serial port exists
if not os.path.exists(runner_params['serial_port']):
    raise OSError("serial port %s does not exist" % 
        runner_params['serial_port'])


## Determine how to set up the webcam
# Get controls from runner_params
webcam_controls = {}
for webcam_param in ['brightness', 'gain', 'exposure']:
    rp_key = 'video_' + webcam_param
    if rp_key in runner_params:
        webcam_controls[webcam_param] = runner_params[rp_key]

# Determine whether we can show it
video_device = runner_params.get('video_device', None)
if video_device is None:
    SHOW_WEBCAM = False
else:
    SHOW_WEBCAM = True


## Only show the IR_plot if use_ir_detector
SHOW_IR_PLOT = runner_params.get('use_ir_detector', False)
SHOW_IR_PLOT = False

# sensor plot
SHOW_SENSOR_PLOT = False


## Reward amounts
# Target amount for this mouse (nL)
target_water_volume = runner_params['target_water_volume']
norm_target_water_volume = runner_params['target_water_volume'] / 5000.0

# Clamp
if norm_target_water_volume < .8:
    norm_target_water_volume = .8
if norm_target_water_volume > 1.1:
    norm_target_water_volume = 1.1 

# Typical value for this box (ms)
l_typical = float(runner_params['l_reward_duration'])
r_typical = float(runner_params['r_reward_duration'])

# Sensitivity for this box (normed duration / normed amount)
# Eventually this should be a box parameter
l_sensitivity = .3
r_sensitivity = .3

# Adjusted durations
l_adjustment = l_typical * l_sensitivity * (norm_target_water_volume - 1)
r_adjustment = r_typical * r_sensitivity * (norm_target_water_volume - 1)

# Adjust and convert to int
l_adjusted_duration = int(np.rint(l_typical + l_adjustment))
r_adjusted_duration = int(np.rint(r_typical + r_adjustment))


## Various window positions
video_window_position = runner_params.get('video_window_position', None)
gui_window_position = runner_params.get('gui_window_position', None)
window_position_IR_plot = runner_params.get(
    'window_position_IR_plot', None)

    
## Set up params_table
# First we load the table of protocol-specific parameters that is used by the UI
# Then we assign a few that were set by the runner
params_table = ParamsTable.get_params_table()
params_table.loc['RD_L', 'init_val'] = l_adjusted_duration
params_table.loc['RD_R', 'init_val'] = r_adjusted_duration
params_table.loc['STPHAL', 'init_val'] = 3 if runner_params['has_side_HE_sensor'] else 2
params_table.loc['STPFR', 'init_val'] = runner_params['step_first_rotation']
try:
    params_table.loc['TO', 'init_val'] = runner_params['timeout']
except KeyError:
    pass
if runner_params['use_ir_detector']:
    params_table.loc['TOUT', 'init_val'] = runner_params['l_ir_detector_thresh']    
    params_table.loc['RELT', 'init_val'] = runner_params['r_ir_detector_thresh']   

# Set the current-value to be equal to the init_val
params_table['current-value'] = params_table['init_val'].copy()


## Load the specified trial types
trial_types_name = runner_params['stimulus_set'] + '_r'
trial_types = get_trial_types(trial_types_name)


## User interaction
session_results = {}
# Print out the results from last time
try:
    recent_pipe = float(runner_params['recent_pipe'])
except (ValueError, KeyError):
    recent_pipe = -1.0
try:
    recent_weight = float(runner_params['recent_weight'])
except (ValueError, KeyError):
    recent_weight = -1.0
print "Previously mouse %s weighed %0.1fg and the pipe was at %0.2f" % (
    runner_params['mouse'],
    recent_weight,
    recent_pipe,
    )

# Get weight
session_results['mouse_mass'] = \
    raw_input("Enter mass of %s: " % runner_params['mouse'])

# Get stepper in correct position
if not runner_params['has_side_HE_sensor']:
    # Note this may not be a stimulus we're using in this stimulus set
    raw_input("Rotate stepper to position %s" % 
        params_table.loc['STPIP', 'init_val'])

raw_input("Fill water reservoirs and press Enter to start")

## Set up the scheduler
if runner_params['scheduler'] == 'Auto':
    scheduler_obj = Scheduler.Auto
elif runner_params['scheduler'] == 'ForcedAlternation':
    scheduler_obj = Scheduler.ForcedAlternation

# Do all scheduler objects accept reverse_srvpos?
scheduler = scheduler_obj(trial_types=trial_types, reverse_srvpos=True)


## Create Chatter
logfilename = None # autodate
chatter = ArduFSM.chat.Chatter(to_user=logfilename, to_user_dir='./logfiles',
    baud_rate=115200, serial_timeout=.1, 
    serial_port=runner_params['serial_port'])
logfilename = chatter.ofi.name


## Reset video filename
date_s = os.path.split(logfilename)[1].split('.')[1]
video_filename = os.path.join(os.path.expanduser('~/Videos'), 
    '%s-%s.mkv' % (runner_params['box'], date_s))


## Trial setter
ts_obj = trial_setter.TrialSetter(chatter=chatter, 
    params_table=params_table,
    scheduler=scheduler)

## Initialize UI
RUN_UI = True
RUN_GUI = True
ECHO_TO_STDOUT = not RUN_UI
ui_obj = trial_setter_ui.UI
if RUN_UI:
    ui = ui_obj(timeout=200, chatter=chatter, 
        logfilename=logfilename,
        ts_obj=ts_obj,
        banner='Port: %s. Mouse: %s. Logfile: %s.' % (
            runner_params['serial_port'],
            runner_params['mouse'],
            os.path.split(logfilename)[1],
        ),
    )

    try:
        ui.start()

    except curses.error as err:
        raise Exception(
            "UI error. Most likely the window is, or was, too small.\n"
            "Quit Python, type resizewin to set window to 80x23, and restart.")

    except:
        print "error encountered when starting UI"
        raise
    
    finally:
        ui.close()


## Main loop
final_message = None
try:
    ## Initialize webcam
    if SHOW_WEBCAM:
        window_title = os.path.split(video_filename)[1]
        try:
            wc = my.video.WebcamController(device=video_device, 
                output_filename=video_filename,
                window_title=window_title,
                image_controls=webcam_controls,)
            wc.start()
        except IOError:
            print "cannot find webcam at port", video_device
            wc = None
            SHOW_WEBCAM = False
        except OSError:
            print "something went wrong with webcam process"
            wc = None
            SHOW_WEBCAM = False
    else:
        wc = None
    
    ## Initialize GUI
    if RUN_GUI:
        plotter = ArduFSM.plot.PlotterWithServoThrow(trial_types)
        plotter.init_handles()
        move_figure(plotter.graphics_handles['f'],
            gui_window_position[0], gui_window_position[1])
        
        if SHOW_IR_PLOT:
            plotter2 = ArduFSM.plot.LickPlotter()
            plotter2.init_handles()
            if window_position_IR_plot is not None:
                move_figure(plotter2.handles['f'],
                    window_position_IR_plot[0], window_position_IR_plot[1])
        
        if SHOW_SENSOR_PLOT:
            sensor_plotter = ArduFSM.plot.SensorPlotter()
            sensor_plotter.init_handles()
        
        last_updated_trial = 0
    
    # Move the webcam window once it appears
    if SHOW_WEBCAM:
        cmd = 'xdotool search --name %s windowmove %d %d' % (
            window_title, video_window_position[0], video_window_position[1])
        while os.system(cmd) != 0:
            # Should test here if it's been too long and then give up
            print "Waiting for webcam window"
            time.sleep(.5)
    
    while True:
        ## Chat updates
        # Update chatter
        chatter.update(echo_to_stdout=ECHO_TO_STDOUT)
        
        # Read lines and split by trial
        # Could we skip this step if chatter reports no new device lines?
        logfile_lines = TrialSpeak.read_lines_from_file(logfilename)
        splines = TrialSpeak.split_by_trial(logfile_lines)

        # Run the trial setting logic
        # This try/except is no good because it conflates actual
        # ValueError like sending a zero
        #~ try:
        translated_trial_matrix = ts_obj.update(splines, logfile_lines)
        #~ except ValueError:
            #~ raise ValueError("cannot get any lines; try reuploading protocol")
        
        ## Update UI
        if RUN_UI:
            ui.update_data(logfile_lines=logfile_lines)
            ui.get_and_handle_keypress()

        ## Update GUI
        # Put this in it's own try/except to catch plotting bugs
        if RUN_GUI:
            if last_updated_trial < len(translated_trial_matrix):
                # update plot
                plotter.update(logfilename)     
                last_updated_trial = len(translated_trial_matrix)
            
                if SHOW_SENSOR_PLOT:
                    sensor_plotter.update(logfile_lines)
                
                # When there are multiple figures to show, it can be
                # hard to make it update both of them. this seems to
                # work:
                # https://gist.github.com/rlabbe/ea3444ef48641678d733
                plotter.graphics_handles['f'].canvas.draw()

            if SHOW_IR_PLOT:
                plotter2.update(logfile_lines)
                
                #~ plt.pause(.01)
                plotter2.handles['f'].canvas.draw()
                
            
            plt.pause(.01)
            
                

except KeyboardInterrupt:
    print "Keyboard interrupt received"

except trial_setter_ui.QuitException as qe:
    final_message = qe.message

    rewdict = ArduFSM.plot.count_rewards(splines)
    nlrew = (rewdict['left auto'].sum() + 
        rewdict['left manual'].sum() + rewdict['left direct'].sum())
    nrrew = (rewdict['right auto'].sum() + 
        rewdict['right manual'].sum() + rewdict['right direct'].sum())
    
    # Get volumes and pipe position
    print "Preparing to save. Press CTRL+C to abort save."
    if session_results.get('mouse_mass') in ['', None]:
        session_results['mouse_mass'] = raw_input("Enter mouse mass: ")
    
    choice = 'N'
    while choice.upper().strip() == 'N':
        session_results['l_volume'] = raw_input("Enter L water volume: ")
        session_results['r_volume'] = raw_input("Enter R water volume: ")
        
        bad_data = False
        try:
            if nlrew == 0:
                lmean = 0.
            else:
                lmean = float(session_results['l_volume']) / nlrew
            if nrrew == 0:
                rmean = 0.
            else:
                rmean = float(session_results['r_volume']) / nrrew
        except ValueError:
            print "warning: cannot convert to float"
            bad_data = True
        
        if not bad_data:
            print "L mean: %0.1f; R mean: %0.1f" % (lmean * 1000, rmean * 1000)
            choice = raw_input("Confirm? [Y/n] ")

    session_results['l_valve_mean'] = lmean
    session_results['r_valve_mean'] = rmean
    
    print "Previous pipe position was %s" % recent_pipe
    session_results['final_pipe'] = raw_input("Enter final pipe position: ")
    
    # Dump the results
    logfile_dir = os.path.split(logfilename)[0]
    with file(os.path.join(logfile_dir, 'results'), 'w') as fi:
        json.dump(session_results, fi, indent=4)
    
    # Rename the directory with the mouse name
    def ignore_fifo(src, names):
        return 'TO_DEV'
    session_dir = os.path.split(os.path.split(logfile_dir)[0])[0]
    shutil.copytree(session_dir, session_dir + '-saved', ignore=ignore_fifo)
    final_message += "\n" + "rename %s to %s" % (
        session_dir, session_dir + '-saved')

except curses.error as err:
    raise Exception(
        "UI error. Most likely the window is, or was, too small.\n"
        "Quit Python, type resizewin to set window to 80x23, and restart.")

except:
    raise

finally:
    if SHOW_WEBCAM:
        wc.stop()
        wc.cleanup()
    chatter.close()
    print "chatter closed"
    
    if RUN_UI:
        ui.close()
        print "UI closed"
    
    if RUN_GUI:
        pass
        #~ plt.close(plotter.graphics_handles['f'])
        #~ print "GUI closed"
    
    if final_message is not None:
        print final_message
    


