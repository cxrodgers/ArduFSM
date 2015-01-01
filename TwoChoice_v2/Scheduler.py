"""Module for logic to choose params for next trial"""
import numpy as np
import my
from TrialSpeak import YES, NO


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
            
            
            # Use the forced side to choose from trial_types
            sub_trial_types = my.pick_rows(self.trial_types, rewside=res['RWSD'])
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



class RandomStim:
    def __init__(self, trial_types, **kwargs):
        """Initialize a new RandomStim scheduler.
        
        Chooses randomly from rows in 'trial_types'.
        """
        self.name = 'random stim'
        self.params = kwargs
        self.params['side'] = 'X'
        self.trial_types = trial_types
    
    def generate_trial_params(self, trial_matrix):
        """Given trial matrix so far, generate params for next trial.
        
        This object simply chooses randomly from all trial types, iid.
        Returns in TrialSpeak. TODO: return straight from trial_types,
        and let trial_setter2 handle the translation to TrialSpeak.
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
        and let trial_setter2 handle the translation to TrialSpeak.
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
        self.trial_types = self.trial_types.ix[[closest_left, closest_right]]

class Auto:
    """Class for automatic training.
    
    Always begins with SessionStarter, then goes random.
    Switches to forced alt automatically based on biases.
    """
    pass