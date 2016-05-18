"""Module for the main loop in Python"""
import os.path
import pandas
import numpy as np
from TrialSpeak import YES, NO, MD


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
        ('STPPOS',  MD,       1, 1, 0, 0, 0),
        ('RWSD',    MD,       1, 1, 0, 0, 0),
        ('SRVPOS',  MD,       1, 1, 0, 0, 0),
        ('ISRND',   NO,       1, 1, 0, 0, 0),
        ('RD_L',    MD,       0, 0, 1, 1, 1),
        ('RD_R',    MD,       0, 0, 1, 1, 1),
        ('ITI',     50,       0, 0, 1, 0, 1),
        ('PSW',     1,        0, 0, 0, 0, 0),
        ('TO',      9000,     0, 0, 1, 0, 1),       
        ('TOE',     YES,      0, 0, 1, 0, 1),
        ('MRT',     1,        0, 0, 1, 0, 1),
        ('STPSPD',  MD,       0, 0, 0, 1, 1),
        ('STPFR',   50,      0, 0, 0, 1, 1),
        ('2PSTP',   MD,       0, 0, 0, 1, 1),
        ('SRVST',   1000,     0, 0, 0, 1, 0),
        ('STPIP',   50,       0, 0, 0, 1, 1),
        ('SRVFAR',  1900,     0, 0, 0, 1, 1),
        ('SRVTT',   MD,       0, 0, 0, 1, 1),
        ('RWIN',    45000,    0, 0, 1, 0, 1),
        ('IRI',     500,      0, 0, 0, 0, 0),    
        ('TOUT',    6,        0, 0, 1, 1, 1),
        ('RELT',    6,        0, 0, 1, 1, 1),
        ('STPHAL',  MD,       0, 0, 0, 1, 1),
        ('HALPOS',  MD,       0, 0, 0, 1, 1),
        ('DIRDEL',  NO,       1, 1, 0, 0, 0),
        ('OPTO',    NO,       1, 1, 0, 0, 0),
        ],
        columns=('name', 'init_val', 'required_ET', 'reported_ET', 
            'ui-accessible', 'rig-dependent', 'send_on_init'),
        ).set_index('name')
    bool_list = ['required_ET', 'reported_ET', 'ui-accessible', 
        'rig-dependent', 'send_on_init']
    params_table[bool_list] = params_table[bool_list].astype(np.bool)
    
    return params_table

