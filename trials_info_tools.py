"""Methods for parsing and dealing with TrialsInfo"""
import ArduFSM


def load_trials_info_from_file(filename):
    """Load trials_info from file."""
    # Read file
    with file(filename) as fi:
        lines = fi.readlines()

    # Split by trial
    splines = ArduFSM.plot.split_by_trial(lines)

    # Form dataframe
    trials_info = make_trials_info_from_splines(splines)    
    
    return trials_info

def make_trials_info_from_splines(splines):
    ## Make trials_info
    # Identify spoiled (forced or rewarded) trials
    bad_trials, force_trials_type = identify_spoiled_trials(splines)

    # Identify trial outcomes and types
    rewarded_side, trial_outcomes = identify_trial_outcomes(splines)
    
    # Position of servo
    raw_servo_positions = identify_servo_positions(splines)
    
    # Stim number
    stim_numbers = identify_stim_numbers(splines)
    
    # Get trials info
    trials_info = form_trials_info(rewarded_side, trial_outcomes, 
        bad_trials)
    
    
    ## Stuff to put into form_trials_info, or otherwise normalize
    # Add in servo throw (put this in form_trials_info)
    trials_info['servo_position'] = raw_servo_positions

    # stim_number
    trials_info['stim_number'] = stim_numbers
    
    # Add in trial times
    trials_info['trial_time'] = identify_trial_times(splines)

    return trials_info

def form_trials_info(rewarded_side, trial_outcomes, bad_trials):
    """Concatenates provided data, sets dtypes, add prevhoice and choice
    
    TODO: make this work for empty inputs
    """
    df = pandas.concat([
        pandas.Series(rewarded_side, dtype=np.int, name='rewside'),
        #pandas.Series(trial_types, dtype=np.int, name='typ'),
        pandas.Series(trial_outcomes, name='outcome'),
        pandas.Series(bad_trials, dtype=np.bool, name='bad'),],
        axis=1, verify_integrity=True)
    
    # add a choice column: -1 spoil, 0 go left, 1 go right
    df['choice'] = df['rewside'].copy()    
    df['choice'][
        (df.outcome == 'error') &
        (df.rewside == 0)] = 1
    df['choice'][
        (df.outcome == 'error') &
        (df.rewside == 1)] = 0
    
    df['choice'][df.outcome == 'spoil'] = -1
    
    # add a lastchoice column:
    df['prevchoice'] = df['choice'].shift(1)
    df['prevchoice'][df.prevchoice.isnull()] = -1
    df['prevchoice'] = df['prevchoice'].astype(np.int)
    return df



def split_by_trial(lines):
    """Takes all lines from the file and splits by TRIAL START
    
    Returns: splines, a list of list of lines, each beginning with
    TRIAL START (which is when the current trial params are determined).
    """
    # Split trials
    trial_starts = np.where([line.startswith('TRIAL START')
        for line in lines])[0]
    splines = []
    for nstart in range(len(trial_starts)-1):
        splines.append(lines[trial_starts[nstart]:trial_starts[nstart+1]])
    
    # Last trial
    if len(trial_starts) >= 1:
        splines.append(lines[trial_starts[-1]:])
    
    return splines

def identify_spoiled_trials(splines):
    """Identify spoiled trials, with manual reward or forced
    
    Manual reward: any trial containing 'ACK REWARD'
        (though technically this only spoils if occurs before response)
        (and also some ACK REWARDs are ignored if delivered outside respwin)
    
    Forced trial: any trial after a FORCE L or FORCE R and before a FORCE X
        All FORCE commands have a latency of one trial to take effect,
        because the current trial params are set at the beginning.

    """
    
    # Identify the trials where a FORCE was issued
    force_trials = np.where([
        np.any([line.startswith('ACK FORCE') for line in tlines])
        for tlines in splines])[0]
    
    # If the force was in the last (current) trial, skip because nothing
    # has happened as a result of this yet
    force_trials = force_trials[force_trials < len(splines) - 1]
    
    # Identify what type of force it was (the last FORCE of the trial)
    # this seems to be something of a bottleneck
    force_trials_type = [
        filter(lambda line: line.startswith('ACK FORCE'), 
            splines[trial])[-1].strip()[-1]
        for trial in force_trials]
    
    # Set bad trials as those after FORCE L/R and before FORCE X
    bad_trials = np.zeros(len(splines), dtype=np.bool)
    for nforce in range(len(force_trials)-1):
        # If it wasn't X, spoil the next string of trials
        if force_trials_type[nforce] != 'X':
            # We add 1 here because of the 1-trial latency
            bad_trials[
                force_trials[nforce] + 1:force_trials[nforce + 1] + 1] = 1
    
    # Deal with the case where we are currently in a force block
    if len(force_trials_type) >= 1 and force_trials_type[-1] != 'X':
        bad_trials[force_trials[-1] + 1:] = 1
    
    # Trials with manual reward
    for nspline, spline in enumerate(splines):
        # But may not have actually been delivered
        if 'ACK REWARD\r\n' in spline:
            bad_trials[nspline] = 1

    return bad_trials, force_trials_type

