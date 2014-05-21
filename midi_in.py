import block
from ooo import CandyBlock
import pygame
import pygame.midi

class MidiInChild(block.Child):
	def process(self):
		pygame.init()
		pygame.midi.init()
		print "# of MIDI devices:",pygame.midi.get_count()
		device_id=3
		midi_in=pygame.midi.Input(device_id)
		q=self.parent.outputs['notes']
		self.running=True
		while self.running:
			for e in midi_in.read(1024):
				e=e[0]

				if e[0]==144:
					q.put({'event_type':'note_on','note':e[1],'velocity':e[2]/256.})
				elif e[0]==128:
					q.put({'event_type':'note_off','note':e[1]})
			# yield?

	def stop(self):
		self.running=False # TODO make this a more thread-safe thing

class MidiInBlock(CandyBlock):
	def __init__(self):
		self.INPUTS=[]
		self.OUTPUTS=['notes']

		CandyBlock.__init__(self)

		mic=MidiInChild()
		mic.parent=self
		self.add_child(mic)

if __name__=='__main__':
	from multiprocessing import Queue
	import time
	m=MidiInBlock()
	m.start()
	q=m.outputs['notes']
	try:
		while True:
			while not q.empty():
				print q.get()
	except KeyboardInterrupt:
		print "caught ctrl-c"
		m.shutdown()
		m.join()
