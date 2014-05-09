from ooo import Peebles
from midi_in import MidiInBlock
from debug import PrintBlock
import time

pb=Peebles()

pb.add_block('piano',MidiInBlock())
pb.add_block('screen',PrintBlock())
pb.add_connection('link',('piano','notes'),[('screen','print')])

try:
	while True:
		time.sleep(1)
except KeyboardInterrupt:
	pb.destroy()
