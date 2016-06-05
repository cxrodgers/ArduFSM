"""Module for looking up specific parameters given session parameters.

Right now these are just hard-coded parameters for boxes, boards, etc.
Later this should be able to access JSON files or a database.

This also contains the function
    get_specific_parameters_from_user_input
which takes the session parameters, gets the specific parameters, and
puts them together by implementing the prioritization rules.

Each parameter dict has the following structure:
    'C': a dict of (key, value) pairs that will become #define macros
        `value` should be a string, or None
        None means do not define
    'Python': a dict that will be written as a JSON parameters file
        for Python.
    'build': a dict of sandbox parameters, like the protocol name,
        that is used in the creation of the sandbox.
    
This could potentially be a list of parameters, each with fields
'human-readable-name', 'code-name', 'value'
"""

def get_box_parameters(box):
    """Dummy function returning parameters determined by box"""
    if box == 'test':
        return {
            'C': {},
            'Python': {
                'l_reward_duration': 30,
                'r_reward_duration': 40,
                'video_device': '/dev/video3',
                'window_position_video': (100, 100),
                'window_position_gui': (500, 600),
            },
            'build': {
                'serial_port': '/dev/ttyACM1',
            },
        }
    elif box == 'CR0':
        return {
            'C': {},
            'Python': {
                'video_device': '/dev/video0',
                'video_window_position': (500, 0),
                'gui_window_position': (700, 0),
                'window_position_IR_plot': (1100, 0),                
                'video_brightness': 0,
                'video_gain': 0,
                'video_exposure': 8,
                'l_reward_duration': 60,
                'r_reward_duration': 55,                
            },
            'build': {
                'serial_port': '/dev/ttyACM0',
                'subprocess_window_ypos': 0,                
            },
        }
    elif box == 'CR1':
        return {
            'C': {},
            'Python': {
                'video_device': '/dev/video0',
                'video_window_position': (1150, 0),
                'gui_window_position': (425, 0),
                'l_reward_duration': 170,
                'r_reward_duration': 220,
            },
            'build': {
                'serial_port': '/dev/ttyACM0',
                'subprocess_window_ypos': 0,
            },
        }        
    elif box == 'CR2':
        return {
            'C': {},
            'Python': {
                'video_device': '/dev/video1',
                'video_window_position': (1150, 260),
                'gui_window_position': (425, 260),
                'l_reward_duration': 95,
                'r_reward_duration': 120,                
            },
            'build': {
                'serial_port': '/dev/ttyACM1',
                'subprocess_window_ypos': 270,
            },
        }            
    elif box == 'CR3':
        return {
            'C': {},
            'Python': {
                'video_device': '/dev/video2',
                'video_window_position': (1150, 520),
                'gui_window_position': (420, 520),
                'window_position_IR_plot': (1000, 260),                            
                'l_reward_duration': 100,
                'r_reward_duration': 100,                
            },
            'build': {
                'serial_port': '/dev/ttyACM2',
                'subprocess_window_ypos': 530,
            },
        }           
    elif box == 'CR4':
        return {
            'C': {},
            'Python': {
                'video_device': '/dev/video3',
                'video_window_position': (1150, 780),
                'gui_window_position': (425, 780),
                'l_reward_duration': 150,
                'r_reward_duration': 100,                
            },
            'build': {
                'serial_port': '/dev/ttyACM3',
                'subprocess_window_ypos': 790,
            },
        }           
    elif box == 'CR5':
        return {
            'C': {},
            'Python': {
                'video_device': '/dev/video4',
                'video_window_position': (1150, 980),
                'gui_window_position': (425, 980),
                'l_reward_duration': 150,
                'r_reward_duration': 150,                
            },
            'build': {
                'serial_port': '/dev/ttyACM4',
                'subprocess_window_ypos': 990,
            },
        }           
    
    raise ValueError("unknown box: %s" % box)

