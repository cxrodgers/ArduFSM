"""Contains various plotting objects to work with TwoChoice and LickTrain.

Currently there is a mixture of old and new approaches here.
* The Plotter object is intended to be a base class for all kinds of
plotters, but it looks like it's limited to only plotting by trial
(instead of, for instance, by time).
* Derived classes from Plotter (currently only PlotterByServoThrow is in
use) provide additional specifity by defining:
    assign_trial_type_to_trials_info
    get_list_of_trial_type_names
* PlotterByStimNumber looks like a general-purpose plotter for multiple
  kinds of stimuli.
* There are some older methods for plotting but I think they are out of date.

One finicky thing is the way the 'trial_types' are passed around, and
shared with the scheduler object. It also needs to be matched up with
scheduler trial_types. If this variable is intended to always be the same,
then we should just match on an index variable. If it is not intended to be
the same, then we should relax that assumption, but right now I think the
code assumes that it is.
"""

import numpy as np, pandas, time
import matplotlib.pyplot as plt
import my
import scipy.stats

# move these to TrialMatrix so we can phase this out
#from trials_info_tools import count_hits_by_type_from_trials_info, calculate_nhit_ntot
from TrialMatrix import count_hits_by_type_from_trials_info, calculate_nhit_ntot


import TrialSpeak, TrialMatrix
from TrialSpeak import YES, NO

o2c = {'hit': 'lightgreen', 'error': 'r', 'spoil': 'k', 'curr': 'white'}


def format_perf_string(nhit, ntot):
    """Helper function for turning hits and totals into a fraction."""
    perf = nhit / float(ntot) if ntot > 0 else 0.
    res = '%d/%d=%0.2f' % (nhit, ntot, perf)
    return res

def count_rewards(splines):
    """Counts the rewards delivered in each trial
    
    Returns : dict with the keys 'left auto', 'right auto', 'left manual',
        and 'right manual'. The values are arrays of the same length as
        splines containing the number of each event on each trial.
    """
    # Get the rewards by each trial in splines
    evname2token = {
        'left auto' : 'EV R_L',
        'right auto' : 'EV R_R',
        'left manual' : 'EV AAR_L',
        'right manual' : 'EV AAR_R',
        }
    evname2list = dict([(evname, []) for evname in evname2token])

    # Iterate over trials
    for nspline, spline in enumerate(splines):        
        # Iterate over events
        for evname, token in evname2token.items():
            # Count events of this type in this trial
            n_events = np.sum([s.strip().endswith(token) for s in spline])
            evname2list[evname].append(n_events)
    
    # Arrayify
    res = dict([(evname, np.asarray(l)) for evname, l in evname2list.items()])
    return res


