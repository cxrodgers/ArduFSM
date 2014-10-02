"""Module for generating and processing TrialMatrix objects.

This module contains functions to form a matrix of parameters and outcomes
on each trial. This is done using the communication protocol defined
by TrialSpeak.
"""
import TrialSpeak
import pandas, my, numpy as np



def make_trials_info_from_splines(lines_split_by_trial, 
    always_insert=('resp', 'outc')):
    """Parse out the parameters and outcomes from the lines in the logfile
    
    For each trial, the following parameters are extracted:
        trial_start : time in seconds at which TRL_START was issued
        trial_released: time in seconds at which trial was released
        All parameters listed for each trial.
    
    Always inserts columns for always_insert, even if they weren't present.
    The main use-case is the response columns which are missing during the
    first trial but which most code assumes exists.
    
    Currently returns None if no data available.
    """
    rec_l = []
    for spline in lines_split_by_trial:
        # Parse into time, cmd, argument with helper function
        parsed_lines = TrialSpeak.parse_lines_into_df(spline)
        
        # Trial timings (seconds)
        rec = {}
        rec['start_time'] = TrialSpeak.get_trial_start_time(parsed_lines)
        rec['release_time'] = TrialSpeak.get_trial_release_time(parsed_lines)
        
        # Trial parameters
        trial_params = TrialSpeak.get_trial_parameters(parsed_lines)
        rec.update(trial_params)
        
        # Trial results
        trial_results = TrialSpeak.get_trial_results(parsed_lines)
        rec.update(trial_results)
        
        # Append results
        rec_l.append(rec)
    
    if len(lines_split_by_trial) == 0:
        # Or if we couldn't find parameters above?
        return None
    
    # DataFrame
    trials_info = pandas.DataFrame.from_records(rec_l)
    
    # Define duration
    trials_info['duration'] = trials_info['release_time'] - trials_info['start_time']
    
    # Reorder
    ordered_cols = ['start_time', 'release_time', 'duration']
    for col in sorted(trials_info.columns):
        if col not in ordered_cols:
            ordered_cols.append(col)
    trials_info = trials_info[ordered_cols]
    
    # Insert always_insert
    for col in always_insert:
        if col not in trials_info:
            trials_info[col] = ''
    
    # Name index
    trials_info.index.name = 'trial'

    return trials_info


#~ def assign_outcome(trial_matrix):
    #~ """Assigns an 'outcome' column based on 'rewside' and 'choice'.
    
    #~ This should not be necessary because it is handled on the arduino.
    
    #~ Silently does nothing if missing those columns.
    #~ Returns a copy.
    #~ I suppose this is protocol-specific since it assumes 2AC.
    #~ """
    #~ trial_matrix = trial_matrix.copy()
    
    #~ if 'outcome' not in trial_matrix:
        #~ raise ValueError("outcome column missing")

    #~ if 'choice' not in trial_matrix:
        #~ raise ValueError("choice column missing")
        #~ return trial_matrix

    #~ if 'rewside' not in trial_matrix:
        #~ raise ValueError("rewside column missing")
        #~ return trial_matrix
    
    #~ # error by default
    #~ trial_matrix['outcome'] = 'error'
    
    #~ # hit if choice == rewside
    #~ trial_matrix['outcome'][
        #~ trial_matrix['rewside'] == trial_matrix['choice']] = 'hit'
    
    #~ # spoil if choice == 'nogo'
    #~ trial_matrix['outcome'][trial_matrix['choice'] == 'nogo'] = 'spoil'
    
    #~ # Set the last one to 'current'
    #~ trial_matrix['choice'].ix[trial_matrix.index[-1]] = 'current'
    
    #~ return trial_matrix