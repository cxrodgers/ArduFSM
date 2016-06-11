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
    
    def parse(box):
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
                    'l_reward_duration': box.left_valve_duration,
                    'r_reward_duration': box.right_valve_duration,                
                },
                'build': {
                    'serial_port': box.serial_port,
                    'subprocess_window_ypos': box.subprocess_window_ypos,                
                },
            }
    
    res = parse(box)
    
    # temporary hack: compare to Hardcoded
    hc_box_params = Hardcoded.get_box_parameters(box_name)
    for typ in ['C', 'Python', 'build']:
        for k, v in hc_box_params[typ].items():
            if k not in res[typ] or res[typ][k] != v:
                print "%s update: setting %s to %r" % (box_name, k, v)
                
                box.__setattr__(k, v)
                box.save()
    
    # reparse to get changes
    res = parse(box)
    
    return res


def get_board_parameters(board_name):
    board = runner.models.Board.objects.get(name=board_name)
    
    def parse(board):
        return {
                'C': {},
                'Python': {
                    'video_device': board.video_device,
                    'video_window_position': board.video_window_position,
                    'gui_window_position': board.gui_window_position,
                    'window_position_IR_plot': board.window_position_IR_plot,
                    'video_brightness': board.video_brightness,
                    'video_gain': board.video_gain,
                    'video_exposure': board.video_exposure,
                    'l_reward_duration': board.left_valve_duration,
                    'r_reward_duration': board.right_valve_duration,                
                },
                'build': {
                    'serial_port': board.serial_port,
                    'subprocess_window_ypos': board.subprocess_window_ypos,                
                },
            }
    
    res = parse(board)
    
    # temporary hack: compare to Hardcoded
    hc_board_params = Hardcoded.get_board_parameters(board_name)
    for typ in ['C', 'Python', 'build']:
        for k, v in hc_board_params[typ].items():
            if k not in res[typ] or res[typ][k] != v:
                print "%s update: setting %s to %r" % (board_name, k, v)
                
                board.__setattr__(k, v)
                board.save()
    
    # reparse to get changes
    res = parse(board)
    
    return res