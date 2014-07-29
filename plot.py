import numpy as np, pandas, time
import matplotlib.pyplot as plt
import my
import scipy.stats

o2c = {'hit': 'g', 'error': 'r', 'spoil': 'k', 'curr': 'white'}

def format_perf_string(nhit, ntot):
    """Helper function for turning hits and totals into a fraction."""
    perf = nhit / float(ntot) if ntot > 0 else 0.
    res = '%d/%d=%0.2f' % (nhit, ntot, perf)
    return res

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

def run_anova(trials_info, remove_bad=False):
    """Run anova on trials info and return stats"""
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
    
    # Do nothing if insufficient data
    ss = ''
    if len(trials_info) >= 10:
        # ANOVA choice ~ rewside * prevchoice (or possibly +)
        try:
            aov_res = my.stats.anova(trials_info, 'choice ~ rewside + prevchoice')
        except np.linalg.LinAlgError:
            # eg, always go left
            return 'lin alg error'
        
        # Summarize stay, side, and correct biases
        ss += anova_text_summarize(aov_res, variable='prevchoice', 
            pos_word='Stay', neg_word='Switch') + '; '
        ss += anova_text_summarize(aov_res, variable='Intercept', 
            pos_word='Right', neg_word='Left') + '; '
        ss += anova_text_summarize(aov_res, variable='rewside', 
            pos_word='Correct', neg_word='Incorrect')

    else:
        ss = 'insufficient data'
    
    #~ # Pval on global perf
    #~ try:
        #~ pval = scipy.stats.binom_test(
            #~ side2perf[0][0] + side2perf[1][0],
            #~ side2perf[0][1] + side2perf[1][1])
    #~ except KeyError:
        #~ pval = 1.0
    
    return ss



