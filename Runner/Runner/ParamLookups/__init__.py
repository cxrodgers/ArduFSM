"""Module for looking up specific parameters given session parameters.

Right now these are just hard-coded parameters for boxes, boards, etc.
Later this should be able to access JSON files or a database.

This also contains the function
    get_specific_parameters_from_user_input
which takes the session parameters, gets the specific parameters, and
puts them together by implementing the prioritization rules.

Each parameter dict has the following structure:
    'C': a dict of (key, value) pairs that will become #define macros
        `value` should be a string, or None
        None means do not define
    'Python': a dict that will be written as a JSON parameters file
        for Python.
    'build': a dict of sandbox parameters, like the protocol name,
        that is used in the creation of the sandbox.
    
This could potentially be a list of parameters, each with fields
'human-readable-name', 'code-name', 'value'
"""
import base
import Hardcoded
try:
    import Database
except ImportError:
    print "warning: cannot import Database"
