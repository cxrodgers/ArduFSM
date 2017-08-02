import os
import subprocess
import json

# cd to sketch directory
baseDir = 'C:\\Users\\Dank\\Documents\\Arduino\\ArduFSM\\MultiSens'
os.chdir(baseDir);

# find all source code files in sketch directory
sources = [x for x in os.listdir(os.getcwd()) if '.cpp' in x or '.h' in x or '.ino' in x or '.py' in x] 

# create a dictionary for each source code file in the sketch directory:
srcList = []
baseCmd = 'git log -n 1 --pretty=format:%H -- '
for s in sources:
	
	# get path:
	fullPath = baseDir + '\\' + s
	
	# get SHA1 hash:
	fullCmd = baseCmd + ' -- ' + fullPath
	proc = subprocess.Popen(fullCmd, stdout=subprocess.PIPE, shell=True)
	sha1, err = proc.communicate()
	
	# put path and SHA1 into dict
	d = {"path": fullPath, "SHA1": sha1}
	srcList.append(d)

# proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, shell=True)

# find all libraries used by the uploaded sketch:
arduinoPath = 'C:\\Program Files (x86)\\Arduino'
libBaseStr = 'Using library'
inos = [y for y in os.listdir(os.getcwd()) if '.ino' in y]
os.chdir(arduinoPath)
verifyCmd = 'arduino_debug -v --verify ' + baseDir + '\\' + inos[0]
out, err = subprocess.Popen(verifyCmd, stdout=subprocess.PIPE, shell=True).communicate()
out = out.splitlines()
libLines = [z for z in out if libBaseStr in z]
print(libLines)

# create a dict for each library used by the main sketch:
libList = []
for lib in libLines:
	
	# get the path of the library:
	ind = lib.find(':')
	libPath = lib[ind+2:]
	print(libPath)
	
	# if the line ends in '(legacy)' because it's been previously compiled, exclude '(legacy)' to isolate the path to the library
	if libPath[-len(' (legacy)'):]  == ' (legacy)':
		libPath = libPath[:-len(' (legacy)')]
	print(libPath)
	
	# get the SHA1 hash of the library:
	os.chdir(libPath)
	
	try:
		sha1 = subprocess.check_output(['git', 'log', '-n 1', '--pretty=format:%H'], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
		print('output:')
		print(e.output)
		sha1 = e.output

	# put path and SHA1 hash into dict:
	e = {"path": libPath, "SHA1": sha1}
	libList.append(e)

# Place list of dicts into dict object, then write to JSON file
out = {'srcFiles': srcList, 'libraries': libList}
os.chdir(baseDir)
with open('testJSON.json', 'w') as fp:
	json.dump(out, fp)