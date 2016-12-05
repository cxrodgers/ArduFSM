"""Functions for trial setting logic"""
import TrialSpeak
import TrialMatrix
import pandas

def send_params_and_release(params, chatter):
    # Set them
    for param_name, param_val in params.items():
        chatter.queued_write_to_device(
            TrialSpeak.command_set_parameter(
                param_name, param_val))
    
    # Release
    chatter.queued_write_to_device(TrialSpeak.command_release_trial())  
    
  

def is_current_trial_incomplete(translated_trial_matrix):
    if len(translated_trial_matrix) < 1:
        raise ValueError("no trials have begun")
    if 'choice' not in translated_trial_matrix.columns:
        raise ValueError("need translated matrix")
    
    return translated_trial_matrix['choice'].iat[-1] == 'curr'


def generate_trial_types():
    trial_types = pandas.DataFrame.from_records([
        {'name':'CV-L-1150-050', 'srvpos':1150, 'stppos':50, 'rewside':'left',},
        {'name':'CC-R-1150-150', 'srvpos':1150, 'stppos':150, 'rewside':'right',},
        {'name':'CV-L-1175-050', 'srvpos':1175, 'stppos':50, 'rewside':'left',},
        {'name':'CC-R-1175-150', 'srvpos':1175, 'stppos':150, 'rewside':'right',},
        ])
    trial_types.to_pickle('trial_types_2stppos')



class TrialSetter:
    """Object to determine state of trial and call scheduler as necessary"""
    def __init__(self, chatter, params_table, scheduler):
        self.initial_params_sent = False
        self.chatter = chatter
        self.params_table = params_table
        self.scheduler = scheduler
        self.last_released_trial = -1
    
    def send_initial_params_when_ready(self, splines):
        """Sends initial params at the right time
        
        Sets initial_params_sent when it's been done.        
        """
        ## Initialization stuff
        # Behavior depends on how much data has been received
        if len(splines) == 0:
            # No data received, or possibly munged data received.
            # Add some more error checks for this   
            # Are we starting at time 0? Is the encoding corrupted?
            # Is the TrialSpeak version right?
            return
        if len(splines) == 1:
            # Some data has been received, so the Arduino has booted up.
            # Add an error check that it is speaking our language here.
            # But no trials have occurred yet (splines[0] is setup info).
            # Send initial params if they haven't already been sent
            if not self.initial_params_sent:
                # Send each initial param
                iparams = self.params_table[self.params_table['send_on_init']]
                for param_name, param_val in iparams['init_val'].iteritems():
                    cmd = TrialSpeak.command_set_parameter(param_name, param_val) 
                    self.chatter.queued_write_to_device(cmd)
                    self.params_table.loc[
                        param_name, 'current-value'] = int(param_val)
                
                # Mark as sent
                self.initial_params_sent = True  
                    
    def update(self, splines, logfile_lines):
        """Main loop of trial setter
        
        Releases trials as necessary by parsing splines and calling scheduler
        """
        ## Initialization check
        # Try to send initial params
        if not self.initial_params_sent:
            self.send_initial_params_when_ready(splines)
        
        # Check if it worked. If not, we're not ready yet
        if not self.initial_params_sent:
            return

        ## Construct trial_matrix
        # Now we know that the Arduino has booted up and that the initial
        # params have been sent.
        # Construct trial_matrix
        #trial_matrix = TrialMatrix.make_trials_info_from_splines(splines)
        trial_matrix = TrialSpeak.make_trials_matrix_from_logfile_lines2(logfile_lines)
        current_trial = len(trial_matrix) - 1
        
        # Translate
        translated_trial_matrix = TrialSpeak.translate_trial_matrix(trial_matrix)
        
        ## Trial releasing logic
        # Was the last released trial the current one or the next one?
        if self.last_released_trial < current_trial:
            raise "unreleased trials have occurred, somehow"
            
        elif self.last_released_trial == current_trial:
            # The current trial has been released, or no trials have been released
            if current_trial == -1:
                # first trial has not even been released yet, nor begun
                params = self.scheduler.choose_params_first_trial(translated_trial_matrix)
                send_params_and_release(params, self.chatter)
                self.last_released_trial = current_trial + 1
                
            elif is_current_trial_incomplete(translated_trial_matrix):
                # Current trial has been released but not completed
                pass
                
            else:
                # Current trial has been completed. Next trial needs to be released.
                params = self.scheduler.choose_params(translated_trial_matrix)
                send_params_and_release(params, self.chatter)
                self.last_released_trial = current_trial + 1          
        
        elif self.last_released_trial == current_trial + 1:
            # Next trial has been released, but has not yet begun
            pass
        
        else:
            raise "too many trials have been released, somehow"    
        
        return translated_trial_matrix