from ooo import Peebles
from midi_in import MidiInBlock
from debug import PrintBlock
from output import OutputBlock
from synth import SynthBlock
import time

pb=Peebles()

pb.add_block('piano',MidiInBlock())
pb.add_block('screen',PrintBlock())
a=10
pb.add_block('sound',OutputBlock(2**a,48000))
pb.add_block('synth',SynthBlock(2**a,48000))

pb.add_connection('link1',('sound','clock'),[('synth','clock')])
pb.add_connection('link2',('synth','sound'),[('sound','sound')])
pb.add_connection('link3',('piano','notes'),[('synth','notes')])

try:
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	pb.destroy()
