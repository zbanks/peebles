from ooo import Peebles
from midi_in import MidiInBlock
from debug import PrintBlock, MidiControlBlock
from output import OutputBlock
from synth import SynthBlock
from looper import LooperBlock
from metronome import MetronomeBlock
from seq import GridSeqBlock, unison_seq
import time

USE_LOOPER = False

pb=Peebles()

pb.add_block('piano',MidiInBlock())
pb.add_block('screen',PrintBlock())
a=256
r=48000
buf=3
pb.add_block('sound',OutputBlock(a,r,buf))
pb.add_block('synth',SynthBlock(a,r))
pb.add_block('mcontrol', MidiControlBlock())
pb.add_block('metronome', MetronomeBlock())
pb.add_block('seq', unison_seq())

if USE_LOOPER:
    pb.add_block('looper', LooperBlock())

pb.add_connection('link1',('sound','clock'),[('synth','clock')])
pb.add_connection('link2',('synth','sound'),[('sound','sound')])
pb.add_connection('link3',('piano','notes'),[('mcontrol','notes'),('screen','print')])
if USE_LOOPER:
    pb.add_connection('link4',('mcontrol','notes'),[('looper','notes')])
    pb.add_connection('link5',('mcontrol','control'),[('looper','control')])
    pb.add_connection('link6',('looper','notes'),[('synth','notes')])
else:
    pb.add_connection('link7',('mcontrol','notes'),[('synth','notes')])
pb.add_connection('link8',('metronome','beat'),[('seq', 'beat')])
pb.add_connection('link9',('seq', 'notes'),[('synth', 'notes')])

try:
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	pb.destroy()