class Plotter(object):
    """Base class for plotters by stim number or servo throw.
    
    Child classes MUST define the following:
    assign_trial_type_to_trials_info
    get_list_of_trial_type_names
    """
    def __init__(self, trial_plot_window_size=50):
        """Initialize base Plotter class."""
        # Size of trial window
        self.trial_plot_window_size = trial_plot_window_size
        
        # Anova caching
        self.cached_anova_text1 = ''
        self.cached_anova_len1 = 0
        self.cached_anova_text2 = ''
        self.cached_anova_len2 = 0       
    
    def init_handles(self):
        """Create graphics handles"""
        # Plot 
        f, ax = plt.subplots(1, 1, figsize=(11, 3))
        f.subplots_adjust(left=.45, right=.95, top=.75)
        
        # Make handles to each outcome
        label2lines = {}
        for outcome, color in o2c.items():
            if color == 'white':
                label2lines[outcome], = ax.plot(
                    [None], [None], 'o', label=outcome, color=color)
            else:
                label2lines[outcome], = ax.plot(
                    [None], [None], 'o', label=outcome, color=color, mec=color)                
        
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
        
        self.graphics_handles['suptitle'] = f.suptitle('', size='small')
        

        # create the window
        plt.show()
    
    def update_trial_type_parameters(self, lines):
        """Update parameters relating to trial type.
        
        Does nothing by default but child classes will redefine."""
        pass
    
    def update(self, filename):   
        """Read info from filename and update the plot"""
        ## Load data and make trials_info
        # Check log
        lines = TrialSpeak.read_lines_from_file(filename)
        splines = TrialSpeak.split_by_trial(lines)        
        
        # Really we should wait until we hear something from the arduino
        # Simply wait till at least one line has been received
        if len(splines) == 0 or len(splines[0]) == 0:
            return

        # Construct trial_matrix. I believe this will always have at least
        # one line in it now, even if it's composed entirely of Nones.
        trials_info = TrialMatrix.make_trials_info_from_splines(splines)

        ## Translate condensed trialspeak into full data
        # Put this part into TrialSpeak.py
        translated_trial_matrix = TrialSpeak.translate_trial_matrix(trials_info)
        
        # return if nothing to do
        if len(translated_trial_matrix) < 1:
            return
        
        # define the "bad" trials
        # these are marked differently and discounted from certain ANOVAs
        # maybe include user delivery trials too?
        if 'isrnd' in translated_trial_matrix:
            translated_trial_matrix['bad'] = ~translated_trial_matrix['isrnd']
        else:
            translated_trial_matrix['bad'] = False

        ## Define trial types, the ordering on the plot
        # Make any updates to trial type parameters (child-class-dependent)
        self.update_trial_type_parameters(lines)
        
        # Add type information to trials_info and generate type names
        translated_trial_matrix = self.assign_trial_type_to_trials_info(translated_trial_matrix)
        trial_type_names = self.get_list_of_trial_type_names()

        ## Count performance by type
        # Hits by type
        typ2perf = count_hits_by_type_from_trials_info(
            translated_trial_matrix[~translated_trial_matrix.bad])
        typ2perf_all = count_hits_by_type_from_trials_info(
            translated_trial_matrix)
        
        # Combined
        total_nhit, total_ntot = calculate_nhit_ntot(
            translated_trial_matrix[~translated_trial_matrix.bad])

        # Turn the typ2perf into ticklabels
        ytick_labels = typ2perf2ytick_labels(trial_type_names, 
            typ2perf, typ2perf_all)

        ## title string
        # number of rewards
        title_string = self.form_string_rewards(splines, 
            translated_trial_matrix)
        
        # This depends on rewside existing, which is only true for 2AC
        if 'rewside' in translated_trial_matrix.columns:
            title_string += '\n' + self.form_string_all_trials_perf(
                translated_trial_matrix)
            title_string += '\n' + self.form_string_unforced_trials_perf(
                translated_trial_matrix)

        ## PLOTTING
        # plot each outcome
        for outcome in ['hit', 'error', 'spoil', 'curr']:
            # Get rows corresponding to this outcome
            msk = translated_trial_matrix['outcome'] == outcome

            # Get the line corresponding to this outcome and set the xdata
            # to the appropriate trial numbers and the ydata to the trial types
            line = self.graphics_handles['label2lines'][outcome]
            line.set_xdata(np.where(msk)[0])
            line.set_ydata(translated_trial_matrix['trial_type'][msk].values)

        # plot vert bars where bad trials occurred
        msk = translated_trial_matrix['bad']
        line = self.graphics_handles['label2lines']['bad']
        line.set_xdata(np.where(msk)[0])
        line.set_ydata(translated_trial_matrix['trial_type'][msk])


        ## PLOTTING axis labels and title
        ax = self.graphics_handles['ax']
        f = self.graphics_handles['f']
        
        # Use the ytick_labels calculated above
        ax.set_yticks(range(len(trial_type_names)))
        ax.set_yticklabels(ytick_labels, size='small')
        
        # The ylimits go BACKWARDS so that trial types are from top to bottom
        ymax = np.max(ax.get_yticks())
        ymin = np.min(ax.get_yticks())
        ax.set_ylim((ymax + .5, ymin -.5))
        
        # The xlimits are a sliding window of size TRIAL_PLOT_WINDOW_SIZE
        ax.set_xlim((
            len(translated_trial_matrix) - self.trial_plot_window_size, 
            len(translated_trial_matrix)))    
        
        # title set above
        #~ ax.set_title(title_string, size='small')
        self.graphics_handles['suptitle'].set_text(title_string)
        
        ## plot division between L and R
        line = self.graphics_handles['label2lines']['divis']
        line.set_xdata(ax.get_xlim())
        line.set_ydata([np.mean(ax.get_yticks())] * 2)
        
        ## PLOTTING finalize
        plt.show()
        plt.draw()    

    def form_string_rewards(self, splines, translated_trial_matrix):
        """Form a string with the number of rewards on each side"""
        # Count rewards
        d = count_rewards(splines)

        # Stringify
        s = 'Rewards (auto/total): L=%d/%d R=%d/%d' % (
            d['left auto'].sum(), 
            d['left auto'].sum() + d['left manual'].sum(),
            d['right auto'].sum(), 
            d['right auto'].sum() + d['right manual'].sum(),
            )
        
        return s

    
    def form_string_all_trials_perf(self, translated_trial_matrix):
        """Form a string with side perf and anova for all trials"""
        side2perf_all = count_hits_by_type_from_trials_info(
            translated_trial_matrix, 
            split_key='rewside')     
        
        string_perf_by_side = self.form_string_perf_by_side(side2perf_all)
        
        if len(translated_trial_matrix) > self.cached_anova_len2 or self.cached_anova_text2 == '':
            numericated_trial_matrix = TrialMatrix.numericate_trial_matrix(
                translated_trial_matrix)
            anova_stats = TrialMatrix.run_anova(numericated_trial_matrix)
            self.cached_anova_text2 = anova_stats
            self.cached_anova_len2 = len(translated_trial_matrix)
        else:
            anova_stats = self.cached_anova_text2
        
        return 'All: ' + string_perf_by_side + '. Biases: ' + anova_stats
    
    def form_string_unforced_trials_perf(self, translated_trial_matrix):
        """Exactly the same as form_string_all_trials_perf, except that:
        
        We drop all trials where bad is True.
        We use cached_anova_len1 and cached_anova_text1 instead of 2.
        """
        side2perf = count_hits_by_type_from_trials_info(
            translated_trial_matrix[~translated_trial_matrix.bad], 
            split_key='rewside')

        string_perf_by_side = self.form_string_perf_by_side(side2perf)
        
        if len(translated_trial_matrix) > self.cached_anova_len1 or self.cached_anova_text1 == '':
            numericated_trial_matrix = TrialMatrix.numericate_trial_matrix(
                translated_trial_matrix[~translated_trial_matrix.bad])
            anova_stats = TrialMatrix.run_anova(numericated_trial_matrix)
            self.cached_anova_text2 = anova_stats
            self.cached_anova_len2 = len(translated_trial_matrix)
        else:
            anova_stats = self.cached_anova_text2
        
        return 'UF: ' + string_perf_by_side + '. Biases: ' + anova_stats        

    def form_string_perf_by_side(self, side2perf):
        s = ''
        if 'left' in side2perf:
            s += 'L: ' + \
                format_perf_string(side2perf['left'][0], side2perf['left'][1]) + '; '
        if 'right' in side2perf:
            s += 'R: ' + \
                format_perf_string(side2perf['right'][0], side2perf['right'][1]) + ';'        
        return s

    def plot_rewards_trace(self, n_rewards_a):
        ## PLOTTING REWARDS
        # Plot the rewards as a separate trace
        for line in self.graphics_handles['ax2'].lines:
            line.remove()    
        self.graphics_handles['ax2'].plot(
            np.arange(len(n_rewards_a)), n_rewards_a, 'k-')
        self.graphics_handles['ax2'].set_yticks(
            np.arange(np.max(n_rewards_a) + 2))
    
    def update_till_interrupt(self, filename, interval=.3):
        # update over and over
        PROFILE_MODE = False

        try:
            while True:
                self.update(filename)
                
                if not PROFILE_MODE:
                    time.sleep(interval)
                else:
                    break

        except KeyboardInterrupt:
            plt.close('all')
            print "Done."
        except:
            raise
        finally:
            pass



