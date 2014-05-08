#!/usr/bin/env python
# Peebles -- Async live music generation
# Ooo - 'slow' async blocks


import collections
import multiprocessing
import threading
import time

from doitlive.refreshable import SafeRefreshMixin, SafeRefreshableLoop

class CandyBlock(multiprocessing.Process, SafeRefreshMixin):
    INPUTS = 0
    OUTPUTS = 0

    def __init__(self, inputs, outputs, **params):
        assert len(inputs) == self.INPUTS
        assert len(outputs) == self.OUTPUTS
        self.inputs = inputs
        self.outputs = outputs
        self.params = params
        multiprocessing.Process.__init__(self)
        self.daemon = True

    def run(self):
        raise NotImplementedError


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

class NightosphereBlock(multiprocessing.Process, SafeRefreshMixin):
    # Synchronous block 
    INPUTS = 0
    OUTPUTS = 0

    def __init__(self, clock, inputs, outputs, **params):
        assert len(inputs) == self.INPUTS
        assert len(outputs) == self.OUTPUTS
        self.clock = clock
        self.inputs = inputs
        self.outputs = outputs
        self.params = params
        multiprocessing.Process.__init__(self)
        self.daemon = True
        self.last_cycle_cpu_time = 0

    def run(self):
        while True:
            self.clock.acquire()

            start_cpu_time = time.clock()
            start_wall_time = time.time()

            unacceptables, in_vals = zip(*[q.get() for q in self.inputs]) # Read
            if any(unacceptables):
                results = [(True, None)] * self.OUTPUTS
            else:
                results = self.step(*in_vals)
            for res, q in zip(results, self.outputs):
                q.put(res) # Write

            end_cpu_time = time.clock()
            end_wall_time = time.time()
            self.last_cycle_time = end_cpu_time - start_cpu_time
            self.last_cycle_wall_time = end_wall_time - start_wall_time

    def step(self, *args):
        raise NotImplementedError


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

