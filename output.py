#!/usr/bin/env python
#!/usr/bin/env python
# Author: Zach Banks <zbanks@mit.edu>
# License: MIT License
# Peebles -- Async live music generation
# output - blocks for outputting sound & other things in the nightosphere (sync)

import pyaudio
import struct
import Queue
import threading
import time

import block
from ooo import CandyBlock

class OutputChild(block.Child):
    def process(self):
        pa = pyaudio.PyAudio()

        self.running=True
        zeros=[0]*self.parent.chunksize
        chunk=zeros
        got=False
        lt=0

        stream = pa.open(format=pyaudio.paFloat32,
                         channels=2, rate=self.parent.rate,
                         frames_per_buffer=self.parent.chunksize,
                         output=True)

        while self.running:
            t=time.time()
            l=self.parent.get_samples()
            interleaved=[val for pair in zip(l, l) for val in pair]
            encoded_chunk = struct.pack(str(len(interleaved)) + 'f', *interleaved)
            stream.write(encoded_chunk)
            #print time.time()-t

        stream.stop_stream()
        stream.close()
        pa.terminate()

    def stop(self):
        self.running=False # TODO make this a more thread-safe thing

class ClockChild(block.Child):
    def process(self):
        self.running=True
        while self.running:
            need=self.parent.samples_size-self.parent.samples.qsize()
            #print "need",need
            for i in range(need):
                self.parent.send('clock',None)
            for i in range(need):
                self.parent.qsem.acquire() # TODO make this interruptable
            time.sleep(0)

    def stop(self):
        self.running=False

class OutputBlock(CandyBlock):
    def __init__(self,chunksize,rate,buf_size):
        self.INPUTS=[('sound',self.got_samples)]
        self.OUTPUTS=['clock']

        CandyBlock.__init__(self)

        self.chunksize=chunksize
        self.rate=rate
        self.samp_lock=threading.Lock()
        self.full=False
        self.zeros=[0]*self.chunksize
        self.lt=0
        self.samples=Queue.Queue()
        self.samples_size=buf_size
        self.qsem=threading.Semaphore(0)

        oc=OutputChild()
        oc.parent=self
        self.add_child(oc)

        cc=ClockChild()
        cc.parent=self
        self.add_child(cc)

    def get_samples(self):
        if self.samples.empty():
            print "underrun"
            return self.zeros
        #print self.samples.qsize()
        return self.samples.get()

    def got_samples(self,samples):
        self.samples.put(samples)
        self.qsem.release()
