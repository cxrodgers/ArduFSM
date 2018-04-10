"""Module for creating the sandbox directories for Arduino and Python.


"""
import os
import subprocess
import shutil
import json
import ParamLookups
import datetime 
import time
import platform
import shlex

def create_sandbox(user_input, sandbox_root):
    """Create a sandbox directory for Autosketch and Script
    
    user_input : dict containing the following keys
        'mouse', 'board', 'box', 'experimenter'
    
    sandbox_root : rooth path of sandboxes
    
    The sandbox directory will be in EYM format:
        sandbox_root/experimenter/year/month
    
    Returns: dict with following keys
        'sandbox': Path to sandbox directory
        'sketch': Path to directory that will contain sketch
        'script': Path to directory that will contain script
    
    All of these directories are created if they don't already exist.
    Also, a logfiles directory is created in the script directory.
    
    Note: 'script' and 'sketch' are subdirectories of 'sandbox'
    """
    now = datetime.datetime.now()
    
    # Construct sandbox name
    date_string = now.strftime('%Y-%m-%d-%H-%M-%S')
    sandbox_name = '%s-%s-%s-%s' % (date_string,
        user_input['mouse'], user_input['board'], user_input['box'])
    
    # Construct path in EYM format
    experimenter_path = os.path.join(sandbox_root, user_input['experimenter'])
    year_path = os.path.join(experimenter_path, str(now.year))
    month_path = os.path.join(year_path, '%02d' % now.month)
    sandbox_path = os.path.join(month_path, sandbox_name)
    
    # Path to other things
    sketch_path = os.path.join(sandbox_path, 'Autosketch')
    script_path = os.path.join(sandbox_path, 'Script')
    logfile_path = os.path.join(script_path, 'logfiles')

    # Status
    print "create sandbox in ", sandbox_path

    # Create directories if necessary
    for dirname in [experimenter_path, year_path, month_path, sandbox_path, 
        sketch_path, script_path, logfile_path]:
        if not os.path.exists(dirname):
            os.mkdir(dirname)
    
    return {
        'sandbox': sandbox_path,
        'sketch': sketch_path,
        'script': script_path,
    }

def copy_protocol_to_sandbox(sandbox_paths,
    build_parameters, protocol_root):
    """Copy files in protocol_path to sketch_path
    
    First we find the protocol directory by joining protocol_root and
    `build_parameters['protocol_name']`.
    
    Then we go through every file in the protocol directory.
    *   If it is in `build_parameters['skip_files']` we skip it.
    *   If it is the name of the protocol + '.ino' then copy it to the
        sketch_path and call it Autosketch.ino
    *   If it ends in '.py' then we copy it to the script_path
    *   Everything else is copied to sketch_path.
    """
    # Find the protocol_path
    protocol_path = os.path.join(protocol_root,
        build_parameters['protocol_name'])

    # Copy all files in protocol_path to sketch_path
    for filename in os.listdir(protocol_path):
        if ('skip_files' in build_parameters and 
            filename in build_parameters['skip_files']):
            # A file to skip
            continue
            
        elif filename == build_parameters['protocol_name'] + '.ino':
            # This is the actual protocol *.ino
            # Rename it Autosketch.ino
            shutil.copyfile(
                os.path.join(protocol_path, filename),
                os.path.join(sandbox_paths['sketch'], 'Autosketch.ino'))
                
        elif filename.endswith('.py'):
            # Python files go to script_path
            shutil.copyfile(
                os.path.join(protocol_path, filename),
                os.path.join(sandbox_paths['script'], filename))
                
        else:
            # All other files go to sketch_path
            shutil.copyfile(
                os.path.join(protocol_path, filename),
                os.path.join(sandbox_paths['sketch'], filename))

def write_c_config_file(sketch_path, c_parameters, verbose=False):
    """Write the C config file to sketch_path
    
    This file will consist of some boilerplate include guards, and
    a #define macro for each parameter in c_parameters. The parameter
    names are mangled using ParamLookups.translate_c_parameter_name.
    If that function returns None, the parameter is skipped. Also, if
    the parameter value is None, the parameter is skipped (#ifndef).
    """
    # config file boilerplate
    config_file_boilerplate_header = '\n'.join([
        '// Auto-generated config.h',
        '#ifndef __AUTOSKETCH_CONFIG_H',
        '#define __AUTOSKETCH_CONFIG_H',
        '',
        '',
    ])
    config_file_boilerplate_footer = '\n'.join([
        '',
        '#endif      // #ifndef __AUTOSKETCH_CONFIG_H',
        ''
    ])

    # Generate file contents
    config_filename = os.path.join(sketch_path, 'config.h')
    config_file_contents = ''
    for param_name, param_value in c_parameters.items():
        # Skip those with None (useful for ifndef)
        if param_value is None:
            continue
        
        # C-mangle the name
        mangled_name = ParamLookups.base.translate_c_parameter_name(param_name)
        if mangled_name is None:
            print "warning: can't mangle parameter %s, skipping" % param_name
            continue
        
        # Check that it's really a string, if not, could be weird errors
        if type(param_value) is not str and type(param_value) is not unicode:
            raise TypeError("C param values must be strings, not type %r" 
                % type(param_value))
        
        # Write to string to write to file
        config_file_contents += "#define %s %s\n" % (mangled_name, param_value)
    
    # Write to the file
    if verbose:
        print "C code written to %s:" % config_filename
        print config_file_contents
    with file(config_filename, 'w') as fi:
        fi.write(config_file_boilerplate_header)
        fi.write(config_file_contents)
        fi.write(config_file_boilerplate_footer)