class PlotterWithServoThrow:
    """Object encapsulating the logic and parameters to plot trials by throw."""
    def __init__(self, pos_near=1150, pos_delta=25, servo_throw=8,
        trial_plot_window_size=50):
        self.pos_near = pos_near
        self.pos_delta = pos_delta
        self.servo_throw = servo_throw
        self.trial_plot_window_size = trial_plot_window_size
    
    def init_handles(self):
        """Create graphics handles"""
        # Plot 
        f, ax = plt.subplots(1, 1, figsize=(11, 4))
        f.subplots_adjust(left=.35, right=.95, top=.75)
        
        # Make handles to each outcome
        label2lines = {}
        for outcome, color in o2c.items():
            label2lines[outcome], = ax.plot(
                [None], [None], 'o', label=outcome, color=color)
        
        # Plot the bads
        label2lines['bad'], = ax.plot(
            [None], [None], '|', label='bad', color='k', ms=10)

        # Plot a horizontal line at SERVO_THROW if available
        label2lines['divis'], = ax.plot(
            [None], [None], 'k-', label='divis')

        # Separate y-axis for rewards
        ax2 = ax.twinx()
        ax2.set_ylabel('rewards')

        # Store graphics handles
        self.graphics_handles = {
            'f': f, 'ax': ax, 'ax2': ax2, 'label2lines': label2lines}
        
        # create the window
        plt.show()
        
    def assign_trial_type_to_trials_info(self, trials_info):
        """Returns a copy of trials_info with a column called trial_type.
        
        # Sequentially assign from LEFT to RIGHT in increasing servo throw
        # eg LEFT 1150, LEFT 1175, LEFT 1200, RIGHT 1150, RIGHT 1175, RIGHT 1200
        """
        trials_info = trials_info.copy()
        
        # Check if any don't integer divide by pos_delta
        if np.any(np.mod(trials_info['servo_position'] - self.pos_near, 
            self.pos_delta) != 0):
            print "error: raw servo positions do not divide by POS_DELTA"
        
        # Divide by pos_delta
        integer_positions = (
            trials_info['servo_position'] - self.pos_near) / self.pos_delta
        
        # Check if any are out of range
        if np.any(integer_positions < 0) or np.any(
            integer_positions >= self.servo_throw):
            print "warning: positions below or above servo throw thresholds"
            integer_positions[integer_positions < 0] = 0
            integer_positions[integer_positions >= self.servo_throw] = \
                self.servo_throw - 1

        # Store integer position
        trials_info['servo_intpos'] = integer_positions
        
        # Finally combine with side info
        trials_info['trial_type'] = \
            trials_info['rewside'] * self.servo_throw + integer_positions
        
        return trials_info

    def get_list_of_trial_type_names(self):
        """Name of each trial type."""
        res = \
            ['LEFT %d' % n for n in range(self.servo_throw)] + \
            ['RIGHT %d' % n for n in range(self.servo_throw)]
        
        return res
    
    def update(self, filename):    
        ## Load data and make trials_info
        # Read file
        with file(filename) as fi:
            lines = fi.readlines()

        # Split by trial
        splines = split_by_trial(lines)

        # Make trials_info
        trials_info = make_trials_info_from_splines(splines)


        ## Define trial types, the ordering on the plot
        # update servo_throw in case it has increased
        st_lines = filter(lambda line: 'SET ST ' in line, lines)
        if len(st_lines) > 0:
            st_line = st_lines[-1]
            inferred_servo_throw = int(st_line.strip().split()[-1])
            
            # only update if increased
            if inferred_servo_throw > self.servo_throw:
                self.servo_throw = inferred_servo_throw
        
        # Add type information to trials_info and generate type names
        trials_info = self.assign_trial_type_to_trials_info(trials_info)
        trial_type_names = self.get_list_of_trial_type_names()

        
        ## Count performance by type
        # Hits by type
        typ2perf = count_hits_by_type_from_trials_info(
            trials_info[~trials_info.bad])
        typ2perf_all = count_hits_by_type_from_trials_info(trials_info)
        
        # Hits by side
        side2perf = count_hits_by_type_from_trials_info(
            trials_info[~trials_info.bad], split_key='rewside')
        side2perf_all = count_hits_by_type_from_trials_info(
            trials_info, split_key='rewside')            
        
        # Combined
        total_nhit, total_ntot = calculate_nhit_ntot(trials_info[~trials_info.bad])

        # Turn the typ2perf into ticklabels
        ytick_labels = typ2perf2ytick_labels(trial_type_names, typ2perf, typ2perf_all)


        ## count rewards
        # Get the rewards by each trial in splines
        n_rewards_l = []
        for nspline, spline in enumerate(splines):
            n_rewards = np.sum(map(lambda s: 'EVENT REWARD' in s, spline))
            n_rewards_l.append(n_rewards)
        n_rewards_a = np.asarray(n_rewards_l)
        
        # Match those onto the rewards from each side
        l_rewards = np.sum(n_rewards_a[(trials_info['rewside'] == 0).values])
        r_rewards = np.sum(n_rewards_a[(trials_info['rewside'] == 1).values])
        
        # turn the rewards into a title string
        title_string = '%d rewards L; %d rewards R;\n' % (l_rewards, r_rewards)
        
        
        ## A line of info about unforced trials
        title_string += 'UF: '
        if 0 in side2perf:
            title_string += 'L: ' + \
                format_perf_string(side2perf[0][0], side2perf[0][1]) + '; '
        if 1 in side2perf:
            title_string += 'R: ' + \
                format_perf_string(side2perf[1][0], side2perf[1][1]) + ';'
        anova_stats = run_anova(trials_info, remove_bad=True)
        title_string += '. Biases: ' + anova_stats
        title_string += '\n'
        
        
        ## A line of info about all trials
        title_string += 'All: '
        if 0 in side2perf_all:
            title_string += 'L_A: ' + \
                format_perf_string(side2perf_all[0][0], side2perf_all[0][1]) + '; '
        if 1 in side2perf_all:
            title_string += 'R_A: ' + \
                format_perf_string(side2perf_all[1][0], side2perf_all[1][1])
        anova_stats = run_anova(trials_info, remove_bad=False)
        title_string += '. Biases: ' + anova_stats
        
        ## PLOTTING REWARDS
        # Plot the rewards as a separate trace
        for line in self.graphics_handles['ax2'].lines:
            line.remove()    
        self.graphics_handles['ax2'].plot(
            np.arange(len(n_rewards_a)), n_rewards_a, 'k-')
        self.graphics_handles['ax2'].set_yticks(
            np.arange(np.max(n_rewards_a) + 2))


        ## PLOTTING
        # plot each outcome
        for outcome in ['hit', 'error', 'spoil', 'curr']:
            # Get rows corresponding to this outcome
            msk = trials_info['outcome'] == outcome

            # Get the line corresponding to this outcome and set the xdata
            # to the appropriate trial numbers and the ydata to the trial types
            line = self.graphics_handles['label2lines'][outcome]
            line.set_xdata(np.where(msk)[0])
            line.set_ydata(trials_info['trial_type'][msk])
        
        # plot vert bars where bad trials occurred
        msk = trials_info['bad']
        line = self.graphics_handles['label2lines']['bad']
        line.set_xdata(np.where(msk)[0])
        line.set_ydata(trials_info['trial_type'][msk])


        ## PLOTTING axis labels and title
        ax = self.graphics_handles['ax']
        
        # Use the ytick_labels calculated above
        ax.set_yticks(range(len(trial_type_names)))
        ax.set_yticklabels(ytick_labels, size='small')
        
        # The ylimits go BACKWARDS so that trial types are from top to bottom
        ax.set_ylim((len(trial_type_names) - .5, -.5))
        
        # The xlimits are a sliding window of size TRIAL_PLOT_WINDOW_SIZE
        ax.set_xlim((
            len(trials_info) - self.trial_plot_window_size, 
            len(trials_info)))    
        
        # title set above
        ax.set_title(title_string, size='medium')
        
        ## plot division between L and R
        line = self.graphics_handles['label2lines']['divis']
        line.set_xdata(ax.get_xlim())
        line.set_ydata([self.servo_throw - .5] * 2)
        
        ## PLOTTING finalize
        plt.show()
        plt.draw()    
    
    def update_till_interrupt(self, filename):
        # update over and over
        PROFILE_MODE = False

        try:
            while True:
                self.update(filename)
                
                if not PROFILE_MODE:
                    time.sleep(.3)
                else:
                    break

        except KeyboardInterrupt:
            plt.close('all')
            print "Done."
        except:
            raise
        finally:
            pass



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

