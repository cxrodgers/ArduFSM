"""Module for starting a behavioral session in a sandbox.

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

import ParamLookups
import Sandbox