def compile_and_upload(sandbox_paths, specific_parameters, verbose=False):
    """Compile and upload the code in the sandbox to the arduino"""
    # Name of the Arduino sketch
    sketch_filename = os.path.join(sandbox_paths['sketch'],
        'Autosketch.ino')

    # Check the serial port and sketch exist
    if not os.path.exists(specific_parameters['build']['serial_port']):
        raise OSError("serial port %s does not exist" % 
            specific_parameters['build']['serial_port'])
    if not os.path.exists(sketch_filename):
        raise OSError("sketch filename %s does not exist" %
            sketch_filename)

    # Form a command string for compilation
    cmd_string = [
        'arduino',
        '--board',
        'arduino:avr:uno',
        '--port',
        specific_parameters['build']['serial_port'],
        '--pref',
        'sketchbook.path=%s' % os.path.expanduser('~/dev/ArduFSM'),
        '--upload',
        sketch_filename,
    ]
    
    # Run the compilation and collect output
    # http://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
    # Non-blocking read magic
    import sys
    from threading import Thread
    from Queue import Queue, Empty
    def enqueue_output(out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()
    
    # Create the subprocess
    n_repeats = 0
    stop_looping = False
    while (not stop_looping and n_repeats < 2):
        n_repeats = n_repeats + 1
        if verbose:
            print "compiling and uploading: " + ' '.join(cmd_string)
        compile_proc = subprocess.Popen(cmd_string, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1)

        # Non-blocking read magic
        q = Queue()
        t = Thread(target=enqueue_output, args=(compile_proc.stderr, q))
        t.daemon = True
        t.start()
        
        # Wait till compilation is finished
        stderr_temp = ''
        killed = False
        while compile_proc.poll() is None:
            time.sleep(2)
            print "working..."
            
            # Check for any new results on STDERR
            try:
                while True:
                    line = q.get_nowait()
                    stderr_temp += line
            except Empty:
                # no output
                pass
            
            # Kill if necessary
            if 'avrdude: stk500_recv(): programmer is not responding' in stderr_temp:
                #~ print "not responding, hit CTRL+C to end this"
                #~ compile_proc.terminate()
                killed = True
                #~ compile_proc.poll()
                break
        
        # compile process either completed or was killed
        if killed:
            raise IOError("avrdude process killed; unplug and replug")
        else:
            # Check if upload failed
            if 'avrdude: ser_open(): can' in stderr_temp:
                if n_repeats < 2:
                    print "upload failed; trying again ..."
                    time.sleep(3)
                else:
                    raise IOError("repeated ser_open errors, giving up")
            else:
                stop_looping = True
            
            stdout = compile_proc.stdout.read()
            if verbose:
                print "COMPILATION STDOUT:"
                print stdout
                print "COMPILATION STDERR:"
                print stderr_temp
        
            # Check for compilation errors
            if compile_proc.returncode != 0:
                print "error in compiling:"
                print stderr_temp
                raise IOError("compilation error")
            else:
                print "successfully compiled and uploaded"
    
def write_python_parameters(sandbox_paths, python_parameters, script_name,
    verbose=False):
    """Write python_parameters to script directory in sandbox"""
    json_file = os.path.join(sandbox_paths['script'], 'parameters.json')
    if verbose:
        print "dumping python parameters to %s" % json_file
        print json.dumps(python_parameters, indent=4)
    with file(json_file, 'w') as fi:
        json.dump(python_parameters, fi, indent=4)
  
def call_python_script(script_path, script_name, ncols=80, nrows=23, 
    xpos=0, ypos=270, zoom=.6):
    """Run the Python script in a subprocess.
    
    A new gnome-terminal window is created at the specified position.
    ipython is called using script_name as input.
    
    script_path : Location of the script
    script_name : Name of the script
    ncols, nrows : size of gnome-terminal window
    zoom : zoom of gnome-terminal window
    """
    # Launch a new terminal window in a certain position
    # Within that window, execute ipython
    # Tell ipython to run the script

    if (platform.system().lower() == "darwin"):
        cmd = "xterm -geometry {}x{}+{}+{} -e 'cd {} && ipython --pylab=tk -i {}' ".format(
            ncols,
            nrows,
            xpos,
            ypos,
            os.path.abspath(script_path),
            script_name
        )
        subprocess.Popen(shlex.split(cmd))
    else:
        subprocess.Popen([
            'gnome-terminal', 
            '--working-directory=%s' % os.path.abspath(script_path),
            '--geometry=%dx%d+%d+%d' % (ncols, nrows, xpos, ypos),
            '--zoom=%0.2f' % zoom,  
            '-x',
            'bash', '-l', '-c',
            "ipython --pylab=qt -i %s" % script_name,
            ])
