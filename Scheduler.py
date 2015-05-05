"""Objects that choose the params for the next trial, given the history.

Each Scheduler object should respond to:
* choose_params(trial_matrix)
* choose_params_first_trial(trial_matrix)
and should return a dict of the params for the next trial.

Each Scheduler object should also be initialized with a 'trial_types'
DataFrame that contains all possible trial types to choose from, and should
choose one of its rows on each trial. In some cases it will only ever
choose from a subset of those trial types, but it should retain the full
trial_types DataFrame because this is used by plotter objects to determine
which trial types to display.

TODOs/gotchas:
* It's a little finicky the way trial_types is passed around different
scheduler objects, and needs to be kept in a format that is readable by
the plotter object. Not sure how to better handle this.
* The handling of sub_trial_types and picked_trial_types is ugly, especially
around SessionStarter which derives from ForcedAlternation.
* Currently, the received trial_matrix is translated ("real words") but
the returned params need to be untranslated ("TrialSpeak"). The untranslation
should probably be handled by whatever is calling Scheduler.
* It's weird that schedulers from different protocols (TwoChoice and LickTrain)
are mixed together here. Not sure how to better handle it. Probably
this file should contain only bare-bones schedulers and each protocol
contains its own more specific ones.
"""
import numpy as np
import my
from TrialSpeak import YES, NO, HIT
import TrialSpeak, TrialMatrix

class ForcedAlternation:
    def __init__(self, trial_types, **kwargs):
        self.name = 'forced alternation'
        self.params = {
            'FD': 'X',
            'RPB': 1,
            }
        self.trial_types = trial_types
    
    def generate_trial_params(self, trial_matrix):
        """Given trial matrix so far, generate params for next"""
        res = {}
        res['ISRND'] = NO
        
        if len(trial_matrix) == 0:
            # First trial, so pick at random from trial_types
            if hasattr(self, 'picked_trial_types'):
                idx = self.trial_types.index[np.random.randint(0, len(self.picked_trial_types))]
            else:
                idx = self.trial_types.index[np.random.randint(0, len(self.trial_types))]
            res['RWSD'] = self.trial_types['rewside'][idx]
            res['STPPOS'] = self.trial_types['stppos'][idx]
            res['SRVPOS'] = self.trial_types['srvpos'][idx]
        
        else:    
            # Not the first trial
            # First check that the last trial hasn't been released
            assert trial_matrix['release_time'].isnull().irow(-1)
            
            # But that it has been responded
            assert not trial_matrix['choice'].isnull().irow(-1)
            
            # Set side to left by default, and otherwise forced alt
            if len(trial_matrix) < 2:
                res['RWSD'] = 'left'
            else:
                # Get last trial
                last_trial = trial_matrix.irow(-1)
                if last_trial['choice'] == last_trial['rewside']:
                    res['RWSD'] = {'left': 'right', 'right':'left'}[last_trial['rewside']]
                else:
                    res['RWSD'] = last_trial['rewside']
            
            # Update the stored force dir
            self.params['FD'] = res['RWSD']
            
            # ugly hack to get Session Starter working
            if hasattr(self, 'picked_trial_types'):
                # Choose from trials from the forced side
                sub_trial_types = my.pick_rows(self.picked_trial_types, 
                    rewside=res['RWSD'])
                assert len(sub_trial_types) > 0                
            else:
                # Choose from trials from the forced side
                sub_trial_types = my.pick_rows(self.trial_types, 
                    rewside=res['RWSD'])
                assert len(sub_trial_types) > 0
            
            idx = sub_trial_types.index[np.random.randint(0, len(sub_trial_types))]
            
            res['STPPOS'] = self.trial_types['stppos'][idx]
            res['SRVPOS'] = self.trial_types['srvpos'][idx]

        
        # Untranslate the rewside
        # This should be done more consistently, eg, use real phrases above here
        # and only untranslate at this point.
        res['RWSD'] = {'left': 1, 'right': 2}[res['RWSD']]
        
        return res

    def choose_params_first_trial(self, trial_matrix):
        """Called when params for first trial are needed"""
        return self.generate_trial_params(trial_matrix)
    
    def choose_params(self, trial_matrix):
        """Called when params for next trial are needed."""
        return self.generate_trial_params(trial_matrix)


