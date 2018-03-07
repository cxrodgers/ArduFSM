"""Load params from django db

First we need to get all of the parameters (hardware info, mouse behavioral
info like pipe position) into the Runner django db.

Then we need to be able to access it when starting a new session, rather
than using Hardcoded.py.

Finally we need a new interface where the Daily Plan is displayed and
edited and the session initiated directly from the Runner admin interface,
as opposed to from the terminal.

What to do about None in the database? This probably means no data available,
as opposed to an explicit None (although maybe for video_device...).
So probably we want to remove it from the dicts, because otherwise a None
from mouse will trump a real value from box or board.

TODO: Interpret a None in a NullBooleanField (like use_ir_detector) as a None
(to be removed) rather than False (taking precedence over something else).

Avoid using nullable char fields because then there are two possible values
that mean null: null, and ''. The django convention is to use ''. This is 
a little tricky for C parameters because they have to be strings. If they
are set to '', should we interpret this as define it without a value, or
don't define it?

"""
import django
import runner.models
import Hardcoded

def fix_ir_detector_params(res):
    """Deal with issues relating to IR detector params
    
    First of all, the same parameter 'use_ir_detector' is used as both
    a Python and C parameter. But in C this needs to be '1' or None,
    where as in Python it needs to be True or False. We store it as True
    or False and translate the C version to '1' or None here.
    
    Secondly, some files need to be added to 'skip_files' build parameter,
    but I don't know how to store a list in the database, so hand-translating
    it here.
    
    This function is called wherever use_ir_detector is stored (mouse and
    board).    
    """
    if res['Python']['use_ir_detector']:
        # Hack because a C and Python parameter have the same name
        # True -> '1'
        res['C']['use_ir_detector'] = '1'
        res['build']['skip_files'] = []

    else:
        # Hack because a C and Python parameter have the same name
        # False -> None
        res['C']['use_ir_detector'] = '0'

        # This has to be '0' or else it gets removed from the dict completely
        # and then the precedence update order fails

        # Hack because I don't know how to store a list of filenames
        # in the django db
        res['build']['skip_files'] = ['ir_detector.cpp', 'ir_detector.h']

    return res

def remove_None_from_dict(d):
    """Remove specific parameters that are None
    
    When we retrieve null values from the database, we want to remove
    them from the dict. This is because the hierarchy (mouse, board, box)
    uses dict.update, and so we don't want null values in the dict.
    
    This function should be applied to each set of specific parameters
    right after the database lookup.
    
    Let's also remove '' at this point, since this basically means None
    in many cases (eg, CharFields). We should not have any charfields where
    '' is to be interpreted as anything other than None/Null.
    """
    res = {}
    for typ, subdict in d.items():
        res_l = []
        for k, v in subdict.items():
            if v is not None and v != (None, None) and v != '':
                res_l.append((k, v))
        res[typ] = dict(res_l)
    
    return res

def get_box_parameters(box_name):
    box = runner.models.Box.objects.get(name=box_name)

    return remove_None_from_dict({
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
                'l_reward_sensitivity': box.l_reward_sensitivity,
                'r_reward_sensitivity': box.r_reward_sensitivity,                         
            },
            'build': {
                'serial_port': box.serial_port,
                'subprocess_window_xpos': box.subprocess_window_xpos,  
                'subprocess_window_ypos': box.subprocess_window_ypos,                
            },
        })

def get_board_parameters(board_name):
    board = runner.models.Board.objects.get(name=board_name)
    
    res = {
        'C': {
            'stepper_driver': board.stepper_driver,
            'use_ir_detector': board.use_ir_detector, 
            'side_HE_sensor_thresh': board.side_HE_sensor_thresh,
            'microstep': board.microstep,
            'invert_stepper_direction': board.invert_stepper_direction,
            'stepper_offset_steps': board.stepper_offset_steps,
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
    
    # Fix the ir_detector params
    res = fix_ir_detector_params(res)

    return remove_None_from_dict(res)
    
def get_mouse_parameters(mouse_name):
    """Extract and format mouse parameters from database"""
    mouse = runner.models.Mouse.objects.get(name=mouse_name)

    res = {
        'C': {
            'use_ir_detector': mouse.use_ir_detector,
            'task_reaction_time': mouse.task_reaction_time,
            'nolick_max_wait_ms': mouse.nolick_max_wait_ms,
            'nolick_required_interval_ms': mouse.nolick_required_interval_ms,
        },
        'Python': {
            'use_ir_detector': mouse.use_ir_detector,                        
            'stimulus_set': mouse.stimulus_set,
            'step_first_rotation': mouse.step_first_rotation,
            'timeout': mouse.timeout,
            'scheduler': mouse.scheduler,
            'max_rewards_per_trial': mouse.max_rewards_per_trial,
            'target_water_volume': mouse.target_water_volume,
        },
        'build': {
            'protocol_name': mouse.protocol_name,
            'script_name': mouse.script_name,
            'default_board': mouse.default_board,
            'default_box': mouse.default_box,
        },  
    }

    # Fix the ir_detector params
    res = fix_ir_detector_params(res)

    return remove_None_from_dict(res)