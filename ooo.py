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


class NightosphereBuffer(multiprocessing.Process, SafeRefreshMixin):
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
                unacceptable, data = self.history.popleft()
            else:
                unacceptable = True
            map(lambda q: q.put((unacceptable, data)), self.out_qs)