def get_board_parameters(board):
    """Dummy function returning parameters determined by board
    

    """
    if board == 'test':
        return {
            'C': {
                'stepper_driver': '1',
                'use_ir_detector': '0',            
                'side_HE_sensor_thresh': '50',
                'top_HE_sensor_thresh': '50',
                'side_HE_sensor_polarity': '1',
                'top_HE_sensor_polarity': '0',
            },
            'Python': {
                'use_ir_detector': False,                        
                'l_ir_detector_thresh': 80,
                'r_ir_detector_thresh': 50,
                'has_side_HE_sensor': True,
            },
            'build': {
                'skip_files': ['ir_detector.cpp', 'ir_detector.h'],
            },
        }
    elif board == 'CR1':
        return {
            'C': {
                'stepper_driver': '1',
                'use_ir_detector': None,            
                'side_HE_sensor_thresh': '50',
                'microstep': '1',
            },
            'Python': {
                'has_side_HE_sensor': True,            
                'use_ir_detector': False,
            },
            'build': {
                'skip_files': ['ir_detector.cpp', 'ir_detector.h'],            
            },
        }        
    elif board == 'CR2':
        return {
            'C': {
                'stepper_driver': '1',
                'use_ir_detector': None,            
                'side_HE_sensor_thresh': '80',
                'microstep': '8',
            },
            'Python': {
                'has_side_HE_sensor': True,            
                'use_ir_detector': False,
            },
            'build': {
                'skip_files': ['ir_detector.cpp', 'ir_detector.h'],            
            },
        }   
    elif board == 'CR3':
        return {
            'C': {
                'stepper_driver': '1',
                'use_ir_detector': None,            
                'side_HE_sensor_thresh': '50',
                'microstep': '8',
            },
            'Python': {
                'has_side_HE_sensor': False,            
                'use_ir_detector': False,
            },
            'build': {
                'skip_files': ['ir_detector.cpp', 'ir_detector.h'],            
            },
        }        
    elif board == 'CR4':
        return {
            'C': {
                'stepper_driver': '1',
                'use_ir_detector': None,            
                'side_HE_sensor_thresh': '15',
                'microstep': '1',
                'invert_stepper_direction': '1',
            },
            'Python': {
                'has_side_HE_sensor': False,            
                'use_ir_detector': False,
            },
            'build': {
                'skip_files': ['ir_detector.cpp', 'ir_detector.h'],            
            },
        }         
    elif board == 'CR5':
        return {
            'C': {
                'stepper_driver': '1',
                'use_ir_detector': None,            
                'side_HE_sensor_thresh': '50',
                'microstep': '8',
                'invert_stepper_direction': '1',                
            },
            'Python': {
                'has_side_HE_sensor': True,            
                'use_ir_detector': False,                        
            },
            'build': {
                'skip_files': ['ir_detector.cpp', 'ir_detector.h'],
            },
        }
    elif board == 'CR6':
        return {
            'C': {
                'stepper_driver': '1',
                'use_ir_detector': '1',            
                'side_HE_sensor_thresh': '50',
                'microstep': '8',                
                'invert_stepper_direction': '1',                
            },
            'Python': {
                'has_side_HE_sensor': False,            
                'use_ir_detector': True,                        
                'l_ir_detector_thresh': 40,
                'r_ir_detector_thresh': 80,
                'window_position_IR_detector': (1300, 450),
            },
            'build': {
            },
        }    
    
    raise ValueError("unknown board: %s" % board)

def translate_c_parameter_name(name):
    """Translate C parameters from human-readable to C-mangled.
    
    For example: if name is 'side_HE_sensor_thresh', this function returns
        '__HWCONSTANTS_H_HALL_THRESH'
    
    If the name is not recognized, returns None.
    
    """
    if name == 'side_HE_sensor_thresh':
        return '__HWCONSTANTS_H_HALL_THRESH'
    elif name == 'use_ir_detector':
        return '__HWCONSTANTS_H_USE_IR_DETECTOR'
    elif name == 'stepper_driver':
        return '__HWCONSTANTS_H_USE_STEPPER_DRIVER'
    elif name == 'microstep':   
        return '__HWCONSTANTS_H_MICROSTEP'
    elif name == 'invert_stepper_direction':
        return '__HWCONSTANTS_H_INVERT_STEPPER_DIRECTION'
    else:
        return None