def identify_trial_outcomes(splines):
    """Identify side (L=0, R=1) and outcome ('hit', 'error', 'spoil', 'curr')"""
    trial_types = []
    trial_outcomes = []
    for nspline, spline in enumerate(splines):
        if 'TRIAL SIDE L\r\n' in spline:
            trial_types.append(0)
        else:
            trial_types.append(1)
        
        if 'TRIAL OUTCOME hit\r\n' in spline:
            trial_outcomes.append('hit')
        elif 'TRIAL OUTCOME error\r\n' in spline:
            trial_outcomes.append('error')
        elif 'TRIAL OUTCOME spoil\r\n' in spline:
            trial_outcomes.append('spoil')
        elif nspline == len(splines) - 1:
            trial_outcomes.append('curr')
        else:
            print "warning: unknown trial type"
            trial_outcomes.append('spoil')
            #1/0
    trial_types = np.asarray(trial_types)
    trial_outcomes = np.asarray(trial_outcomes)

    return trial_types, trial_outcomes

def identify_servo_positions(splines):
    servo_pos_l = []
    for spline in splines:
        line = filter(lambda line: line.startswith('TRIAL SERVO_POS'), spline)[0]
        servo_pos_l.append(int(line.split()[-1]))
    return np.asarray(servo_pos_l)

def identify_stim_numbers(splines):
    res = []
    for spline in splines:
        line = filter(lambda line: line.startswith('TRIAL STIM_NUMBER'), spline)[0]
        res.append(int(line.split()[-1]))
    return np.asarray(res)    

def identify_trial_times(splines):
    """Return time of each TRIAL START in splines"""
    res_l = []
    for spline in splines:
        match_line = filter(lambda line: line.startswith('TRIAL START'), spline)[0]
        res_l.append(int(match_line.split()[-1]))
    return np.asarray(res_l, dtype=np.int)

def identify_servo_retract_times(splines):
    """Return time that servo began to retract, hard-coded as 15 11
    
    Returns: Series of times in s, indexed by the entry in splines
    """
    res_l = []
    idx_l = []
    for nspline, spline in enumerate(splines):
        # Find the state change line
        match_lines = filter(
            lambda line: 'STATE CHANGE 15 11' in line, spline)
        
        # There should be 1 hit, except in rare cases
        if len(match_lines) == 1:
            # Append result and nspline as index
            res_l.append(int(match_lines[0].split()[0]))
            idx_l.append(nspline)
        elif len(match_lines) == 0:
            # no state change found
            # this is only okay on the most recent ("current") trial
            if nspline != len(splines) - 1:
                print "error: cannot find state change in non-last trial"
        else:
            # should never find multiple instances
            raise ValueError("multiple state changes per spline")

    return pandas.Series(res_l, index=idx_l, dtype=np.float) / 1000.

def count_hits_by_type(trial_types, trial_outcomes, bad_trials):    
    uniq_types = np.unique(trial_types)
    typ2perf = {}
    
    for typ in uniq_types:
        msk = trial_types == typ
        nhit = np.sum((trial_outcomes[msk] == 'hit') & ~bad_trials[msk])
        ntot = np.sum((trial_outcomes[msk] != 'curr')& ~bad_trials[msk])
        typ2perf[typ] = (nhit, ntot)
        
    return typ2perf

def count_hits_by_type_from_trials_info(trials_info, split_key='trial_type'):    
    """Returns (nhit, ntot) for each value of split_key in trials_info as dict."""
    uniq_types = np.unique(trials_info[split_key])
    typ2perf = {}
    
    for typ in uniq_types:
        msk = trials_info[split_key] == typ
        typ2perf[typ] = calculate_nhit_ntot(trials_info[msk])
        
    return typ2perf

def calculate_nhit_ntot(df):
    nhit = np.sum(df['outcome'] == 'hit')
    ntot = np.sum(df['outcome'] != 'curr')
    return nhit, ntot

def _run_anova(trials_info, remove_bad=False):
    """Helper function that runs anova without parsing stats.
    
    Returns None if LinAlgError or ValueError.
    """
    trials_info = trials_info.copy()
    
    # Remove trials with outcome == spoil or choice == -1 or prevchoice = -1
    trials_info = trials_info[
        (trials_info.choice != -1) &
        (trials_info.prevchoice != -1) &
        trials_info.outcome.isin(['hit', 'error'])]
    
    # Optionally remove bad
    if remove_bad:
        trials_info = trials_info[~trials_info.bad]
    
    # Replace 0s with -1s
    trials_info['choice'][trials_info.choice == 0] = -1
    trials_info['rewside'][trials_info.rewside == 0] = -1
    trials_info['prevchoice'][trials_info.prevchoice == 0] = -1

    # ANOVA choice ~ rewside * prevchoice (or possibly +)
    try:
        aov_res = my.stats.anova(trials_info, 'choice ~ rewside + prevchoice')
    except (np.linalg.LinAlgError, ValueError, TypeError):
        aov_res = None
    
    return aov_res
    

def run_anova(trials_info, remove_bad=False):
    """Run anova on trials info and return stats"""
    # Return variable
    ss = ''
    
    # Do nothing if insufficient data
    if len(trials_info) < 10:
        ss = 'insufficient data'
    
    else:
        # Try to run the anova
        aov_res = _run_anova(trials_info, remove_bad=remove_bad)
        
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