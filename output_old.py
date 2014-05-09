#!/usr/bin/env python
#!/usr/bin/env python
# Author: Zach Banks <zbanks@mit.edu>
# License: MIT License
# Peebles -- Async live music generation
# output - blocks for outputting sound & other things in the nightosphere (sync)

import pyaudio
import struct
import math

from ooo import *

class PyaudioOutputNightBlock(SoulBlock):
    # Sync block, output over pyaudio
    INPUTS = ["sound"]
    OUTPUTS = []
    NUM_FRAMES = 1

    def init_sync(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paFloat32,
                              channels=1, rate=self.rate,
                              frames_per_buffer=self.chunksize,
                              output=True)
        self.process2([0.0] * (2 ** 10))

    def step(self):
        unacceptables, in_vals = zip(*[q.get() for q in self.inputs.values()]) # Read
        if any(unacceptables):
            results = [(True, None)] * len(self.outputs)
        else:
            results = self.process2(*in_vals)
        #for res, q in zip(results, self.outputs):
            #q.put(res) # Write

    def process2(self, chunk):
        encoded_chunk = struct.pack(str(len(chunk)) + 'f', *chunk)
        self.stream.write(encoded_chunk)
        return []

    def destroy_sync(self): # Never called yet
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        SoulBlock.stop(self)

import multiprocessing
#po = PyaudioOutputNightBlock(1024, 22100)
#inp = po.inputs["sound"]
#clk = po.clock_lock
#def qi(): inp.put((False, [math.sin(x / 24.0) for x in range(2 ** 10)]))
#
#import time
##po.process2([math.sin(x / 24.0) for x in range(2 ** 10)])
#qi()
#qi()
#po.start()
#po.step()
#while True:
#    qi()
#    po.clock()
#    po.handle_errors()
#    #po.process2([math.sin(x / 24.0) for x in range(2 ** 10)])
#    #po.step()
#
#    time.sleep(0.1)

if __name__=='__main__':
    from multiprocessing import Queue
    import time
    po = PyaudioOutputNightBlock(1024, 22100)
    inp=po.inputs['sound']
    def qi(): inp.put((False, [math.sin(x * math.pi / 16.0) for x in range(2 ** 10)]))
    qi()
    po.start()
    try:
        while True:
            qi()
            po.clock()
            po.handle_errors()
            time.sleep(0.02)
    except KeyboardInterrupt:
        print "caught ctrl-c"
        po.stop()
        po.join()