class ForcedAlternationLickTrain:
    def __init__(self, trial_types, **kwargs):
        self.name = 'forced alternation lick train'
        self.params = {
            'FD': 'X',
            'RPB': 1,
            }
        self.trial_types = trial_types
    
    def generate_trial_params(self, trial_matrix):
        """Given trial matrix so far, generate params for next"""
        res = {}
        
        if len(trial_matrix) == 0:
            idx = self.trial_types.index[np.random.randint(0, len(self.trial_types))]
            res['RWSD'] = self.trial_types['rewside'][idx]
        
        else:    
            # Not the first trial
            # First check that the last trial hasn't been released
            assert trial_matrix['release_time'].isnull().irow(-1)
            
            # But that it has been responded
            assert not trial_matrix['choice'].isnull().irow(-1)
            
            # Set side to left by default, and otherwise forced alt
            if len(trial_matrix) < 2:
                res['RWSD'] = 'left'
            else:
                # Get last trial
                last_trial = trial_matrix.irow(-1)
                if last_trial['outcome'] == 'hit':
                    res['RWSD'] = {'left': 'right', 'right':'left'}[last_trial['rewside']]
                else:
                    res['RWSD'] = last_trial['rewside']
            
            # Update the stored force dir
            self.params['FD'] = res['RWSD']

            # Choose from trials from the forced side
            sub_trial_types = my.pick_rows(self.trial_types, 
                rewside=res['RWSD'])
            assert len(sub_trial_types) > 0
            
            idx = sub_trial_types.index[np.random.randint(0, len(sub_trial_types))]

        
        # Untranslate the rewside
        # This should be done more consistently, eg, use real phrases above here
        # and only untranslate at this point.
        res['RWSD'] = {'left': 1, 'right': 2}[res['RWSD']]
        
        return res

    def choose_params_first_trial(self, trial_matrix):
        """Called when params for first trial are needed"""
        return self.generate_trial_params(trial_matrix)
    
    def choose_params(self, trial_matrix):
        """Called when params for next trial are needed."""
        return self.generate_trial_params(trial_matrix)


class RandomStim:
    def __init__(self, trial_types, **kwargs):
        """Initialize a new RandomStim scheduler.
        
        Chooses randomly from rows in 'trial_types'.
        """
        self.name = 'random stim'
        self.params = kwargs
        self.params['side'] = 'X'
        self.trial_types = trial_types.copy()
    
    def generate_trial_params(self, trial_matrix):
        """Given trial matrix so far, generate params for next trial.
        
        This object simply chooses randomly from all trial types, iid.
        Returns in TrialSpeak. TODO: return straight from trial_types,
        and let trial_setter handle the translation to TrialSpeak.
        """
        res = {}
        

        idx = self.trial_types.index[np.random.randint(0, len(self.trial_types))]
        res['RWSD'] = self.trial_types['rewside'][idx]
        res['STPPOS'] = self.trial_types['stppos'][idx]
        res['SRVPOS'] = self.trial_types['srvpos'][idx]
        res['ISRND'] = YES
        
        # Save current side for display
        self.params['side'] = res['RWSD']
        
        # Untranslate the rewside
        # This should be done more consistently, eg, use real phrases above here
        # and only untranslate at this point.
        res['RWSD'] = {'left': 1, 'right': 2}[res['RWSD']]
        
        return res

    def choose_params_first_trial(self, trial_matrix):
        """Called when params for first trial are needed"""
        return self.generate_trial_params(trial_matrix)
    
    def choose_params(self, trial_matrix):
        """Called when params for next trial are needed."""
        return self.generate_trial_params(trial_matrix)

class RandomStimPassiveDetect:
    def __init__(self, trial_types, **kwargs):
        """Initialize a new RandomStim scheduler.
        
        This is for PassiveDetect but I think it might work for everything.        
        Chooses randomly from rows in 'trial_types'.
        """
        self.name = 'random stim'
        self.params = kwargs
        self.trial_types = trial_types.copy()
    
    def generate_trial_params(self, trial_matrix):
        """Given trial matrix so far, generate params for next trial.
        
        This object simply chooses randomly from all trial types, iid.
        Returns in TrialSpeak. TODO: return straight from trial_types,
        and let trial_setter handle the translation to TrialSpeak.
        """
        # Choose a random row and convert to dict
        idx = self.trial_types.index[
            np.random.randint(0, len(self.trial_types))]
        res = self.trial_types.ix[idx].to_dict()
        
        # Save current side for display
        for key, val in res.items():
            self.params[key] = val
        
        # remove the "name" line from trial_types
        if 'name' in res:
            res.pop('name')
        
        # upcase all the keys
        res2 = {}
        for key, val in res.items():
            res2[key.upper()] = val
        
        # Remember to untranslate here if necessary
        return res2

    def choose_params_first_trial(self, trial_matrix):
        """Called when params for first trial are needed"""
        return self.generate_trial_params(trial_matrix)
    
    def choose_params(self, trial_matrix):
        """Called when params for next trial are needed."""
        return self.generate_trial_params(trial_matrix)

