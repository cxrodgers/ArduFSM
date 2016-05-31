"""Defines the parameters that are shared between Python and Arduino"""
import os.path
import pandas
import numpy as np
from ArduFSM.TrialSpeak import YES, NO, MD


def get_params_table():
    """Params table

    These are all the parameters that the Arduino code uses.
    Columns:
        name            The abbreviation used to set the param.
        init_val        The value that the Python code uses by default, if it isn't
                        set in any other way. If this is MD ("must-define"),
                        then it must be set by something, either at the beginning
                        of the session or on each trial.
        required_ET     If True, then it is required to be set on each trial.
                        Currently this is ignored, though we should implement
                        error checking for it on both sides.
                        init_val should probably be ignored for required_ET,
                        unless we want to interpret it as some sort of default?
        reported_ET     If True, then its value is reported by the Arduino on 
                        each trial, using the TRLP command.
                        Currently this is hand-copied to the Arduino code.
                        Eventually, we probably want to default to all params
                        reported and no params required, and then set it from
                        Python side.
        ui_accessible   If True, then the UI provides a mechanism for setting it.
                        This is simply to make the UI less overwhelming, and
                        because some params seem unlikely to ever change during
                        a session.
        rig_dependent   If True, then this parameter is expected to vary by rig.
                        A rig-specific params file will be loaded and used to
                        set this param. If it is not specified by that file,
                        its init_val is used (unless it is MD).
        send_on_init    If True, then this parameter is sent before the first
                        trial begins. Any param that is not send_on_init and
                        not required_ET will use Arduino defaults, which really
                        only applies to params that we don't expect to ever change.

    Note that the value 0 may never be sent to the Arduino, due to limitations
    in the Arudino-side conversion of strings to int. To send boolean values,
    use YES and NO. It is undetermined whether negative values should be allowed.

    We currently define MD as 0, since this is not an allowable value to send.
    """
    params_table = pandas.DataFrame([
        ('RWSD',    MD,       1, 1, 0, 0, 0),
        ('MRT',     1,        0, 1, 1, 0, 1),
        ('RWIN',    45000,    0, 0, 0, 0, 1),
        ('IRI',     500,      0, 0, 1, 0, 0),    
        ('TOUT',    6,        0, 0, 1, 1, 1),
        ('RELT',    6,        0, 0, 1, 1, 1),
        ('RD_L',    MD,       0, 0, 1, 1, 1),
        ('RD_R',    MD,       0, 0, 1, 1, 1),
        ],
        columns=('name', 'init_val', 'required_ET', 'reported_ET', 
            'ui-accessible', 'rig-dependent', 'send_on_init'),
        ).set_index('name')
    bool_list = ['required_ET', 'reported_ET', 'ui-accessible', 
        'rig-dependent', 'send_on_init']
    params_table[bool_list] = params_table[bool_list].astype(np.bool)
    
    return params_table
   