def form_trials_info(rewarded_side, trial_outcomes, bad_trials):
    """Concatenates provided data, sets dtypes, add prevhoice and choice"""
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




def update_by_time_till_interrupt(plotter, filename):
    # update over and over
    PROFILE_MODE = False

    try:
        while True:
            # This part differs between the by trial and by time functions
            # Update_by_time should be updating the data, not replotting
            for line in plotter['ax'].lines:
                line.remove()
            
            update_by_time(plotter, filename)
            
            if not PROFILE_MODE:
                time.sleep(.3)
            else:
                break

    except KeyboardInterrupt:
        plt.close('all')
        print "Done."
    except:
        raise
    finally:
        pass



def init_by_time(**kwargs):
    # Plot 
    f, ax = plt.subplots(figsize=(10, 2))
    f.subplots_adjust(left=.2, right=.95, top=.85)

    # create the window
    plt.show()

    return {'f': f, 'ax': ax}

def update_by_time(plotter, filename):
    ax = plotter['ax']
    #~ label2lines = plotter['label2lines']    
    
    with file(filename) as fi:
        lines = fi.readlines()

    #rew_lines = filter(lambda line: line.startswith('REWARD'), lines)
    rew_lines_l = filter(lambda line: 'EVENT REWARD_L' in line, lines)
    rew_times_l = np.array(map(lambda line: int(line.split()[0])/1000., 
        rew_lines_l))
    rew_lines_r = filter(lambda line: 'EVENT REWARD_R' in line, lines)
    rew_times_r = np.array(map(lambda line: int(line.split()[0])/1000., 
        rew_lines_r))

    if len(rew_times_l) + len(rew_times_r) == 0:
        counts_l, edges = [0], [0, 1]
        counts_r, edges = [0], [0, 1]
    else:
        binlen = 20
        bins = np.arange(0, 
            np.max(np.concatenate([rew_times_l, rew_times_r])) + 2* binlen, 
            binlen)
        counts_l, edges = np.histogram(rew_times_l, bins=bins)
        counts_r, edges = np.histogram(rew_times_r, bins=bins)

    ax.plot(edges[:-1], counts_l, 'b')
    ax.plot(edges[:-1], counts_r, 'r')
    ax.set_xlabel('time (s)')
    ax.set_ylabel('rewards')
    ax.set_title('%d %d rewards' % tuple(map(len, [rew_times_l, rew_times_r])))
    plt.draw()
    plt.show()    
    
    
    
def make_trials_info_from_splines(splines):
    ## Make trials_info
    # Identify spoiled (forced or rewarded) trials
    bad_trials, force_trials_type = identify_spoiled_trials(splines)

    # Identify trial outcomes and types
    rewarded_side, trial_outcomes = identify_trial_outcomes(splines)
    
    # Position of servo
    raw_servo_positions = identify_servo_positions(splines)
    
    # Get trials info
    trials_info = form_trials_info(rewarded_side, trial_outcomes, 
        bad_trials)
    
    # Add in servo throw (put this in form_trials_info)
    trials_info['servo_position'] = raw_servo_positions

    return trials_info


def typ2perf2ytick_labels(trial_type_names, typ2perf, typ2perf_all):
    """Go through types and make ytick label about the perf for each."""
    ytick_labels = []
    for typnum, typname in enumerate(trial_type_names):
        tick_label = typname + ':'
        
        if typnum in typ2perf:
            nhits, ntots = typ2perf[typnum]
            tick_label += ' Unforced:%03d/%03d' % (nhits, ntots)
            if ntots > 0:
                tick_label += '=%0.2f' % (float(nhits) / ntots)
            tick_label += '.'
        
        if typnum in typ2perf_all:
            nhits, ntots = typ2perf_all[typnum]
            tick_label += ' All:%03d/%03d' % (nhits, ntots)
            if ntots > 0:
                tick_label += '=%0.2f' % (float(nhits) / ntots)
            tick_label += '.'        
    
        ytick_labels.append(tick_label)
    
    return ytick_labels