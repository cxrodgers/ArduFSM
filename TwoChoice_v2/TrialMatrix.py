"""Module for generating and processing TrialMatrix objects.

This module contains functions to form a matrix of parameters and outcomes
on each trial. This is done using the communication protocol defined
by TrialSpeak.
"""
import TrialSpeak
import pandas, my, numpy as np

def make_trial_matrix_from_file(log_filename, translate=True, numericate=False):
    """Read data from file and make trial matrix.
    
    Wrapper around:
    TrialSpeak.read_lines_from_file
    TrialSpeak.split_by_trial
    make_trials_info_from_splines
    TrialSpeak.translate_trial_matrix
    numericate_trial_matrix
    
    
    This could probably be turned into an object with methods like
    .numericated, .translated, etc
    """
    # Read
    logfile_lines = TrialSpeak.read_lines_from_file(log_filename)
    
    # Spline
    lines_split_by_trial = TrialSpeak.split_by_trial(logfile_lines)
    
    # Make matrix
    trial_matrix = make_trials_info_from_splines(lines_split_by_trial)
    
    # Translate and/or numericate
    if translate:
        trial_matrix = TrialSpeak.translate_trial_matrix(trial_matrix)
        if numericate:
            trial_matrix = numericate_trial_matrix(trial_matrix)
    
    return trial_matrix
    

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
    

def numericate_trial_matrix(translated_trial_matrix):
    """Replaces strings with ints to allow anova
    
    * Insert prevchoice column by shifting choice
    * Dump trials unless choice is left or right, prevchoice is left or right,
      and outcome is hit or error. This drops spoiled and current trials.
    * Replace left with -1 and right with +1 in choice, prevchoice, and rewside
      and intify those columns.
    
    Return the result.
    """
    # Copy and add a prevchoice
    df = translated_trial_matrix.copy()
    df['prevchoice'] = df['choice'].shift(1)
    
    # Drop where choice, prevchoice are not equal to left or right
    df = my.pick_rows(df, 
        choice=['left', 'right'], prevchoice=['left', 'right'],
        rewside=['left', 'right'],
        outcome=['hit', 'error'])
    
    # Replace and intify
    df['choice'] = df['choice'].replace(
        {'left': -1, 'right': 1}).astype(np.int)
    df['prevchoice'] = df['prevchoice'].replace(
        {'left': -1, 'right': 1}).astype(np.int)
    df['rewside'] = df['rewside'].replace(
        {'left': -1, 'right': 1}).astype(np.int)    
    
    return df


## ANOVA stuff
def _run_anova(numericated_trial_matrix):
    """Helper function that runs anova without parsing stats.
    
    Returns None if LinAlgError or ValueError.
    """
    numericated_trial_matrix = numericated_trial_matrix.copy()

    # ANOVA choice ~ rewside * prevchoice (or possibly +)
    try:
        aov_res = my.stats.anova(numericated_trial_matrix, 'choice ~ rewside + prevchoice')
    except (np.linalg.LinAlgError, ValueError, TypeError):
        aov_res = None
    except NameError:
        # NameError occurs if the keywords do not exist in the matrix        
        s = "trial matrix must contain choice, rewside, and prevchoice. " \
            "Instead, contains: " + ', '.join(list(
                numericated_trial_matrix.columns))
        raise NameError(s)
    
    return aov_res

def pval_to_star(pval):
    if pval < .001:
        return '***'
    elif pval < .01:
        return '**'
    elif pval < .05:
        return '*'
    else:
        return ''
    
def anova_text_summarize(aov_res, variable='prevchoice', pos_word='Stay', 
    neg_word='Switch'):
    """Turn anova results into human-readable summary."""
    s = pos_word if aov_res['fit']['fit_' + variable] > 0 else neg_word
    s += ' %0.2f' % aov_res['ess']['ess_' + variable]
    s += pval_to_star(aov_res['pvals']['p_' + variable])
    return s

def run_anova(numericated_trial_matrix):
    """Run anova on trials info and return stats"""
    # Return variable
    ss = ''
    
    # Do nothing if insufficient data
    if len(numericated_trial_matrix) < 3:
        ss = 'insufficient data'
    
    else:
        # Try to run the anova
        aov_res = _run_anova(numericated_trial_matrix)
        
        # Test for anova error, like LinAlgError or ValueError
        if aov_res is None:
            ss = 'anova error'

        else:
            # Summarize stay, side, and correct biases
            ss += anova_text_summarize(aov_res, variable='prevchoice', 
                pos_word='Stay', neg_word='Switch') + '; '
            ss += anova_text_summarize(aov_res, variable='Intercept', 
                pos_word='Right', neg_word='Left') + '; '
            ss += anova_text_summarize(aov_res, variable='rewside', 
                pos_word='Correct', neg_word='Incorrect')

    return ss


def count_hits_by_type_from_trials_info(trials_info, split_key='trial_type'):    
    """Returns (nhit, ntot) for each value of split_key in trials_info as dict."""
    uniq_types = np.unique(trials_info[split_key])
    typ2perf = {}
    
    for typ in uniq_types:
        msk = trials_info[split_key] == typ
        typ2perf[typ] = calculate_nhit_ntot(trials_info[msk])
        
    return typ2perf


def count_hits_by_type(trials_info, split_key='trial_type'):    
    """Returns (nhit, ntot) for each value of split_key in trials_info as dict."""
    uniq_types = np.unique(trials_info[split_key])
    typ2perf = {}
    
    for typ in uniq_types:
        msk = trials_info[split_key] == typ
        typ2perf[typ] = calculate_nhit_ntot(trials_info[msk])
        
    return typ2perf

def calculate_nhit_ntot(df):
    """Return nhits and ntotal trials"""
    nhit = np.sum(df['outcome'] == 'hit')
    ntot = np.sum(df['outcome'] != 'curr')
    return nhit, ntot

def calculate_safe_perf(df):
    """Returns nhits / ntots, unless NaN, in which case 0."""
    nhit, ntot = calculate_nhit_ntot(df)
    return nhit / float(ntot) if ntot > 0 else 0.