class PlotterByStimNumber(Plotter):
    """Plots performance by stim number."""
    def __init__(self, n_stimuli=6, **base_kwargs):
        # Initialize base
        super(PlotterByStimNumber, self).__init__(**base_kwargs)
        
        # Initialize me
        # This could be inferred
        self.n_stimuli = n_stimuli

    def update_trial_type_parameters(self, lines):
        """Looks for changes in number of stimuli.
        
        lines: read from file
        """
        pass
    
    def assign_trial_type_to_trials_info(self, trials_info):
        """Returns a copy of trials_info with a column called trial_type.
        
        Trial type is defined by this object as stim number.
        """
        trials_info = trials_info.copy()
        trials_info['trial_type'] = trials_info['stim_number']
        return trials_info

    def get_list_of_trial_type_names(self):
        """Return the name of each trial type.
        
        This object assumes left and right stimuli are alternating and that
        the very first trial_type is a left stimulus.
        
        Returns ['LEFT 0', 'RIGHT 1', 'LEFT 2', ...] up to self.n_stimuli
        """
        res = []
        for sn in range(self.n_stimuli):
            # All even are LEFT
            side = 'LEFT' if np.mod(sn, 2) == 0 else 'RIGHT'
            res.append(side + ' %d' % sn)        
        return res


