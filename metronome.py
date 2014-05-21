import block
import Queue
import time

from ooo import CandyBlock

class MetronomeChild(block.Child):
    def __init__(self, parent, *args,**kwargs):
        self.parent = parent
        block.Child.__init__(self, *args, **kwargs)

    def process(self):
        parent = self.parent
        q = parent.outputs['beat']
        self.running = True
        while self.running:
            t = time.time()
            if not parent.ticking:
                continue
            if t > parent.next_tick:
                # Prevent clock drift but reset if there was a significant difference
                parent.next_tick += parent.delta_t
                # If we've missed 1 (or more) ticks, just reset the clock entirely
                if (t - parent.next_tick) > parent.delta_t:
                    parent.next_tick = parent.delta_t + t
                # Emit tick
                q.put({"beat": "tick", "bpm": 60. / parent.delta_t, "period": parent.delta_t, "next_tick": parent.next_tick})

    def stop(self):
        self.running = False # TODO make this a more thread-safe thing

class MetronomeBlock(CandyBlock):
    STOP = "stop"
    START = "start"
    SET_BPM = "set bpm"
    SET_PERIOD = "set period"
    SYNC = "sync"
    CONTROL_CMDS = {STOP, START, SET_BPM, SET_PERIOD}

    def __init__(self):
        self.INPUTS = [('control', self.handle_control)]
        self.OUTPUTS = ["beat"]

        CandyBlock.__init__(self)

        child = MetronomeChild(self)
        #self.parent = self
        self.add_child(child)

        self.delta_t = 0.5
        self.next_tick = 0

        self.ticking = True

    def handle_control(self, value):
        if value["command"] not in self.CONTROL_CMDS:
            return # ? Command not found XXX

        if value["command"] == self.START:
            self.ticking = True
        elif value["command"] == self.STOP:
            self.ticking = False
        elif value["command"] == self.SET_BPM and "bpm" in value:
            self.delta_t = 60.0 / value["bpm"]
        elif value["command"] == self.SET_PERIOD and "period" in value:
            self.delta_t = value["period"]
        elif value["command"] == self.SYNC:
            self.next_tick = time.time()

class SnapClockBlock(CandyBlock):
    def __init__(self):
        self.INPUTS = [('beat', self.snap), ('channel', None)]
        self.OUTPUTS = ['channel']
        CandyBlock.__init__(self)
    def snap(self, value):
        while True:
            try:
                self.outputs['channel'].put(self.inputs['channel'].get(timeout=0))
            except Queue.Empty:
                break
