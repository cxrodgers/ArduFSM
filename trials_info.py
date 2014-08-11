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
    trials_info = ArduFSM.plot.make_trials_info_from_splines(splines)    
    
    return trials_info