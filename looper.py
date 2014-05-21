import block
import time

from ooo import CandyBlock

class LooperChild(block.Child):
    def __init__(self, parent, *args,**kwargs):
        self.parent = parent
        block.Child.__init__(self, *args, **kwargs)

    def process(self):
        parent = self.parent
        q= parent.outputs['notes']
        self.running=True
        playback_time = None
        while self.running:
            if parent.playback == 0 or parent.recording or not parent.events:
                playback_time = None
                continue
            if playback_time is None:
                playback_time = time.time()
            if parent.ev_id >= len(parent.events):
                parent.ev_id = 0
                #parent.playback = 0
                # This happens if recording and playback overlap
            t, note = parent.events[parent.ev_id]
            if note == LooperBlock.STOP_LOOP:
                parent.ev_id = 0
                playback_time += t
            elif t < (time.time() - playback_time):
                #print "Playing note", t, (time.time() - playback_time)
                q.put(note)
                parent.ev_id += 1

    def stop(self):
        self.running = False # TODO make this a more thread-safe thing

class LooperBlock(CandyBlock):
    LOOP_FOREVER = "loop forever"
    LOOP_COUNT = "loop count"
    LOOP_STOP = "loop stop"
    RECORD_START = "record start"
    RECORD_STOP = "record stop"
    CONTROL_CMDS = {LOOP_FOREVER, LOOP_COUNT, LOOP_STOP, RECORD_START, RECORD_STOP}

    STOP_LOOP = "stahp"

    def __init__(self):
        self.INPUTS=[('notes', self.recieve_note), ('control', self.handle_control)]
        self.OUTPUTS=['notes']

        CandyBlock.__init__(self)

        child = LooperChild(self)
        #self.parent = self
        self.add_child(child)

        self.events = []
        self.ev_id = 0
        self.playback = 0
        self.passthru = True
        self.recording = None

    def recieve_note(self, value):
        if self.passthru:
            self.outputs["notes"].put(value)
        if self.recording is not None:
            self.events.append((time.time() - self.recording, value))

    def handle_control(self, value):
        if value["command"] not in self.CONTROL_CMDS:
            return # ? Command not found XXX
        if value["command"] == self.RECORD_START:
            self.events = []
            self.recording = time.time()
        elif value["command"] == self.RECORD_STOP and self.recording is not None:
            self.events.append((time.time() - self.recording, self.STOP_LOOP))
            self.recording = None
        elif value["command"] == self.LOOP_FOREVER:
            self.playback = -1
        elif value["command"] == self.LOOP_COUNT and "count" in value:
            self.playback = value["count"]
        elif value["command"] == self.LOOP_STOP:
            self.playback = 0
