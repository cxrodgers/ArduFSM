"""Module for reading and generating TrialSpeak

For instance, this module contains functions for reading log files, splitting
them by trial, and also for generating commands to send to the arduino.
"""
import pandas, numpy as np, my

ack_token = 'ACK'
release_trial_token = 'RELEASE_TRL'
trial_released_token = 'TRL_RELEASED'
start_trial_token = 'TRL_START'
trial_param_token = 'TRLP'
trial_result_token = 'TRLR'

# dictionary for actions
# this must match the arduino code
LEFT = 1
RIGHT = 2
NOGO = 3

# dictionary for outcomes
# this assumes two-alternative choice
HIT = 1
ERROR = 2
SPOIL = 3


## Reading functions
def load_splines_from_file(filename):
    """Reads lines from file and split into list of lists by trial"""
    # Read lines
    lines = read_lines_from_file(filename)
    
    # Split by trial
    splines = split_by_trial(lines)

    return splines

def split_by_trial(lines):
    """Splits lines from logfile into list of lists by trial.

    Returns: splines, a list of list of lines, each beginning with
    TRIAL START (which is when the current trial params are determined).
    
    Note that this means that the first entry (if it exists) will always be 
    setup info, not trial info.
    """
    if len(lines) == 0:
        return [[]]
    
    # Find the trial start lines
    # This could be done in a couple of ways. Which is most efficient?
    # This method: split by space, check for token in position 1
    trial_starts = [0]
    for nline, line in enumerate(lines):        
        sp_line = line.split()
        if len(sp_line) > 1 and sp_line[1] == start_trial_token:
            trial_starts.append(nline)

    # Now iterate over trial_starts and append the chunks
    splines = []
    for nstart in range(len(trial_starts)-1):
        splines.append(lines[trial_starts[nstart]:trial_starts[nstart+1]])
    
    # Append the leftovers as the last trial, if there is anything
    if len(trial_starts) >= 1:
        splines.append(lines[trial_starts[-1]:])
    
    return splines
    
def read_lines_from_file(filename):
    """Reads all lines from file and returns as list"""
    with file(filename) as fi:
        lines = fi.readlines()
    return lines


## Parsing functions
def parse_lines_into_df(lines):
    """Parse every line into time, command, and argument.
    
    In trial speak, each line has the same format: the time in milliseconds,
    space, a string command, space, an optional argument. This function parses
    each line into those three components and returns as a dataframe.
    """
    # Split each line
    rec_l = []
    for line in lines:
        sp_line = line.split()
        
        # Skip anything with no strings or without a time argument first
        try:
            int(sp_line[0])
        except (IndexError, ValueError):
            continue
        
        # If longer than 3, join the 3rd to the end into a single argument
        if len(sp_line) > 3:
            sp_line = [sp_line[0], sp_line[1], ' '.join(sp_line[2:])]
        rec_l.append(sp_line)
    
    # DataFrame it and convert string times to integer
    df = pandas.DataFrame(rec_l, columns=['time', 'command', 'argument'])
    df['time'] = df['time'].astype(np.int)
    return df


def my_replace(ser, d, nanval='nanval'):
    """My version of pandas.Series.replace
    
    There is some bug in pandas 0.12.0 replace function. This is a
    workaround.
    
    ser : Series
    d   : dict. 
    
    First ser is converted to an object data-type, because this is only
    intended to translate numeric data into strings.
    
    Then, for each key, value in d, all instances of key in ser are replaced
    with value.
    
    Finally, because we can't directly compare with np.nan, all null rows
    of ser are replaced with nanval.    
    """
    # Need to convert to object incase new val has different type
    ser = ser.copy().astype(np.object)
    
    # Replace each key, value
    for val, new_val in d.items():
        ser[ser == val] = new_val
        if pandas.isnull(val):
            raise ValueError("cannot compare to nan")
    
    # Replace nans
    ser[ser.isnull()] = nanval
    
    return ser


def translate_trial_matrix(trial_matrix):
    """Replace shorthand with longhand, eg, resp -> response."""
    trial_matrix = trial_matrix.copy()
    trial_matrix = trial_matrix.rename(columns={
        'rwsd': 'rewside',
        'resp': 'choice',
        'outc': 'outcome',
        'srvpos': 'servo_pos',
        'stppos': 'stepper_pos'
        })
    
    
    # How to deal with current trial here?
    if 'outcome' in trial_matrix:
        trial_matrix['outcome'] = my_replace(trial_matrix['outcome'], {
            HIT: 'hit', ERROR: 'error', SPOIL: 'spoil'},
            nanval='curr')
    if 'choice' in trial_matrix:
        trial_matrix['choice'] = my_replace(trial_matrix['choice'], {
            LEFT: 'left', RIGHT: 'right', NOGO: 'nogo'},
            nanval='curr')
    if 'rewside' in trial_matrix:
        trial_matrix['rewside'] = my_replace(trial_matrix['rewside'], {
            LEFT: 'left', RIGHT: 'right'})

    return trial_matrix
    

def get_trial_start_time(parsed_lines):
    """Returns the time of the start of the trial in seconds"""
    rows = my.pick_rows(parsed_lines, command=start_trial_token)
    
    if len(rows) > 1:
        raise ValueError("too many trial start lines")
    elif len(rows) == 0:
        return None
    else:
        return int(rows['time'].irow(0)) / 1000.
    
def get_trial_release_time(parsed_lines):
    """Returns the time of trial release in seconds"""
    rows = my.pick_rows(parsed_lines, command=trial_released_token)
    if len(rows) > 1:
        raise ValueError("too many trial relased lines")
    elif len(rows) == 0:
        return None
    else:
        return int(rows['time'].irow(0)) / 1000.

def get_trial_parameters(parsed_lines, command_string=trial_param_token):
    """Returns the value of trial parameters"""
    rec = {}
    rows = my.pick_rows(parsed_lines, command=command_string)
    for arg in rows['argument'].values:
        name, value = arg.split()
        rec[name.lower()] = int(value)
    return rec

def get_trial_results(parsed_lines, command_string=trial_result_token):
    """Returns the value of trial results"""
    # We can use the same code but another token
    return get_trial_parameters(parsed_lines, command_string=command_string)

def check_if_trial_released(trial):
    """Checks if ACK RELEASE_TRL is in trial"""
    for line in trial:
        sp_line = line.split()
        if len(sp_line) == 3 and sp_line[1:3] == [ack_token, release_trial_token]:
            return True
    return False


## Writing functions
def command_set_parameter(param_name, param_value):
    """Returns the command to use to set a parameter.
    
    TODO: error checking here for param_value as int, param_name as string
    without spaces, etc.
    """
    if int(param_value) == 0:
        print "warning: cannot send zeros"
    return 'SET %s %s' % (param_name, str(int(param_value)))

def command_release_trial():
    """Returns the command to use to release the current trial."""
    return release_trial_token