"""Module for generating and processing TrialMatrix objects.

This module contains functions to form a matrix of parameters and outcomes
on each trial. This is done using the communication protocol defined
by TrialSpeak.
"""
import TrialSpeak
import pandas, my, numpy as np



def make_trials_info_from_splines(lines_split_by_trial):
    """Parse out the parameters and outcomes from the lines in the logfile
    
    For each trial, the following parameters are extracted:
        trial_start : time in seconds at which TRL_START was issued
        trial_released: time in seconds at which trial was released
        All parameters listed for each trial.
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
        
        # Append results
        rec_l.append(rec)
    
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
    
    # Name index
    trials_info.index.name = 'trial'

    return trials_info