class PlotterWithServoThrow(Plotter):
    """Object encapsulating the logic and parameters to plot trials by throw."""
    def __init__(self, trial_types, **base_kwargs):
        # Initialize base
        super(PlotterWithServoThrow, self).__init__(**base_kwargs)
        
        # Initialize me
        self.trial_types = trial_types
        
    def assign_trial_type_to_trials_info(self, trials_info):
        """Returns a copy of trials_info with a column called trial_type.
        
        We match the srvpos and stppos variables in trials_info to the 
        corresponding rows of self.trial_types. The index of the matching row
        is the trial type for that trial.
        
        Warnings are issued if keywords are missing, multiple matches are 
        found (in which case the first is used), or no match is found
        (in which case the first trial type is used, although this should
        probably be changed to None).
        """
        trials_info = trials_info.copy()
        
        # Set up the pick kwargs for how we're going to pick the matching type
        # The key is the name in self.trial_types, and the value is the name
        # in trials_info
        pick_kwargs = {'stppos': 'stepper_pos', 'srvpos': 'servo_pos', 
            'rewside': 'rewside'}
        
        # Test for missing kwargs
        warn_missing_kwarg = []
        for key, val in pick_kwargs.items():
            if val not in trials_info.columns:
                pick_kwargs.pop(key)
                warn_missing_kwarg.append(key)
        if len(warn_missing_kwarg) > 0:
            print "warning: missing kwargs to match trial type:" + \
                ' '.join(warn_missing_kwarg)
        
        # Iterate over trials
        # Could probably be done more efficiently with a groupby
        trial_types_l = []
        warn_no_matches = []
        warn_multiple_matches = []
        warn_missing_data = []
        warn_type_error = []
        for idx, ti_row in trials_info.iterrows():
            # Pick the matching row in trial_types
            trial_pick_kwargs = dict([
                (k, ti_row[v]) for k, v in pick_kwargs.items() 
                if not pandas.isnull(ti_row[v])])
            
            # Try to pick
            try:
                pick_idxs = my.pick(self.trial_types, **trial_pick_kwargs)
            except TypeError:
                # typically, comparing string with int
                warn_type_error.append(idx)
                pick_idxs = [0]
            
            # error check missing data
            if len(trial_pick_kwargs) < len(pick_kwargs):
                warn_missing_data.append(idx)            
            
            # error-check and reduce to single index
            if len(pick_idxs) == 0:
                # no match, use the first trial type
                1/0
                warn_no_matches.append(idx)
                pick_idx = 0
            elif len(pick_idxs) > 1:
                # multiple match
                warn_multiple_matches.append(idx)
                pick_idx = pick_idxs[0]
            else:
                # no error
                pick_idx = pick_idxs[0]
            
            # Store result
            trial_types_l.append(pick_idx)

        # issue warnings
        if len(warn_type_error) > 0:
            print "error: type error in pick on trials " + \
                ' '.join(map(str, warn_type_error))
        if len(warn_missing_data) > 0:
            print "error: missing data on trials " + \
                ' '.join(map(str, warn_missing_data))
        if len(warn_no_matches) > 0:
            print "error: no matches found in some trials " + \
                ' '.join(map(str, warn_no_matches))
        elif len(warn_multiple_matches) > 0:
            print "error: multiple matches found on some trials"

        # Put into trials_info and return
        trials_info['trial_type'] = trial_types_l
        return trials_info

    def get_list_of_trial_type_names(self):
        """Name of each trial type."""
        res = list(self.trial_types['name'])        
        return res



