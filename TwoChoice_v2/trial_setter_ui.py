"""Module for generating and interacting with the user."""
import curses
import numpy as np


HEADINGS = """
Actions                |          Parameters         |        Scheduler
------------------------------------------------------------------------------
"""

"""
(L) reward L                  MRT      |         3       "forced alternation"
(R) reward R                  RWIN     |       1000        FD     |    R
(W) reward current                                         RPB    |    1
(Q) save+quit

(P) set parameter
(S) set scheduler
"""

def clear_line(line_num, stdscr):
    stdscr.move(line_num, 0)
    stdscr.clrtoeol()

## Functions that are triggered by various user actions
def ui_action_reward_l():
    pass

def ui_action_reward_r():
    pass

def ui_action_reward_current():
    pass

def ui_action_reward_l():
    pass

def ui_action_save_and_quit():
    pass


ui_actions = [
    ('L', 'reward L', ui_action_reward_l),
    ('R', 'reward R', ui_action_reward_r),
    ('W', 'reward current', ui_action_reward_current),    
    ('Q', 'reward L', ui_action_save_and_quit),
    ]


class UI:
    def __init__(self, chatter, logfilename, params=None, scheduler=None, 
        timeout=1000):
        """Create new UI object"""
        self.element_row = {
            'banner': 0,
            'headings': 2,
            'action_list': 5,
            'param_list': 5,
            'scheduler_panel': 5,
            'info': 21,
            'user_input': 20,
            }
        self.element_col = {
            'param_list': 30,
            'scheduler_panel': 55,
            }
        
        self.chatter = chatter
        self.logfilename = logfilename
        self.params = params
        self.scheduler = scheduler
        self.timeout = timeout
    
    def start(self):
        self.stdscr = curses.initscr()
        #~ curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        self.stdscr.clear()
        self.stdscr.timeout(self.timeout)

        self.draw_menu()
    
    def close(self):
        """Shut down UI and return terminal to nice state."""
        # Shut down UI
        curses.nocbreak()
        if hasattr(self, 'stdscr'):
            self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()
        
    def update_data(self, params=None, scheduler=None):
        """Update info about params and scheduler and redraw menu"""
        if params is not None:
            self.params = params
        if scheduler is not None:
            self.scheduler = scheduler
        self.draw_menu()
    
    def get_and_handle_keypress(self):
        """Take appropriate action for keypresss"""
        # clear user entry line
        clear_line(self.element_row['user_input'], self.stdscr)
        
        # get input
        c = self.stdscr.getch()
        
        if c != -1:
            # Sanitize input
            try:
                c = chr(c)
            except ValueError:
                # eg, for backspace or something
                return
            
            self.stdscr.addstr(self.element_row['info'], 0, "You pressed: %s" % c)        
    
    def draw_menu(self):
        """Writes the whole menu to the screen."""
        self.write_banner()
        self.write_headings()
        self.write_actions()
        self.write_params()
        self.write_scheduler()
    
    def write_banner(self):
        """Write a simple banner at the top"""
        s = "Behavior control UI. Port: %s. Logfile: %s." % (
            self.chatter.ser.port, self.logfilename)
        self.stdscr.addstr(self.element_row['banner'], 0, s)
    
    def write_headings(self):
        """Write out headings for action, params, and scheduler panels"""
        self.stdscr.addstr(self.element_row['headings'], 0, HEADINGS)
    
    def write_actions(self):
        """Write out each action in the action panel"""
        col = 0
        start_row = self.element_row['action_list']
        
        # Write out each action
        for nrow, (key, desc, func) in enumerate(ui_actions):
            s = '(%s) %s' % (key, desc)
            self.stdscr.addstr(start_row + nrow, col, s)
    
    def write_params(self):
        """Write out the current value of everything in self.params"""
        if self.params is None:
            return
        
        start_row = self.element_row['param_list']
        col = self.element_col['param_list']
        
        for nparam, (name, value) in enumerate(self.params):
            s = '%s = %s' % (name, str(value))
            self.stdscr.addstr(start_row + nparam, col, s)
    
    def write_scheduler(self):
        """Write out the scheduler panel"""
        start_row = self.element_row['scheduler_panel']
        col = self.element_col['scheduler_panel']
        
        if 'name' in self.scheduler:
            self.stdscr.addstr(start_row, col, self.scheduler['name'])
        
        if 'params' in self.scheduler:
            for nparam, (name, value) in enumerate(self.scheduler['params']):
                s = '%s = %s' % (name, str(value))
                self.stdscr.addstr(start_row + nparam + 1, col, s)
        
        
    
    
    

#~ class LINES:
    #~ pass
#~ LINES.BANNER = 0
#~ LINES.MENU = 1
#~ LINES.ENTRY = 10
#~ LINES.ENTRY2 = 11
#~ LINES.ERROR = 12
#~ LINES.ARDU_ECHO = 15
#~ LINES.SCHED_PARAMS = 17
#~ LINES.PARAMS = 18
