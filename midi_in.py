from ooo import CandyBlock
import pygame
import pygame.midi

class MidiInBlock(CandyBlock):
	INPUTS=0
	OUTPUTS=1

	def process(self):
		pygame.init()
		pygame.midi.init()
		print "# of MIDI devices:",pygame.midi.get_count()
		device_id=3
		midi_in=pygame.midi.Input(device_id)
		while self.keep_running():
			while True:
				e=midi_in.read(1)
				if len(e)==0:
					break
				e=e[0][0]

				if e[0]==144:
					self.outputs[0].put({'note_on':{'note':e[1],'velocity':e[2]}})
				elif e[0]==128:
					self.outputs[0].put({'note_off':{'note':e[1]}})
			# yield?

if __name__=='__main__':
	from multiprocessing import Queue
	import time
	q=Queue()
	err=Queue()
	m=MidiInBlock([],[q],err)
	m.start()
	try:
		while True:
			while not q.empty():
				print q.get()
			m.handle_errors()
	except KeyboardInterrupt:
		print "caught ctrl-c"
		m.stop()
		m.join()
