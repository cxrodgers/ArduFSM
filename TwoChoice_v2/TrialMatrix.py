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
 

    The first entry in lines_split_by_trial is taken to be info about setup,
    not about the first trial.
    
    Behavior depends on the length of lines_split_by_trial:
        0:  it is empty, so None is returned
        1:  only setup info, so None is returned
        >1: the first entry is ignored, and subsequent entries become
            rows in the resulting DataFrame.

    If a DataFrame is returned, then the columns in always_insert are
    always inserted, even if they weren't present. They will be inserted
    with np.nan, so the dtype should be numerical, not stringy.
    
    The main use-case is the response columns which are missing during the
    first trial but which most code assumes exists.
    """
    if len(lines_split_by_trial) < 1:
        return None
    
    rec_l = []
    for spline in lines_split_by_trial[1:]:
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
        
    # DataFrame
    trials_info = pandas.DataFrame.from_records(rec_l)
    
    # Define duration
    if 'release_time' in trials_info.columns and 'start_time' in trials_info.columns:
        trials_info['duration'] = trials_info['release_time'] - trials_info['start_time']
    else:
        trials_info['release_time'] = pandas.Series([], dtype=np.float)
        trials_info['start_time'] = pandas.Series([], dtype=np.float)
        trials_info['duration'] = pandas.Series([], dtype=np.float)
    
    # Reorder
    ordered_cols = ['start_time', 'release_time', 'duration']
    for col in sorted(trials_info.columns):
        if col not in ordered_cols:
            ordered_cols.append(col)
    trials_info = trials_info[ordered_cols]
    
    # Insert always_insert
    for col in always_insert:
        if col not in trials_info:
            trials_info[col] = np.nan
    
    # Name index
    trials_info.index.name = 'trial'

    return trials_info