class PlotterPassiveDetect(Plotter):
    """Simple plotter"""
    def __init__(self, trial_types, **base_kwargs):
        # Initialize base
        super(PlotterPassiveDetect, self).__init__(**base_kwargs)
        
        # Initialize me
        self.trial_types = trial_types
        
    def assign_trial_type_to_trials_info(self, trials_info):
        """Returns a copy of trials_info with a column called trial_type.
        
        We match the srvpos and stppos variables in trials_info to the 
        corresponding rows of self.trial_types. The index of the matching row
        is the trial type for that trial.
        
        Warnings are issued if keywords are missing, multiple matches are 
        found (in which case the first is used), or no match is found
        (in which case the first trial type is used, although this should
        probably be changed to None).
        """
        trials_info = trials_info.copy()
        
        # Set up the pick kwargs for how we're going to pick the matching type
        # The key is the name in self.trial_types, and the value is the name
        # in trials_info
        pick_kwargs = {'isgo': 'isgo'}
        
        # Test for missing kwargs
        warn_missing_kwarg = []
        for key, val in pick_kwargs.items():
            if val not in trials_info.columns:
                pick_kwargs.pop(key)
                warn_missing_kwarg.append(key)
        if len(warn_missing_kwarg) > 0:
            print "warning: missing kwargs to match trial type:" + \
                ' '.join(warn_missing_kwarg)
        
        # Iterate over trials
        # Could probably be done more efficiently with a groupby
        trial_types_l = []
        warn_no_matches = []
        warn_multiple_matches = []
        warn_missing_data = []
        warn_type_error = []
        for idx, ti_row in trials_info.iterrows():
            # Pick the matching row in trial_types
            trial_pick_kwargs = dict([
                (k, ti_row[v]) for k, v in pick_kwargs.items() 
                if not pandas.isnull(ti_row[v])])
            
            # Try to pick
            try:
                pick_idxs = my.pick(self.trial_types, **trial_pick_kwargs)
            except TypeError:
                # typically, comparing string with int
                warn_type_error.append(idx)
                pick_idxs = [0]
            
            # error check missing data
            if len(trial_pick_kwargs) < len(pick_kwargs):
                warn_missing_data.append(idx)            
            
            # error-check and reduce to single index
            if len(pick_idxs) == 0:
                # no match, use the first trial type
                1/0
                warn_no_matches.append(idx)
                pick_idx = 0
            elif len(pick_idxs) > 1:
                # multiple match
                warn_multiple_matches.append(idx)
                pick_idx = pick_idxs[0]
            else:
                # no error
                pick_idx = pick_idxs[0]
            
            # Store result
            trial_types_l.append(pick_idx)

        # issue warnings
        if len(warn_type_error) > 0:
            print "error: type error in pick on trials " + \
                ' '.join(map(str, warn_type_error))
        if len(warn_missing_data) > 0:
            print "error: missing data on trials " + \
                ' '.join(map(str, warn_missing_data))
        if len(warn_no_matches) > 0:
            print "error: no matches found in some trials " + \
                ' '.join(map(str, warn_no_matches))
        elif len(warn_multiple_matches) > 0:
            print "error: multiple matches found on some trials"

        # Put into trials_info and return
        trials_info['trial_type'] = trial_types_l
        return trials_info

    def get_list_of_trial_type_names(self):
        """Name of each trial type."""
        res = list(self.trial_types['name'])        
        return res


## This is all for the updating by time, instead of trial
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



## Utility functions
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