def get_params_table_licktrain():
    """Params table for lick train

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

def get_params_table_passive_detect():
    """Params table for lick train

    Note that the value 0 may never be sent to the Arduino, due to limitations
    in the Arudino-side conversion of strings to int. To send boolean values,
    use YES and NO. It is undetermined whether negative values should be allowed.

    We currently define MD as 0, since this is not an allowable value to send.
    """
    params_table = pandas.DataFrame([
        ('ITI',     2000,     0, 1, 1, 0, 1),            
        ('ISGO',    MD,       1, 1, 0, 0, 0),
        ('NSTPS',   1,        1, 1, 1, 0, 1),
        ('STPT',    10,       1, 0, 0, 0, 0),
        ('MRT',     1,        0, 0, 1, 0, 1),
        ('RWIN',    2000,     0, 0, 1, 0, 1),
        ('IRI',     1500,     0, 0, 0, 0, 1),    
        ('2PSTP',   MD,       0, 0, 0, 1, 1),
        ('TOUT',    6,        0, 0, 1, 1, 1),
        ('RELT',    6,        0, 0, 1, 1, 1),
        ('STPSPD',  MD,       0, 0, 1, 1, 1),
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

def get_serial_port(rigname):
    """Get the serial port for the specified rigname"""
    d = {
        'L0': '/dev/ttyACM0',
        'L1': '/dev/ttyACM0', 
        'L2': '/dev/ttyACM1', 
        'L3': '/dev/ttyACM2', 
        'B1': '/dev/ttyACM0',
        'B2': '/dev/ttyACM1',
        'B3': '/dev/ttyACM2',
        'B4': '/dev/ttyACM3',
        'B5': '/dev/ttyACM0',
        }
    
    try:
        return d[rigname]
    except KeyError:
        raise ValueError("can't find serial port for rig %s" % rigname)        

def get_rig_specific(rigname):
    """Return a dict of params for each rig.
    
    Currently hard coded but should probably be read from disk.
    """
    if rigname == 'L0':
        return {
            'STPSPD': 30,
            '2PSTP': YES,
            'SRVFAR' : 1100,
            'SRVTT': 2000,
            'RD_L': 60,
            'RD_R': 55,
            'STPHAL': YES,
            'HALPOS': 50,
            }
    
    elif rigname == 'L1':
        return {
            'STPSPD': 30,
            '2PSTP': NO,
            'SRVTT': 2000,
            'RD_L': 60,
            'RD_R': 50,
            'STPHAL': YES,
            'HALPOS': 150,
            }
    
    elif rigname == 'L2':
        return {
            'STPSPD': 30,
            '2PSTP': NO,
            'SRVTT': 2000,
            'RD_L': 21,
            'RD_R': 30,
            'STPHAL': YES,
            'HALPOS': 50,
            }
    
    elif rigname == 'L3':
        return {
            'STPSPD': 30,
            '2PSTP': YES,
            'SRVTT': 2000,
            'RD_L': 25,
            'RD_R': 26,
            'STPHAL': YES,
            'HALPOS': 50,
            }  
            
    elif rigname == 'B3':
        return {
            'STPSPD': 30,
            '2PSTP': YES,
            'SRVFAR' : 1100,
            'SRVTT': 2000,
            'RD_L': 95,
            'RD_R': 110,
            'STPHAL': YES,
            'HALPOS': 50,
            }              

    elif rigname == 'B4':
        return {
            'STPSPD': 30,
            '2PSTP': YES,
            'SRVFAR' : 1100,
            'SRVTT': 2000,
            'RD_L': 140,
            'RD_R': 200,
            'STPHAL': YES,
            'HALPOS': 50,
            }     

    elif rigname == 'B1':
        return {
            'STPSPD': 30,
            '2PSTP': YES,
            'SRVFAR' : 1100,
            'SRVTT': 2000,
            'RD_L': 105,
            'RD_R': 105,
            'STPHAL': YES,
            'HALPOS': 50,
            }  

    elif rigname == 'B2':
        return {
            'STPSPD': 30,
            '2PSTP': YES,
            'SRVFAR' : 1100,
            'SRVTT': 2000,
            'RD_L': 80,
            'RD_R': 105,
            'STPHAL': YES,
            'HALPOS': 50,
            }        

    elif rigname == 'B5':
        return {
            'STPSPD': 30,
            '2PSTP': YES,
            'SRVFAR' : 1100,
            'SRVTT': 2000,
            'RD_L': 70,
            'RD_R': 95,
            'STPHAL': NO,
            'HALPOS': 50,
            'TO': 100,
            'RWIN': 100,
            }       
            
    else:
        raise ValueError("cannot find rig-specific for %s" % rigname)

def get_rig_specific_passive_detect(rigname):
    """Return a dict of params for each rig.
    
    Currently hard coded but should probably be read from disk.
    """
    return {
        'STPSPD': 2,
        '2PSTP': YES,
        'RD_L': 50,
        'RD_R': 50,
        }

def get_rig_specific_licktrain(rigname):
    """Return a dict of params for each rig for licktrain.
    """
    if rigname == 'L1':
        return {
            'RD_L': 60,
            'RD_R': 31,
            }
    
    elif rigname == 'L2':
        return {
            'RD_L': 23,
            'RD_R': 21,
            }
    
    elif rigname == 'L3':
        return {
            'RD_L': 16,
            'RD_R': 25,
            }  
    
    elif rigname == 'B1':
        return {
            'RD_L': 95,
            'RD_R': 95,
            }  

    elif rigname == 'B2':
        return {
            'RD_L': 70,
            'RD_R': 95,
            }              

    elif rigname == 'B3':
        return {
            'RD_L': 100,
            'RD_R': 60,
            }  
    
    elif rigname == 'B4':
        return {
            'RD_L': 70,
            'RD_R': 70,
            }  
    
    else:
        raise ValueError("cannot find rig-specific for %s" % rigname)

def assign_rig_specific_params(rigname, params_table):
    """Get rig-specific params and assign to init and current val in table"""
    d = get_rig_specific(rigname)
    for param_name, param_value in d.items():
        try:
            params_table.loc[param_name, 'init_val'] = param_value
        except KeyError:
            raise ValueError("cannot find param named %s" % param_name)
    return params_table

def assign_rig_specific_params_licktrain(rigname, params_table):
    """Get rig-specific params and assign to init and current val in table"""
    d = get_rig_specific_licktrain(rigname)
    for param_name, param_value in d.items():
        try:
            params_table.loc[param_name, 'init_val'] = param_value
        except KeyError:
            raise ValueError("cannot find param named %s" % param_name)
    return params_table

def assign_rig_specific_params_passive_detect(rigname, params_table):
    """Get rig-specific params and assign to init and current val in table"""
    d = get_rig_specific_passive_detect(rigname)
    for param_name, param_value in d.items():
        try:
            params_table.loc[param_name, 'init_val'] = param_value
        except KeyError:
            raise ValueError("cannot find param named %s" % param_name)
    return params_table

def get_trial_types(name, directory='~/dev/ArduFSM/stim_sets'):
    """Loads and returns the trial types file"""
    
    filename = os.path.join(os.path.expanduser(directory), name)
    try:
        trial_types = pandas.read_csv(filename)
    except IOError:
        raise ValueError("cannot find trial type file %s" % name)
    return trial_types
