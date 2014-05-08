from ooo import CandyBlock
import pygame
import pygame.midi

class MidiInBlock(CandyBlock):
	INPUTS=[]
	OUTPUTS=['notes']

	def process(self):
		pygame.init()
		pygame.midi.init()
		print "# of MIDI devices:",pygame.midi.get_count()
		device_id=3
		midi_in=pygame.midi.Input(device_id)
		q=self.outputs['notes']
		while self.keep_running():
			for e in midi_in.read(1024):
				e=e[0]

				if e[0]==144:
					q.put({'note_on':{'note':e[1],'velocity':e[2]}})
				elif e[0]==128:
					q.put({'note_off':{'note':e[1]}})
			# yield?

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
			m.handle_errors()
	except KeyboardInterrupt:
		print "caught ctrl-c"
		m.stop()
		m.join()