class ForcedSide:
    """Forces trials from a given side"""
    def __init__(self, trial_types, side, **kwargs):
        """Initialize a new ForcedSide scheduler.
        
        Chooses randomly from rows in 'trial_types', for which rewside=side.
        Side should be in {'left', 'right'}
        """
        self.name = 'forced side'
        self.params = kwargs
        self.trial_types = trial_types
        
        self.params['side'] = side
    
    def generate_trial_params(self, trial_matrix):
        """Given trial matrix so far, generate params for next trial.
        
        This object simply chooses randomly from all trial types, iid.
        Returns in TrialSpeak. TODO: return straight from trial_types,
        and let trial_setter handle the translation to TrialSpeak.
        """
        res = {}
        
        # Choose from trials from the forced side
        sub_trial_types = my.pick_rows(self.trial_types, 
            rewside=self.params['side'])
        assert len(sub_trial_types) > 0
        idx = sub_trial_types.index[np.random.randint(0, len(sub_trial_types))]

        # Set the rest of the params
        res['RWSD'] = self.trial_types['rewside'][idx]
        res['STPPOS'] = self.trial_types['stppos'][idx]
        res['SRVPOS'] = self.trial_types['srvpos'][idx]
        res['ISRND'] = NO
            
        # Untranslate the rewside
        # This should be done more consistently, eg, use real phrases above here
        # and only untranslate at this point.
        res['RWSD'] = {'left': 1, 'right': 2}[res['RWSD']]
        
        return res

    def choose_params_first_trial(self, trial_matrix):
        """Called when params for first trial are needed"""
        return self.generate_trial_params(trial_matrix)
    
    def choose_params(self, trial_matrix):
        """Called when params for next trial are needed."""
        return self.generate_trial_params(trial_matrix)

class SessionStarter(ForcedAlternation):
    """Scheduler for beginning session with forced alt and closest pos
    
    TODO: instead of changing scheduler with meta-scheduler, just have this
    one contain the logic for both FA and random, and switch itself
    """
    def __init__(self, trial_types, **kwargs):
        self.name = 'session starter'
        self.params = {
            'FD': 'X',
            'RPB': 1,
            }
        self.trial_types = trial_types

        # For simplicity, slice trial_types
        # Later, might want to reimplement the choosing rule instead
        lefts = my.pick_rows(self.trial_types, rewside='left')
        closest_left = lefts.srvpos.argmin()
        
        rights = my.pick_rows(self.trial_types, rewside='right')
        closest_right = rights.srvpos.argmin()
        
        # Because we maintain the indices, plotter will work correctly
        # Not quite right, we don't currently use indices, but this is a TODO
        self.picked_trial_types = self.trial_types.ix[
            [closest_left, closest_right]].copy()

class SessionStarterSrvMax(ForcedAlternation):
    """Scheduler for beginning session with forced alt and argmax srvpos
    
    """
    def __init__(self, trial_types, **kwargs):
        self.name = 'session starter'
        self.params = {
            'FD': 'X',
            'RPB': 1,
            }
        self.trial_types = trial_types

        # For simplicity, slice trial_types
        # Later, might want to reimplement the choosing rule instead
        lefts = my.pick_rows(self.trial_types, rewside='left')
        closest_left = lefts.srvpos.argmax()
        
        rights = my.pick_rows(self.trial_types, rewside='right')
        closest_right = rights.srvpos.argmax()
        
        # Because we maintain the indices, plotter will work correctly
        # Not quite right, we don't currently use indices, but this is a TODO
        self.picked_trial_types = self.trial_types.ix[
            [closest_left, closest_right]].copy()

