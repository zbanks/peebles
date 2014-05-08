#!/usr/bin/env python
# Author: Zach Banks <zbanks@mit.edu>
# License: MIT License
# Peebles -- Async live music generation


import collections
import multiprocessing
import threading
import time
import signal
import sys
import traceback

from doitlive.refreshable import SafeRefreshMixin, SafeRefreshableLoop

class CandyBlockException(Exception):
    def __init__(self, block, traceback):
        self.block = block
        self.traceback = traceback
        Exception.__init__(self,"Exception in {0}:\n{1}".format(block,traceback))

class CandyBlock(multiprocessing.Process, SafeRefreshMixin):
    INPUTS = []
    OUTPUTS = []

    def __init__(self, *args, **kwargs):
        self.inputs = dict([(in_name,multiprocessing.Queue()) for in_name in self.INPUTS])
        self.outputs = dict([(out_name,multiprocessing.Queue()) for out_name in self.OUTPUTS])
        self.errors = multiprocessing.Queue()
        multiprocessing.Process.__init__(self)
        self.daemon = True
        self.exit=multiprocessing.Event()
        self.init(*args,**kwargs)

    def keep_running(self):
        return not self.exit.is_set()

    def spin(self):
        self.exit.wait()

    def run(self):
        #signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            self.process()
        except:
            traceback.print_exc()
            self.errors.put(traceback.format_exc())

    def handle_errors(self):
        if not self.errors.empty():
            raise CandyBlockException(self,self.errors.get())

    def process(self):
        self.spin()

    def init(self):
        pass

    def stop(self):
        self.exit.set()

class Peebles(SafeRefreshMixin):
    def __init__(self):
        pass

class BananaGuard(threading.Thread):
    # Thread to constantly shovel data from inp_q to out_q
    STOP_SIGNAL = Exception()

    def __init__(self, inp_q, out_qs):
        self.inp_q = inp_q
        self.out_qs = out_qs
        threading.Thread.__init__(self)
        self.daemon = True
    def run(self):
        while True:
            data = self.wee()
            if data == STOP_SIGNAL:
                break
            self.woo(data)
    def wee(self):
        return self.inp_q.get()
    def woo(self, data):
        map(lambda q: q.put(data), self.out_qs)

class SoulBlock(CandyBlock):
    def __init__(self, chunksize, rate, *args, **kwargs):
        self.chunksize = chunksize
        self.rate = rate
        self.clock_lock = multiprocessing.Semaphore(0)
        CandyBlock.__init__(self, *args,**kwargs)

    def clock(self):
        self.clock_lock.release()

    def run(self):
        self.sync_thread=threading.Thread(target=self.run2)
        self.sync_thread.daemon=True
        self.sync_thread.start()
        CandyBlock.run(self)

    def stop(self):
        CandyBlock.stop(self)
        self.clock_lock.release()

    def run2(self):
        while True:
            print "waiting for clk"
            self.clock_lock.acquire()
            if not self.keep_running():
                break
            print "clk acquired"

            start_cpu_time = time.clock()
            start_wall_time = time.time()

            print "stepping"
            try:
                self.step()
            except:
                self.errors.put(traceback.format_exc())
                self.stop()
                break
            print "stepped"

            end_cpu_time = time.clock()
            end_wall_time = time.time()
            self.last_cycle_cpu_time = end_cpu_time - start_cpu_time
            self.last_cycle_wall_time = end_wall_time - start_wall_time
    
    def step(self):
       pass


#class SoulBlock(multiprocessing.Process, SafeRefreshMixin):
#    # Synchronous block 
#    INPUTS = []
#    OUTPUTS = []
#
#    def __init__(self, chunksize, *args, **kwargs):
#        self.clock_lock = multiprocessing.Semaphore(0)
#        self.inputs = dict([(in_name,multiprocessing.Queue()) for in_name in self.INPUTS])
#        self.outputs = dict([(out_name,multiprocessing.Queue()) for out_name in self.OUTPUTS])
#        multiprocessing.Process.__init__(self)
#        self.daemon = True
#        self.last_cycle_cpu_time = 0
#        self.last_cycle_wall_time = 0
#        self.init(*args,**kwargs)
#
#    def init(self):
#        pass
#
#    def clock(self):
#        self.clock_lock.release()
#
#    def run(self):
#        while True:
#            print "waiting for clk"
#            self.clock_lock.acquire()
#            print "clk acquired"
#
#            start_cpu_time = time.clock()
#            start_wall_time = time.time()
#
#            print "stepping"
#            self.step()
#            print "stepped"
#
#            end_cpu_time = time.clock()
#            end_wall_time = time.time()
#            self.last_cycle_cpu_time = end_cpu_time - start_cpu_time
#            self.last_cycle_wall_time = end_wall_time - start_wall_time
#    
#    def step(self):
#        #unacceptables, in_vals = zip(*[q.get() for q in self.inputs]) # Read
#        #if any(unacceptables):
#        #    results = [(True, None)] * self.OUTPUTS
#        #else:
#        #    results = self.process(*in_vals)
#        #for res, q in zip(results, self.outputs):
#        #    q.put(res) # Write
#        pass


class NightosphereBuffer(multiprocessing.Process, SafeRefreshMixin):
    # Buffer & Connection between two synchronous blocks 
    STOP_SIGNAL = Exception()

    def __init__(self, clock, inp_q, out_qs, depth=0):
        self.clock = clock
        self.inp_q = inp_q
        self.out_qs = out_qs
        self.depth = depth
        self.history = collections.deque()
        multiprocessing.Process.__init__(self)
        self.daemon = True

    def run(self):
        while True:
            self.clock.acquire() # release by master clock
            unacceptable, data = self.inp_q.get()
            if data == STOP_SIGNAL:
                break
            self.history.append((unacceptable, data))
            if len(self.history) > self.depth:
                # This currently has horrible behavior if self.depth decreases XXX
                unacceptable, data = self.history.popleft()
            else:
                unacceptable = True
            map(lambda q: q.put((unacceptable, data)), self.out_qs)

