import chat 

portNum = 3
serialPort = 'COM' + str(portNum)
testMessage = 'test test test'

#Create chatter object
chtr = chat.Chatter(serialPort)
 
#Write the test message to the Chatter object's pipein
f = open(chtr.pipein.name, 'w')
f.write(testMessage + '\n')
f.close()
 
#The next 4 lines replicate the Chatter.update() function 
new_user_text = chat.read_from_user(chtr.pipein)
chat.write_to_device(chtr.ser, new_user_text)
 
new_device_lines = chat.read_from_device(chtr.ser)
chat.write_to_user(chtr.ofi, new_device_lines)
 
#Read the message read back from the Arduino
f2 = open(chtr.ofi.name, 'r')
echo = f2.read()
f2.close() 
print( 'Received echo = ' + echo)
 