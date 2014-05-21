import block
from ooo import CandyBlock
import inspect

# The nth grid sequencer zbanks has written

class GridSeqBlock(CandyBlock):
    SET_PERIOD = "set period"
    SYNC = "sync"

    CONTROL_CMDS = {SET_PERIOD, SYNC}

    def __init__(self):
        self.INPUTS=[('beat', self.on_beat), ('control', self.handle_control)]
        self.OUTPUTS=['notes']

        CandyBlock.__init__(self)

        self.grid = {}
        self.channels = {}

        self.t = 0
        self.period = 8

    def on_beat(self, value):
        if self.t >= self.period:
            self.t = 0

        for ch, note in self.channels.items():
            d = self.grid[ch][self.t]
            if d is not None:
                self.outputs["notes"].put(note(d))
        
        self.t += 1
        if self.t >= self.period:
            self.t = 0

    def handle_control(self, value):
        if value["command"] not in self.CONTROL_CMDS:
            return # ? Command not found XXX

        if value["command"] == self.SYNC:
            self.sync()
        elif value["command"] == self.SET_PERIOD and "period" in value:
            self.set_period(value["period"])

    def set_period(self, p):
        self.period = p
        self.t = self.t % p
        for g in self.grid:
            while len(self.grid[g]) < p:
                self.grid.append(None)

    def sync(self):
        self.t = 0

    def new_channel(self, name, note):
        if inspect.isfunction(note):
            note_fn = note
        else:
            note_fn = lambda x: note
        self.channels[name] = note_fn
        self.grid[name] = [None] * self.period

def unison_seq():
    song = [65, 75, None, 72, 67, 67, 68, None, 65, 70, 72, 70, 65, 65, None, None, 65, 75, None, 72, 67, 67, 68, 65, 72, 75, None, 72, 77]
    gs = GridSeqBlock()
    gs.set_period(len(song) + 4)
    for i in range(65,78):
        gs.new_channel(i, {'event_type':'note_on','note': i,'velocity': 0.8})
    for t, s in enumerate(song):
        if s is not None:
            gs.grid[s][t] = True
    return gs
