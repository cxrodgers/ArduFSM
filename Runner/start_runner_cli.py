#!/usr/bin/python
"""Framework for setting up parameters for each behavioral session.

1.  The user provides the following *session parameters*:
        board
        box
        mouse
    This information could also be provided by an automated trainer.

2.  Each of the session parameters is used to look up *specific parameters*
    (i.e., reward duration, stimulus set, video device). There are three
    types of specific parameters: C, Python, and build. Within each type
    of specific parameter, any conflict is resolved in this order:
    mouse, board, box.
    
    The following build parameters must be specified at this point:
        protocol_name
        script_name
        serial_port

3.  A build environment ("sandbox") is created. The protocol is copied
    into a "Autosketch" subdirectory. The script is copied into a "Script"
    subdirectory. The C parameters are written as a C header file into
    the "Autosketch" subdirectory. The Python parameters are written
    in JSON format to the "Script" subdirectory.

5.  The Arduino code in "Autosketch" is compiled and uploaded to the
    serial port.

6.  The Python script is called in a subprocess.
"""
from __future__ import absolute_import

import os
import shutil
import json
import subprocess
from . import Sandbox
from . import ParamLookups
import argparse
import sys

def main(mouse, board, box, experimenter, **other_python_parameters):
    """Get specific parameters, create sandbox, and call the python script.
    
    mouse, board, box : session parameters as strings
        These are used to collect the specific parameters using
        ParamLookups.base.get_specific_parameters_from_user_input
    
    experimenter : also passed to create_sandbox just to create sandbox
    
    All other keyword arguments will be added to the Python parameters,
    so they will be written to the json file that is available to the 
    Python script.
    """
    # Create a place to keep sandboxes
    sandbox_root = os.path.expanduser('~/sandbox_root')
    if not os.path.exists(sandbox_root):
        os.mkdir(sandbox_root)

    # Where to look for protocols by name
    protocol_root = os.path.expanduser('~/dev/ArduFSM')
        
    # Get session parameters from user (board number, etc)
    user_input = {'mouse': mouse, 'board': board, 'box': box,
        'experimenter': experimenter}

    # Look up the specific parameters
    specific_parameters = \
        ParamLookups.base.get_specific_parameters_from_user_input(user_input)
    
    # Add in the other python parameters
    specific_parameters['Python'].update(other_python_parameters)

    # Use the sandbox parameters to create the sandbox
    sandbox_paths = Sandbox.create_sandbox(user_input, 
        sandbox_root=sandbox_root)

    # Copy protocol to sandbox
    Sandbox.copy_protocol_to_sandbox(
        sandbox_paths,
        build_parameters=specific_parameters['build'], 
        protocol_root=protocol_root)

    # Write the C parameters
    Sandbox.write_c_config_file(
        sketch_path=sandbox_paths['sketch'],
        c_parameters=specific_parameters['C'])

    # Write the Python parameters
    Sandbox.write_python_parameters(
        sandbox_paths, 
        python_parameters=specific_parameters['Python'], 
        script_name=specific_parameters['build']['script_name'])

    # Compile and upload
    Sandbox.compile_and_upload(sandbox_paths, specific_parameters)

    # Call Python process
    # Extract some subprocess kwargs from the build dict
    subprocess_kwargs = {}
    for kwarg in ['nrows', 'ncols', 'xpos', 'ypos', 'zoom']:
        try:
            subprocess_kwargs[kwarg] = specific_parameters['build'][
                'subprocess_window_' + kwarg]
        except KeyError:
            continue
    Sandbox.call_python_script(
        script_path=sandbox_paths['script'], 
        script_name=specific_parameters['build']['script_name'],
        **subprocess_kwargs
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Collect mouse, board, box')
    parser.add_argument('--mouse', help='mouse name', required=True)
    parser.add_argument('--board', help='board name', required=True)
    parser.add_argument('--box', help='box name', required=True)
    #~ print parser.parse_args()
    pargs = parser.parse_args()
    main(mouse=pargs.mouse, board=pargs.board, box=pargs.box)