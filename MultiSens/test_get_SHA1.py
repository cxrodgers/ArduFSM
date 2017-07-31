import os
import subprocess
import json

# cd to sketch directory
baseDir = 'C:\\Users\\Dank\\Documents\\Arduino\\ArduFSM\\MultiSens'
os.chdir(baseDir);

# find all source code files in sketch directory
sources = [x for x in os.listdir(os.getcwd()) if '.cpp' in x or '.h' in x] 

# create a dictionary for each source code file
dat = []
baseCmd = 'git log -n 1 --pretty=format:%H -- '
for s in sources:
	
	# get path:
	fullPath = baseDir + '\\' + s
	
	# get SHA1 hash:
	cmd = baseCmd + fullPath
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(sha1, err) = proc.communicate()
	
	# put path andSHA1 into dict
	d = {"fullPath": fullPath, "SHA1": sha1}
	dat.append(d)

# proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, shell=True)

# Place list of dicts into dict object, then write to JSON file
out = {'sources': dat}
with open('testJSON.json', 'w') as fp:
	json.dump(out, fp)