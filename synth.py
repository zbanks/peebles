from ooo import SoulBlock
import threading
import math

class SynthBlock(SoulBlock):
	INPUTS=['notes']
	OUTPUTS=['samples']

	def init(self):
		self.notes={}
		self.notelock=threading.Lock()

	def process(self):
		q=self.inputs['notes']
		while True:
			e=q.get()
			if not self.keep_running:
				break
			with self.notelock:
				if 'note_on' in e:
					p=e['note_on']
					n=p['note']
					v=p['velocity']
					if n not in self.notes:
						self.notes[n]={'velocity':v,'t':0.}
					else:
						self.notes[n]['velocity']=v
				elif 'note_off' in e:
					del self.notes[e['note_off']['note']]

	def synthesize(self,note,velocity,t):
		freq = 440*2**((note-69)/12.0)
		# [t] = sec
		# [rate] = samp / sec
		# [2 pi freq] = 1 / sec
		# sin(
		return float(velocity)*math.sin(freq*2*math.pi*t)/128

	def reduce_fn(self,values):
		return sum(values)

	def stop(self):
		SoulBlock.stop(self)
		self.inputs['notes'].put(None)

	def step(self):
		with self.notelock:
			active_notes=self.notes.items()
			for note in self.notes:
				self.notes[note]['t']+=float(self.chunksize)/self.rate
		out=[self.reduce_fn([self.synthesize(note,params['velocity'],params['t']+float(i)/self.rate) for (note,params) in active_notes]) for i in range(self.chunksize)]
		self.outputs['samples'].put(out)
			

if __name__=='__main__':
	from multiprocessing import Queue
	from output import PyaudioOutputNightBlock
	import time
	from midi_in import MidiInBlock
	m=MidiInBlock()
	m.start()
	mq=m.outputs['notes']
	po = PyaudioOutputNightBlock(256, 48000)
	po.start()
	s=SynthBlock(256,48000)
	s.start()
	qi=s.inputs['notes']
	qo=s.outputs['samples']
	try:
		qi.put({'note_on':{'note':72,'velocity':100}})
		while True:
			#print 1
			s.clock()
			po.clock()
			d = qo.get(1)
			po.inputs['sound'].put((False, d))
			try:
				md = mq.get_nowait()
				print md
				qi.put(md)
			except:
				pass
			#print d[0:4]
			s.handle_errors()
			po.handle_errors()
			m.handle_errors()
			time.sleep(0.001)
	except KeyboardInterrupt:
		print "caught ctrl-c"
		s.stop()
		s.join()
		m.stop()
		m.join()
		po.stop()
		po.join()
