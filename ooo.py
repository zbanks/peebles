#!/usr/bin/env python
# Author: Zach Banks <zbanks@mit.edu>
# License: MIT License
# Peebles -- Async live music generation


import collections
import multiprocessing
import time
import signal
import sys
import traceback
import block
import threading

from doitlive.refreshable import SafeRefreshMixin, SafeRefreshableLoop

class CandyBlock(block.Block,multiprocessing.Process, SafeRefreshMixin):
    INPUTS = []
    OUTPUTS = []

    def __init__(self):
        block.Block.__init__(self)
        self.inputs={}
        for (in_name,callback) in self.INPUTS:
            q=block.InterruptableQueue(multiprocessing.Queue)
            self.add_child(block.Listener(q,callback))
            self.inputs[in_name]=q

        self.outputs = dict([(out_name,block.InterruptableQueue(multiprocessing.Queue)) for out_name in self.OUTPUTS])

        self.ipc_queue=block.InterruptableQueue(multiprocessing.Queue)
        self.add_child(block.Listener(self.ipc_queue,self.recv_ipc))

        self.error_queue=block.InterruptableQueue(multiprocessing.Queue)

        multiprocessing.Process.__init__(self)
        self.daemon = True
        self.exit=multiprocessing.Event()

    def send(self,out_name,out_data):
        self.outputs[out_name].put(out_data)

    def run(self):
        signal.signal(signal.SIGINT,signal.SIG_IGN) # disregard ctrl-c
        try:
            block.Block.run(self)
        except Exception:
            #raise # debugging
            self.error_queue.put(traceback.format_exc())

    def recv_ipc(self,message):
        self.stop() # for now, stop on all messages

    def shutdown(self):
        self.ipc_queue.put(None)

class Peebles(SafeRefreshMixin):
    def __init__(self):
        self.reset()

    def reset(self):
        self.blocks={}
        self.all_blocks=set()
        self.supervisors={}
        self.all_supervisors=set()
        self.connections={}
        self.all_connections=set()

    def add_block(self,name,b):
        self.all_blocks.add(b)
        self.blocks[name]=b
        s=block.Listener(b.error_queue,lambda err:self.handle_error(name,err))
        self.all_supervisors.add(s)
        self.supervisors[name]=s
        s.start()
        b.start()

    def handle_error(self,block_name,err):
        print err
        # in the future, maybe do something about this
        # note: this is called from a thread off of the main program

    def destroy(self):
        for (name,b) in self.blocks.iteritems():
            #print "Shut down",name
            b.shutdown()
        for (name,connection) in self.connections.iteritems():
            #print "Unconnect",name
            connection.stop()
        for (name,supervisor) in self.supervisors.iteritems():
            #print "Stop supervising",name
            supervisor.stop()
        for b in self.all_blocks:
            #print "Join block process..."
            b.join()
        for connection in self.all_connections:
            #print "Join connection thread..."
            connection.join()
        for supervisor in self.all_supervisors:
            #print "Join supervisor thread..."
            supervisor.join()
        self.reset()

    def remove_block(self,name):
        self.blocks[name].shutdown()
        del self.blocks[name]

    def add_connection(self,name,(from_name,from_output),to_names):
        from_block=self.blocks[from_name]
        to_blocks=[(self.blocks[to_name],to_input) for (to_name,to_input) in to_names]

        bg=BananaGuard((from_block,from_output),to_blocks)
        self.all_connections.add(bg)
        self.connections[name]=bg
        bg.start()

    def remove_connection(self,name):
        self.connections[name].stop()
        del self.connections[name]

class BananaGuard(block.Listener):
    def __init__(self,(from_block,output_name),to_blocks):
        from_q=from_block.outputs[output_name]
        self.to_qs=[to_block.inputs[input_name] for (to_block,input_name) in to_blocks]
        block.Listener.__init__(self,from_q,self.recv)

    def recv(self,data):
        for q in self.to_qs:
            q.put(data)

#class BananaGuard(threading.Thread):
#    # Thread to constantly shovel data from inp_q to out_q
#    STOP_SIGNAL = Exception()
#
#    def __init__(self, inp_q, out_qs):
#        self.inp_q = inp_q
#        self.out_qs = out_qs
#        threading.Thread.__init__(self)
#        self.daemon = True
#    def run(self):
#        while True:
#            data = self.wee()
#            if data == STOP_SIGNAL:
#                break
#            self.woo(data)
#    def wee(self):
#        return self.inp_q.get()
#    def woo(self, data):
#        map(lambda q: q.put(data), self.out_qs)

class SoulBlock(CandyBlock):
    def __init__(self, chunksize, rate):
        self.chunksize = chunksize
        self.rate = rate
        self.clock_lock=block.InterruptableQueue(multiprocessing.Queue)
        self.add_child(block.Listener(self.clock_lock,self.step))
        CandyBlock.__init__(self)

    def clock(self):
        self.clock_lock.put(None)

    def step(self,value=None):
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


