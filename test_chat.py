import serial
import time
import datetime
import os
import sys
import errno
import platform
import chat 

chtr = chat.Chatter('COM3')
testMessage = 'test test test\n'
 
f = open(chtr.pipein.name, 'w')
f.write(testMessage)
f.close()
 
new_user_text = chat.read_from_user(chtr.pipein)
chat.write_to_device(chtr.ser, new_user_text)
 
new_device_lines = chat.read_from_device(chtr.ser)
chat.write_to_user(chtr.ofi, new_device_lines)
 
f2 = open(chtr.ofi.name, 'r')
echo = f2.read()
f2.close()
 
print( 'Received echo = ' + echo)
 