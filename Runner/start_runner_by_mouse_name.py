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

import os
import shutil
import json
import subprocess
import Sandbox
import ParamLookups
import ParamLookups.base

# Create a place to keep sandboxes
sandbox_root = os.path.expanduser('~/sandbox_root')
if not os.path.exists(sandbox_root):
    os.mkdir(sandbox_root)

# Where to look for protocols by name
protocol_root = os.path.expanduser('~/dev/ArduFSM')

def get_dummy_user_input():
    """Dummy function returning simulated user input"""
    return {
        'board': 'CR2',
        'box': 'CR2',
        'mouse': 'KF80',
    }

def get_user_input_from_keyboard():
    """Get user to type the board, box, and mouse"""
    board = raw_input("Enter board: ")
    board = board.upper().strip()
    box = raw_input("Enter box: ")
    box = box.upper().strip()
    mouse = raw_input("Enter mouse: ")
    mouse = mouse.upper().strip()
    
    return {
        'board': board,
        'box': box,
        'mouse': mouse,
    }
    
# Get mouse name
mouse_name = raw_input("Enter mouse: ")
mouse_name = mouse_name.upper().strip()

# Look up the specific parameters
specific_parameters = ParamLookups.base.get_specific_parameters_from_mouse_name(mouse_name)

# Fudge the user input for the sandbox creations
user_input = {
    'board': specific_parameters['build']['default_board'],
    'box': specific_parameters['build']['default_box'],
    'mouse': mouse_name,
}

#~ # Get session parameters from user (board number, etc)
#~ user_input = get_user_input_from_keyboard()

# Look up the specific parameters
#~ specific_parameters = \
    #~ ParamLookups.get_specific_parameters_from_user_input(user_input)

# Use the sandbox parameters to create the sandbox
sandbox_paths = Sandbox.create_sandbox(user_input, sandbox_root=sandbox_root)

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
