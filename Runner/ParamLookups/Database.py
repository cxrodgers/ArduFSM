"""Load params from django db

First we need to get all of the parameters (hardware info, mouse behavioral
info like pipe position) into the Runner django db.

Then we need to be able to access it when starting a new session, rather
than using Hardcoded.py.

Finally we need a new interface where the Daily Plan is displayed and
edited and the session initiated directly from the Runner admin interface,
as opposed to from the terminal.
"""
import django
import runner.models
import Hardcoded

def get_box_parameters(box_name):
    box = runner.models.Box.objects.get(name=box_name)

    return {
            'C': {},
            'Python': {
                'video_device': box.video_device,
                'video_window_position': box.video_window_position,
                'gui_window_position': box.gui_window_position,
                'window_position_IR_plot': box.window_position_IR_plot,
                'video_brightness': box.video_brightness,
                'video_gain': box.video_gain,
                'video_exposure': box.video_exposure,
                'l_reward_duration': box.l_reward_duration,
                'r_reward_duration': box.r_reward_duration,                
            },
            'build': {
                'serial_port': box.serial_port,
                'subprocess_window_ypos': box.subprocess_window_ypos,                
            },
        }

def get_board_parameters(board_name):
    board = runner.models.Board.objects.get(name=board_name)
    
    res = {
        'C': {
            'stepper_driver': board.stepper_driver,
            'use_ir_detector': board.use_ir_detector, 
            'side_HE_sensor_thresh': board.side_HE_sensor_thresh,
            'microstep': board.microstep,
            'invert_stepper_direction': board.invert_stepper_direction,
        },
        'Python': {
            'has_side_HE_sensor': board.has_side_HE_sensor,            
            'use_ir_detector': board.use_ir_detector,                        
            'l_ir_detector_thresh': board.l_ir_detector_thresh,
            'r_ir_detector_thresh': board.r_ir_detector_thresh,
        },
        'build': {
        },
    }
    
    # Hack because a C and Python parameter have the same name
    res['C']['use_ir_detector'] = '1' if res['Python']['use_ir_detector'] else None
    
    # Hack because I don't know how to store a list of filenames
    # in the django db
    if not board.use_ir_detector:
        res['build']['skip_files'] = ['ir_detector.cpp', 'ir_detector.h']

    return res
    
def get_mouse_parameters(mouse_name):
    """Extract and format mouse parameters from database"""
    mouse = runner.models.Mouse.objects.get(name=mouse_name)

    res = {
        'C': {
        },
        'Python': {
            'stimulus_set': mouse.stimulus_set,
            'step_first_rotation': mouse.step_first_rotation,
            'timeout': mouse.timeout,
            'scheduler': mouse.scheduler,
        },
        'build': {
            'protocol_name': mouse.protocol_name,
            'script_name': mouse.script_name,
            'default_board': mouse.default_board,
            'default_box': mouse.default_box,
        },  
    }

    return res