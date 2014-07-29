"""Objects for setting trials and convenient interaction with chatter"""
import sys, time, shutil
import datetime
import numpy as np
import os
import glob
import curses


def reward_bout_scheduler(params, filename):
    """Scheduler that sends FORCE commands to produce bouts of rewards.
    
    scheduler_params  : dict, state information about bouts
        This will be updated in this function.
    filename    : name of ardulines file to read
    
    Returns: cmd
        The text of the os.system command that was issued, if any.
    """
    #~ os.system('echo "X" > TO_DEV')
    
    # Extract params
    bout_beginning = params['bout_beginning']
    force_dir = params['force_dir']
    REWARDS_PER_BOUT = params['REWARDS_PER_BOUT']

    # Return variable
    cmd = ''
    
    # Read the files
    with file(filename) as fi:
        lines = fi.readlines()
    
    # identify the current force
    force_lines = filter(
        lambda line: line.strip() == 'ACK FORCE L' or line.strip() == 'ACK FORCE R', 
        lines)
    if len(force_lines) == 0:
        # nothing force yet, for instance upon start
        cmd = 'echo "FORCE %s" > TO_DEV' % force_dir
        os.system(cmd)
        return cmd
    elif len(force_lines) > 0:
        # something's been forced, check that we're right
        inferred_force = force_lines[-1].strip()[-1]
        if inferred_force != force_dir:
            force_dir = inferred_force
            params['force_dir'] = inferred_force

    # Include only events since the most recent force
    lines = lines[bout_beginning:]

    # Find all the reward lines
    rew_l_lines = np.where([
        line.strip().endswith('EVENT REWARD_L') for line in lines])[0]
    rew_r_lines = np.where([
        line.strip().endswith('EVENT REWARD_R') for line in lines])[0]

    # Decide whether to force
    if force_dir == 'L':
        if len(rew_l_lines) >= REWARDS_PER_BOUT:
            cmd = 'echo "FORCE R" > TO_DEV'
            os.system(cmd)
            
            # Update variables for next bout
            params['force_dir'] = 'R'
            params['bout_beginning'] = len(lines) + bout_beginning
        
    elif force_dir == 'R':
        if len(rew_r_lines) >= REWARDS_PER_BOUT:
            cmd = 'echo "FORCE L" > TO_DEV'
            os.system(cmd)      
            
            # Update variables for next bout
            params['force_dir'] = 'L'
            params['bout_beginning'] = len(lines) + bout_beginning

    # debug
    #~ cmd = '%d %d %r' % (len(rew_l_lines), len(rew_r_lines), params)

    return cmd


## UI stuff
MENU = """(q) save and quit
(e) echo
(s) set rewards
(l) reward L
(r) reward R
(w) reward current
(f) force L
(g) force R
(x) force X and raise RPB to 1000
"""

class LINES:
    pass
LINES.FILENAME = 0
LINES.MENU = 1
LINES.ENTRY = 10
LINES.ENTRY2 = 11
LINES.ERROR = 12
LINES.ARDU_ECHO = 15
LINES.SCHED_PARAMS = 17
LINES.PARAMS = 18
TIMEOUT = 1000

def clear_line(line_num, stdscr):
    stdscr.move(line_num, 0)
    stdscr.clrtoeol()

def get_additional_input(prompt, stdscr):
    clear_line(LINES.ENTRY, stdscr)
    clear_line(LINES.ENTRY2, stdscr)
    stdscr.addstr(LINES.ENTRY, 0, prompt)
    stdscr.move(LINES.ENTRY2, 0)
    stdscr.timeout(-1)
    val = stdscr.getstr()
    stdscr.timeout(TIMEOUT)
    clear_line(LINES.ENTRY2, stdscr)
    return val


