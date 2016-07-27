def get_box_parameters(box):
    """Dummy function returning parameters determined by box"""
    if box == 'CR0':
        return {
            'C': {},
            'Python': {
                'video_device': '/dev/video0',
                'video_window_position': (500, 0),
                'gui_window_position': (700, 0),
                'window_position_IR_plot': (2000, 0),                
                'video_brightness': 0,
                'video_gain': 0,
                'video_exposure': 8,
                'l_reward_duration': 60,
                'r_reward_duration': 55,                
                'timeout': 6000,
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
                'l_reward_duration': 190,
                'r_reward_duration': 310,
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
                'l_reward_duration': 130,
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
                'l_reward_duration': 150,
                'r_reward_duration': 115,                
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
                'l_reward_duration': 210,
                'r_reward_duration': 150,                
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
    if box == 'CR6':
        return {
            'C': {},
            'Python': {
                'video_device': '/dev/video0',
                'video_window_position': (500, 0),
                'gui_window_position': (700, 0),
                'window_position_IR_plot': (2000, 0),                
                'video_brightness': 0,
                'video_gain': 0,
                'video_exposure': 8,
                'l_reward_duration': 60,
                'r_reward_duration': 55,                
                'timeout': 6000,
            },
            'build': {
                'serial_port': '/dev/tty.usbmodem1421',
                'subprocess_window_ypos': 0,                
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
                'microstep': '8',
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
                'l_ir_detector_thresh': 50,
                'r_ir_detector_thresh': 50,
            },
            'build': {
            },
        }    
    
    raise ValueError("unknown board: %s" % board)

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

    if mouse == 'default2':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_3srvpos',
                'step_first_rotation': 50,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'ModularTwoChoice',
                'script_name': 'ModularTwoChoice.py',
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
                'default_board': 'CR4',
                'default_box': 'CR4',                
            },        
        }             
    elif mouse == 'KM65':
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
                'default_board': 'CR1',
                'default_box': 'CR1',                
            },        
        }    
    elif mouse == 'KF73':
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
                'default_board': 'CR3',
                'default_box': 'CR3',
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
                'default_board': 'CR3',
                'default_box': 'CR3',                
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
                'default_board': 'CR4',
                'default_box': 'CR4',                
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
                'default_board': 'CR6',
                'default_box': 'CR0',
            },        
        }
    elif mouse == 'KM81':
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
                'default_board': 'CR2',
                'default_box': 'CR2',                
            },        
        }
    elif mouse == 'KM82':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_1srvpos',
                'step_first_rotation': 50,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
                'default_board': 'CR1',
                'default_box': 'CR1',                
            },        
        }
    elif mouse == 'KM83':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_b2shapes_CCL_3srvpos',
                'step_first_rotation': 125,
                'scheduler': 'Auto',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
                'default_board': 'CR2',
                'default_box': 'CR2',                
            },        
        }
    elif mouse == 'KM84':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_2srvpos',
                'step_first_rotation': 50,
                'timeout': 6000,
                'scheduler': 'ForcedAlternation',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
                'default_board': 'CR1',
                'default_box': 'CR1',                
            },        
        }
    elif mouse == 'KM85':
        return {
            'C': {
            },
            'Python': {
                'stimulus_set': 'trial_types_CCL_2srvpos',
                'step_first_rotation': 50,
                'timeout': 6000,
                'scheduler': 'ForcedAlternation',
            },
            'build': {
                'protocol_name': 'TwoChoice',
                'script_name': 'TwoChoice.py',
                'default_board': 'CR4',
                'default_box': 'CR4',                
            },        
        }
    elif mouse == 'KM86':
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
                'default_board': 'CR2',
                'default_box': 'CR2',                
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