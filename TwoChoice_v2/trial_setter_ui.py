"""Module for generating and interacting with the user."""
import curses
import numpy as np
import os.path, shutil
import TrialSpeak

HEADINGS = """
Actions                |          Parameters         |        Scheduler
------------------------------------------------------------------------------
"""


def clear_line(line_num, stdscr):
    stdscr.move(line_num, 0)
    stdscr.clrtoeol()

class QuitException(Exception):
    pass

## Functions that are triggered by various user actions
class UIActionTaker:
    """Implements the actions that are parsed by the UI"""
    def __init__(self, ui, chatter):
        self.ui = ui
        self.chatter = chatter
    
    def ui_action_reward_l(self):
        # these tokens should be in TrialSpeak
        self.chatter.queued_write_to_device('REWARD L')

    def ui_action_reward_r(self):
        self.chatter.queued_write_to_device('REWARD R')

    def ui_action_reward_current(self):
        self.chatter.queued_write_to_device('REWARD')

    def ui_action_save(self):
        """Asks for mouse name and saves"""
        # chatter should store this attribute more transparently
        filename = self.chatter.ofi.name
        
        # Get mouse name
        mousename = self.ui.get_additional_input("Enter mouse name: ")
        mousename = mousename.strip()
        
        # Copy the file
        if mousename != '':
            new_filename = filename + '.' + mousename
            assert not os.path.exists(new_filename)
            shutil.copyfile(filename, new_filename)  
        
        # Quit
        raise QuitException("saved as %s" % new_filename)
    
    def set_param(self):
        # Get name and value
        param_name = self.ui.get_additional_input("Enter param name: ").strip().upper()
        param_value = self.ui.get_additional_input("Enter param value: ").strip()
        
        # Send to device
        cmd = TrialSpeak.command_set_parameter(param_name, param_value)
        self.chatter.queued_write_to_device(cmd)
        
        # Update in ui params
        uipd = dict(self.ui.params)
        uipd[param_name] = int(param_value)
        self.ui.update_data(params=uipd.items())
        


class UI:
    def __init__(self, chatter, logfilename, params=None, scheduler=None, 
        timeout=1000):
        """Create new UI object"""
        self.chatter = chatter
        self.logfilename = logfilename
        self.params = params
        self.scheduler = scheduler
        self.timeout = timeout

        # Create default positioning tables
        self.element_row = {
            'banner': 0,
            'headings': 2,
            'action_list': 5,
            'param_list': 5,
            'scheduler_panel': 5,
            'info': 21,
            'user_input': 20,
            'addl_input_prompt': 20,
            'addl_input_response': 21,
            'logfile_lines': 10,
            }
        self.element_col = {
            'param_list': 30,
            'scheduler_panel': 55,
            }
        
        # "Size" of the various panels. Probably need some more consistent
        # way to handle this.
        self.panel_height = {
            'logfile_lines': 10
            }
        self.logfile_lines = []

        # Create an action taker
        self.ui_action_taker = UIActionTaker(self, self.chatter)
        
        # Create a shortcut dispatch table
        # Pressing the key in the first position triggers a call to the
        # function in the last position
        self.ui_actions = [
            ('L', 'reward L', self.ui_action_taker.ui_action_reward_l),
            ('R', 'reward R', self.ui_action_taker.ui_action_reward_r),
            ('W', 'reward current', self.ui_action_taker.ui_action_reward_current),    
            ('Q', 'save + quit', self.ui_action_taker.ui_action_save),
            ('P', 'set param', self.ui_action_taker.set_param),
            ]
    
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
        
    def update_data(self, params=None, scheduler=None, logfile_lines=None):
        """Update info about params and scheduler and redraw menu"""
        if params is not None:
            self.params = params
        if scheduler is not None:
            self.scheduler = scheduler
        if logfile_lines is not None:
            self.logfile_lines = logfile_lines
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
                self.print_info("invalid character pressed")                
                return

            # Echo what was pressed
            self.print_info("You pressed: %s" % c)
            
            # always capitalize
            c = c.upper()
            
            # Dispatch by shortcut
            action_short_cut_l = [l[0] for l in self.ui_actions]
            if c in action_short_cut_l:
                ui_action_rowidx = action_short_cut_l.index(c)
                
                # Call the function
                self.ui_actions[ui_action_rowidx][2]()
            else:
                self.print_info("Unknown shortcut: %s" % c)

    def get_additional_input(self, prompt):
        """Gets an additional string of input from the user"""
        # Clear prompt and entry rows
        self.clear_line(self.element_row['addl_input_prompt'])
        self.clear_line(self.element_row['addl_input_response'])
        
        # Display prompt and move to input row
        self.safe_print(prompt, self.element_row['addl_input_prompt'], 0, 
            max_lines=1, max_width=80)
        self.stdscr.move(self.element_row['addl_input_response'], 0)
        
        # Reset timeout so that user has plenty of time
        self.stdscr.timeout(-1)
        val = self.stdscr.getstr()
        
        # Reset timeout to default
        self.stdscr.timeout(self.timeout)
        
        # Clear
        self.clear_line(self.element_row['addl_input_prompt'])
        self.clear_line(self.element_row['addl_input_response'])
        return val
    
    def clear_line(self, row):
        """Wrapper around function to clear a line"""
        clear_line(row, self.stdscr)

    def print_info(self, s):
        """Prints info to info line, with some error checking for size"""
        clear_line(self.element_row['info'], self.stdscr)
        self.safe_print(s, self.element_row['info'], 0, max_lines=1, max_width=80)
    
    def safe_print(self, s, row, col, max_lines=1, max_width=80):
        """Error-checking print function. Does not clear first
        
        Should probably change this to match addstr syntax
        """
        splines = s.split('\n')
        
        # Truncate if too many lines
        if len(splines) > max_lines:
            splines = splines[:max_lines]
        
        # Truncate lines that are too long
        splines = [spline[:max_width] for spline in splines]
        
        # Now print
        # Could print individual lines separately
        self.stdscr.addstr(row, col, '\n'.join(splines))
    
    def draw_menu(self):
        """Writes the whole menu to the screen."""
        self.stdscr.clear()
        self.write_banner()
        self.write_headings()
        self.write_actions()
        self.write_params()
        self.write_scheduler()
        self.write_logfile_lines()
    
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
        for nrow, (key, desc, func) in enumerate(self.ui_actions):
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
    
    def write_logfile_lines(self):
        """Write out the most recent lines in the logfile"""
        start_row = self.element_row['logfile_lines']
        nrows = self.panel_height['logfile_lines']
        
        # Write backwards from the end
        for nline, line in enumerate(self.logfile_lines[-1:-nrows:-1]):
            row = start_row + nrows - nline - 1
            self.clear_line(row)
            self.safe_print(line.strip(), row, col=0)
    
    
    

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
