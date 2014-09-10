import numpy as np, pandas, time
import matplotlib.pyplot as plt
import my
import scipy.stats
import trials_info_tools # replace this with specifics

o2c = {'hit': 'g', 'error': 'r', 'spoil': 'k', 'curr': 'white'}


def format_perf_string(nhit, ntot):
    """Helper function for turning hits and totals into a fraction."""
    perf = nhit / float(ntot) if ntot > 0 else 0.
    res = '%d/%d=%0.2f' % (nhit, ntot, perf)
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
    
    def update_trial_type_parameters(self, lines):
        """Update parameters relating to trial type.
        
        Does nothing by default but child classes will redefine."""
        pass
    
    def update(self, filename):   
        """Read info from filename and update the plot"""
        ## Load data and make trials_info
        # Read file
        with file(filename) as fi:
            lines = fi.readlines()

        # Split by trial
        splines = trials_info_tools.split_by_trial(lines)

        if len(splines) <= 1:
            # Probably just the first trial
            return

        # Make trials_info
        trials_info = trials_info_tools.make_trials_info_from_splines(splines)


        ## Define trial types, the ordering on the plot
        # Make any updates to trial type parameters (child-class-dependent)
        self.update_trial_type_parameters(lines)
        
        # Add type information to trials_info and generate type names
        trials_info = self.assign_trial_type_to_trials_info(trials_info)
        trial_type_names = self.get_list_of_trial_type_names()

        
        ## Count performance by type
        # Hits by type
        typ2perf = trials_info_tools.count_hits_by_type_from_trials_info(
            trials_info[~trials_info.bad])
        typ2perf_all = trials_info_tools.count_hits_by_type_from_trials_info(
            trials_info)
        
        # Hits by side
        side2perf = trials_info_tools.count_hits_by_type_from_trials_info(
            trials_info[~trials_info.bad], split_key='rewside')
        side2perf_all = trials_info_tools.count_hits_by_type_from_trials_info(
            trials_info, split_key='rewside')            
        
        # Combined
        total_nhit, total_ntot = trials_info_tools.calculate_nhit_ntot(
            trials_info[~trials_info.bad])

        # Turn the typ2perf into ticklabels
        ytick_labels = typ2perf2ytick_labels(trial_type_names, 
            typ2perf, typ2perf_all)


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
        if len(trials_info) > self.cached_anova_len1 or self.cached_anova_text1 == '':
            anova_stats = trials_info_tools.run_anova(
                trials_info, remove_bad=True)
            self.cached_anova_text1 = anova_stats
            self.cached_anova_len1 = len(trials_info)
        else:
            anova_stats = self.cached_anova_text1
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
        if len(trials_info) > self.cached_anova_len2 + 5 or self.cached_anova_text2 == '':
            anova_stats = trials_info_tools.run_anova(
                trials_info, remove_bad=False)
            self.cached_anova_text2 = anova_stats
            self.cached_anova_len2 = len(trials_info)
        else:
            anova_stats = self.cached_anova_text2
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
        #~ line.set_xdata(ax.get_xlim())
        #~ line.set_ydata([self.servo_throw - .5] * 2)
        
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
    def __init__(self, pos_near=1150, pos_delta=25, servo_throw=8,
        **base_kwargs):
        # Initialize base
        super(PlotterWithServoThrow, self).__init__(**base_kwargs)
        
        # Initialize me
        self.pos_near = pos_near
        self.pos_delta = pos_delta
        self.servo_throw = servo_throw        
    
    def update_trial_type_parameters(self, lines):
        """Looks for changes in servo throw or pos delta params.
        
        lines: read from file
        """
        # update servo_throw in case it has increased
        st_lines = filter(lambda line: 'SET ST ' in line, lines)
        if len(st_lines) > 0:
            st_line = st_lines[-1]
            inferred_servo_throw = int(st_line.strip().split()[-1])
            
            # only update if increased
            if inferred_servo_throw > self.servo_throw:
                self.servo_throw = inferred_servo_throw

        # extract pos_delta from history
        st_lines = filter(lambda line: 'SET PD ' in line, lines)
        if len(st_lines) > 0:
            st_line = st_lines[-1]
            inferred_pos_delta = int(st_line.strip().split()[-1])
            self.pos_delta = inferred_pos_delta    
    
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