def get_mouse_parameters(mouse):
    """Dummy function returning parameters determined by mouse
    
    Note that these overrule any other parameters.
    """
    if mouse == 'default':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_2shapes_CCL_3srvpos',
                'step_first_rotation': 125,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    elif mouse == 'KF61':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_2shapes_3srvpos',
                'step_first_rotation': 125,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }        
    elif mouse == 'KM63':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_2shapes_CCL_3srvpos',
                'step_first_rotation': 125,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }             
    elif mouse == 'KM65':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_3srvpos',
                'step_first_rotation': 50,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }    
    elif mouse == 'KF73':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_2srvpos',
                'step_first_rotation': 50,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    elif mouse == 'KF75':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_2shapes_CCL_3srvpos',
                'step_first_rotation': 125,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    elif mouse == 'KF79':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_2shapes_CCL_3srvpos',
                'step_first_rotation': 125,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    elif mouse == 'KF80':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_3srvpos',
                'step_first_rotation': 50,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    elif mouse == 'KM81':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_3srvpos',
                'step_first_rotation': 50,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    elif mouse == 'KM82':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_2srvpos',
                'step_first_rotation': 50,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    elif mouse == 'KM83':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_3srvpos',
                'step_first_rotation': 50,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    elif mouse == 'KM84':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_2srvpos',
                'step_first_rotation': 50,
                'scheduler': 'ForcedAlternation',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    elif mouse == 'KM85':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_2srvpos',
                'step_first_rotation': 50,
                'scheduler': 'ForcedAlternation',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    elif mouse == 'KM86':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_2srvpos',
                'step_first_rotation': 50,
                'scheduler': 'ForcedAlternation',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
            },        
        }
    
    raise ValueError("unknown mouse: %s" % mouse)


def get_default_parameters():
    """Set these parameters if nothing else overrules them
    
    Perhaps there should be a default for each session parameter instead
    """
    return {
        'C': {
            'step_delay_us': '4000',
        },
        'Python': {
            'stimulus_set': '2shapes_CCL',
            'step_first_rotation': 125,
            'error_timeout': 2000,
            'scheduler': 'Auto',
        },    
        'build': {
        },
    }

def get_specific_parameters_from_user_input(user_input):
    """Converts session parameters to specific parameters.
    
    """
    # Convert session parameters into specific parameters
    board_parameters = get_board_parameters(user_input['board'])
    box_parameters = get_box_parameters(user_input['box'])
    mouse_parameters = get_mouse_parameters(user_input['mouse'])    
    
    # Split into C, Python, and build parameters
    specific_parameters = {}
    for param_type in ['C', 'Python', 'build']:
        if param_type not in specific_parameters:
            specific_parameters[param_type] = {}
        
        specific_parameters[param_type].update(box_parameters[param_type])
        specific_parameters[param_type].update(board_parameters[param_type])
        specific_parameters[param_type].update(mouse_parameters[param_type])

    # Check the required ones are present
    for param_name in ['protocol_name', 'script_name', 'serial_port']:
        assert param_name in specific_parameters['build']
    
    # Copy some from 'build' to 'python'
    if 'serial_port' not in specific_parameters['Python']:
        specific_parameters['Python']['serial_port'] = specific_parameters[
            'build']['serial_port']
    if 'box' not in specific_parameters['Python']:
        specific_parameters['Python']['box'] = user_input['box']
    if 'mouse' not in specific_parameters['Python']:
        specific_parameters['Python']['mouse'] = user_input['mouse']
    
    return specific_parameters
