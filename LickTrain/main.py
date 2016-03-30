# Main script to run to run LickTrain_v2 behavior

import sys
import os
import numpy as np, pandas
import my
import time
import curses
import matplotlib.pyplot as plt

# Ardu imports
import ArduFSM
import ArduFSM.chat
import ArduFSM.plot
from ArduFSM import TrialSpeak, TrialMatrix
from ArduFSM import trial_setter_ui
from ArduFSM import Scheduler
from ArduFSM import trial_setter
from ArduFSM import mainloop


## Find out what rig we're in using the current directory
this_dir_name = os.getcwd()
rigname = os.path.split(this_dir_name)[1]
serial_port = mainloop.get_serial_port(rigname)

## Get webcam params
SHOW_WEBCAM = True
if rigname == 'L0':
    SHOW_WEBCAM = False
    video_device = '/dev/video0'
    video_filename = '/dev/null'
elif rigname == 'B1':
    video_device = '/dev/video0'
    video_window_position = 1150, 0
    gui_window_position = 425, 0    
elif rigname == 'B2':
    video_device = '/dev/video1'
    video_window_position = 1150, 260
    gui_window_position = 425, 260    
elif rigname == 'B3':
    video_device = '/dev/video2'
    video_window_position = 1150, 520
    gui_window_position = 425, 520    
elif rigname == 'B4':
    video_device = '/dev/video3'
    video_window_position = 1150, 780
    gui_window_position = 425, 780    

video_filename = None

## Get params
params_table = mainloop.get_params_table_licktrain()
params_table = mainloop.assign_rig_specific_params_licktrain(rigname, params_table)
params_table['current-value'] = params_table['init_val'].copy()

## Upload
if raw_input('Reupload protocol [y/N]? ').upper() == 'Y':
    protocol_name = 'LickTrain_%s' % rigname

    os.system('arduino --board arduino:avr:uno --port %s \
        --pref sketchbook.path=/home/mouse/dev/ArduFSM \
        --upload ~/dev/ArduFSM/%s/%s.ino' % (
        serial_port, protocol_name, protocol_name))

## Get trial types
trial_types = mainloop.get_trial_types('trial_types_licktrain')

## Initialize the scheduler
scheduler = Scheduler.ForcedAlternationLickTrain(trial_types=trial_types)

## Create Chatter
logfilename = 'out.log'
logfilename = None # autodate
chatter = ArduFSM.chat.Chatter(to_user=logfilename, to_user_dir='./logfiles',
    baud_rate=115200, serial_timeout=.1, serial_port=serial_port)
logfilename = chatter.ofi.name

## Trial setter
ts_obj = trial_setter.TrialSetter(chatter=chatter, 
    params_table=params_table,
    scheduler=scheduler)

## Initialize UI
RUN_UI = True
RUN_GUI = True
ECHO_TO_STDOUT = not RUN_UI
if RUN_UI:
    ui = trial_setter_ui.UI(timeout=100, chatter=chatter, 
        logfilename=logfilename,
        ts_obj=ts_obj)

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
        window_title = rigname + '_licktrain'
        try:
            wc = my.video.WebcamController(device=video_device, 
                output_filename=video_filename,
                window_title=window_title)
            wc.start()
        except IOError:
            print "cannot find webcam at port", video_device
            wc = None
            SHOW_WEBCAM = False
    else:
        wc = None
        
    ## Initialize GUI
    if RUN_GUI:
        plotter = ArduFSM.plot.PlotterWithServoThrow(trial_types)
        plotter.init_handles()

        if rigname == 'L0':
            plotter.graphics_handles['f'].canvas.manager.window.wm_geometry("+700+0")
        else:
            plotter.graphics_handles['f'].canvas.manager.window.move(
                gui_window_position[0], gui_window_position[1])
        
        last_updated_trial = 0
    
    # Move the webcam window once it appears
    if SHOW_WEBCAM:
        cmd = 'xdotool search --name %s windowmove %d %d' % (
            window_title, video_window_position[0], video_window_position[1])
        while os.system(cmd) != 0:
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
        translated_trial_matrix = ts_obj.update(splines, logfile_lines)
        
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
                
                # don't understand why these need to be here
                plt.show()
                plt.draw()


except KeyboardInterrupt:
    print "Keyboard interrupt received"

except trial_setter_ui.QuitException as qe:
    final_message = qe.message

except curses.error as err:
    raise Exception(
        "UI error. Most likely the window is, or was, too small.\n"
        "Quit Python, type resizewin to set window to 80x23, and restart.")

except:
    raise

finally:
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
    


