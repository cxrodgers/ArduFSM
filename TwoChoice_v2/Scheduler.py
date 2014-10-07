"""Module for logic to choose params for next trial"""
import numpy as np
import my


class ForcedAlternation:
    def __init__(self, trial_types):
        self.name = 'forced alternation'
        self.params = {
            'FD': 'X',
            'RPB': 1,
            }
        self.trial_types = trial_types
    
    def generate_trial_params(self, trial_matrix):
        """Given trial matrix so far, generate params for next"""
        res = {}
        
        if len(trial_matrix) == 0:
            # First trial, so pick at random from trial_types
            idx = self.trial_types.index[np.random.randint(0, len(self.trial_types))]
            res['RWSD'] = self.trial_types['rewside'][idx]
            res['STPPOS'] = self.trial_types['stppos'][idx]
            res['SRVPOS'] = self.trial_types['srvpos'][idx]
            res['ITI'] = np.random.randint(10000)
        
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
            res['ITI'] = np.random.randint(10000)
            
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
