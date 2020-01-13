# Write to pipe

import os
import time

MANIPULATOR_PIPE = '/home/chris/dev/ArduFSM/manipulator_pipe'

try:
    pipeout = os.open(MANIPULATOR_PIPE, os.O_WRONLY | os.O_NONBLOCK)
except OSError:
    print "cannot start, likely no one is listening"
    raise

try:
    while True:
        os.write(pipeout, 'goup\n')
        os.write(pipeout, 'goto_interpos\n')
        os.write(pipeout, 'goto_C3up\n')
        os.write(pipeout, 'goto_C3\n')
        time.sleep(5)
        os.write(pipeout, 'goup\n')
        os.write(pipeout, 'goto_i')
        time.sleep(1)
        os.write(pipeout, 'nterpos\n')
        os.write(pipeout, 'goto_C1up\n')
        os.write(pipeout, 'goto_C1\n')
        time.sleep(5)

except KeyboardInterrupt:
    print "received keyboard interrupt, shutting down"

except OSError:
    print "OSError, likely no one is listening, shutting down"

except:
    raise

finally:
    os.close(pipeout)