class Auto:
    """Class for automatic training.
    
    Always begins with SessionStarter, then goes random.
    Switches to forced alt automatically based on biases.
    """
    def __init__(self, trial_types, debug=False, reverse_srvpos=False, **kwargs):
        self.name = 'auto'
        self.params = {
            'subsch': 'none',
            'status': 'X',
            }
        self.trial_types = trial_types.copy()
        
        # Initialize my contained types
        self.sub_schedulers = {}
        self.sub_schedulers['ForcedAlternation'] = \
            ForcedAlternation(trial_types=trial_types)
        self.sub_schedulers['RandomStim'] = \
            RandomStim(trial_types=trial_types)
        self.sub_schedulers['ForcedSide'] = \
            ForcedSide(trial_types=trial_types, side='right')
        if reverse_srvpos:
            self.sub_schedulers['SessionStarter'] = \
                SessionStarterSrvMax(trial_types=trial_types)
        else:
            self.sub_schedulers['SessionStarter'] = \
                SessionStarter(trial_types=trial_types)
        
        if debug:
            self.n_trials_session_starter = 2
            self.n_trials_forced_alt = 5
            self.n_trials_sticky = 3
            self.n_trials_recent_win = 10
            self.n_trials_recent_random_thresh = 2
        else:
            self.n_trials_session_starter = 8
            self.n_trials_forced_alt = 45
            self.n_trials_sticky = 6
            self.n_trials_recent_win = 32
            self.n_trials_recent_random_thresh = 8
        
        self.last_changed_trial = 0
        

    def generate_trial_params(self, trial_matrix):
        # already translated
        translated_trial_matrix = trial_matrix.copy()
        
        if len(translated_trial_matrix) < self.n_trials_session_starter:
            self.current_sub_scheduler = self.sub_schedulers['SessionStarter']
            self.params['status'] = 'start'
        elif len(translated_trial_matrix) < self.n_trials_forced_alt: # 60
            self.current_sub_scheduler = self.sub_schedulers['ForcedAlternation']
            self.params['status'] = 'start2'
        else:
            self.choose_scheduler_main_body(translated_trial_matrix)
        
        self.params['subsch'] = self.current_sub_scheduler.name
        
        return self.current_sub_scheduler.generate_trial_params(trial_matrix)

    def choose_scheduler_main_body(self, translated_trial_matrix):
        # Main body of session
        this_trial = len(translated_trial_matrix)
        
        # Do nothing if we've changed recently
        if this_trial < self.last_changed_trial + self.n_trials_sticky:
            return
        
        # Check whether we've had at least 10 random in the last 50
        recents = translated_trial_matrix['isrnd'].values[
            -self.n_trials_recent_win:]
        recent_randoms = recents.sum()
        if len(recents) == self.n_trials_recent_win and \
            recent_randoms < self.n_trials_recent_random_thresh:
            # Set to occasional random
            self.current_sub_scheduler = self.sub_schedulers['RandomStim']
            self.last_changed_trial = this_trial
            self.params['status'] = 'randchk' + str(this_trial)       
            return
        
        # Run the anova
        numericated_trial_matrix = TrialMatrix.numericate_trial_matrix(
            translated_trial_matrix)
        aov_res = TrialMatrix._run_anova(numericated_trial_matrix)        
        if aov_res is None:
            self.current_sub_scheduler = self.sub_schedulers['RandomStim']
            self.last_changed_trial = this_trial
            self.params['status'] = 'an_none' + str(this_trial)
            return
        
        # Take the largest significant bias
        # Actually, better to take the diff of perf between sides for forced
        # side. Although this is a bigger issue than unexplainable variance
        # shouldn't be interpreted.
        side2perf_all = TrialMatrix.count_hits_by_type(
            translated_trial_matrix, split_key='rewside')     
        if 'left' in side2perf_all and 'right' in side2perf_all:
            lperf = side2perf_all['left'][0] / float(side2perf_all['left'][1])
            rperf = side2perf_all['right'][0] / float(side2perf_all['right'][1])
            sideperf_diff = rperf - lperf
        else:
            sideperf_diff = 0
        
        # Decide whether stay, side, or neither bias is critical
        if aov_res['pvals']['p_prevchoice'] < 0.05 and aov_res['fit']['fit_prevchoice'] > 0:
            # Stay bias
            self.last_changed_trial = this_trial
            self.params['status'] = 'antistay' + str(this_trial)
            self.current_sub_scheduler = self.sub_schedulers['ForcedAlternation']
        elif np.abs(sideperf_diff) > .25:
            # Side bias
            self.last_changed_trial = this_trial
            self.params['status'] = 'antiside' + str(this_trial)
            self.current_sub_scheduler = self.sub_schedulers['ForcedSide']
            
            if sideperf_diff > 0:
                self.current_sub_scheduler.params['side'] = 'left'
            else:
                self.current_sub_scheduler.params['side'] = 'right'
        else:
            # No bias
            self.last_changed_trial = this_trial
            self.params['status'] = 'good' + str(this_trial)
            self.current_sub_scheduler = self.sub_schedulers['RandomStim']        

    def choose_params_first_trial(self, trial_matrix):
        """Called when params for first trial are needed"""
        return self.generate_trial_params(trial_matrix)
    
    def choose_params(self, trial_matrix):
        """Called when params for next trial are needed."""
        return self.generate_trial_params(trial_matrix)
    
    