def run_ui_till_quit(filename, scheduler_params, session_params):
    """Runs a curses UI that sends manual or scheduled commands TO_DEV.
    
    filename    : ardulines file to pass to scheduler
    """
    ## UI main loop
    try:
        stdscr = curses.initscr()
        #~ curses.noecho()
        curses.cbreak()
        stdscr.keypad(1)
        stdscr.clear()
        stdscr.addstr(LINES.FILENAME, 0, filename)
        stdscr.addstr(LINES.MENU, 0, MENU)
        stdscr.timeout(TIMEOUT)
        
        while True:
            # print all params
            clear_line(LINES.PARAMS, stdscr)
            stdscr.addstr(LINES.PARAMS, 0, ' '.join(['%s=%s' % (
                key, str(val)) for key, val in session_params.iteritems()]))

            # print all params
            clear_line(LINES.SCHED_PARAMS, stdscr)
            sched_params_str = scheduler_params['name']
            if 'REWARDS_PER_BOUT' in scheduler_params:
                sched_params_str += ' RPB=%d' % scheduler_params['REWARDS_PER_BOUT']
            if 'force_dir' in scheduler_params:
                sched_params_str += ' FD=%s' % scheduler_params['force_dir']
            stdscr.addstr(LINES.SCHED_PARAMS, 0, sched_params_str)
            
            # clear input line
            clear_line(LINES.ENTRY, stdscr)
            
            # get input
            c = stdscr.getch()
            
            if c != -1:
                # Sanitize input
                try:
                    c = chr(c)
                except ValueError:
                    # eg, for backspace or something
                    continue
                
                # clear any error message
                clear_line(LINES.ERROR, stdscr)
                
                # parse input
                if c == 'q':
                    # save and quit
                    mousename = get_additional_input(
                        "Enter mouse name: \n", stdscr)
                    mousename = mousename.strip()
                    if mousename != '':
                        new_filename = filename + '.' + mousename
                        assert not os.path.exists(new_filename)
                        shutil.copyfile(filename, new_filename)
                    
                    break
                elif c == 'l':
                    cmd = 'echo "REWARD L" > TO_DEV'
                    stdscr.addstr(LINES.ERROR, 0, cmd)
                    os.system(cmd)
                elif c == 'r':
                    cmd = 'echo "REWARD R" > TO_DEV'
                    stdscr.addstr(LINES.ERROR, 0, cmd)
                    os.system(cmd)
                elif c == 'w':
                    cmd = 'echo "REWARD" > TO_DEV'
                    stdscr.addstr(LINES.ERROR, 0, cmd)
                    os.system(cmd)
                elif c == 'f':
                    cmd = 'echo "FORCE L" > TO_DEV'
                    stdscr.addstr(LINES.ERROR, 0, cmd)
                    os.system(cmd)
                elif c == 'g':
                    cmd = 'echo "FORCE R" > TO_DEV'
                    stdscr.addstr(LINES.ERROR, 0, cmd)
                    os.system(cmd)
                elif c == 'x':
                    # also set RPB higher
                    scheduler_params['REWARDS_PER_BOUT'] = 1000
                    
                    cmd = 'echo "FORCE X" > TO_DEV'
                    stdscr.addstr(LINES.ERROR, 0, cmd)
                    os.system(cmd)
                elif c == 'e':
                    msg = get_additional_input("What do you want to echo?\n", stdscr)
                    cmd = 'echo "%s" > TO_DEV' % msg.upper()
                    stdscr.addstr(LINES.ERROR, 0, cmd)
                    os.system(cmd)
                    
                    # try to parse
                    cmd_l = msg.upper().split(' ')
                    if len(cmd_l) == 3 and cmd_l[0] == 'SET':
                        param_name = cmd_l[1]
                        if param_name in session_params:
                            # update stored version of params
                            session_params[param_name] = cmd_l[2]
                    
                elif c == 's':
                    msg = get_additional_input("How many rewards per bout?\n", stdscr)
                    try:
                        val = int(msg)
                    except ValueError:
                        stdscr.addstr(LINES.ERROR, 0, 'invalid input')
                        continue
                    
                    stdscr.addstr(LINES.ERROR, 0, 
                        'setting rewards per bout to %d' % val)
                    scheduler_params['REWARDS_PER_BOUT'] = val
                else:
                    stdscr.addstr(LINES.ERROR, 0, "invalid input: %r" % c)
            
            # Run the scheduler
            ardulines_cmd = reward_bout_scheduler(scheduler_params, filename)
            if ardulines_cmd != '':
                timestr = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                stdscr.addstr(LINES.ARDU_ECHO, 0, timestr + ' ' + ardulines_cmd)

    finally:
        curses.nocbreak()
        stdscr.keypad(0)
        curses.echo()

        curses.endwin()