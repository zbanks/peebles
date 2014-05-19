from ooo import CandyBlock
import threading
import math
import time

class SynthBlock(CandyBlock):
	def __init__(self,chunksize,rate):
		self.INPUTS=[('notes',self.recv_note),('clock',self.step)]
		self.OUTPUTS=['sound']

		CandyBlock.__init__(self)

		self.chunksize=chunksize
		self.rate=rate

		self.notes={}
		self.notelock=threading.Lock()
		self.chunkrange=range(self.chunksize)

	def recv_note(self,e):
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
		def f(x):
			if x%1>0.5:
				return 1
			return -1

		freq = 440*2**((note-69)/12.0)
		return float(velocity)*f(freq*t)/128

	def reduce_fn(self,values):
		return sum(values)

	def step(self,value):
		t=time.time()
		with self.notelock:
			active_notes=self.notes.items()
			for note in self.notes:
				self.notes[note]['t']+=float(self.chunksize)/self.rate
		out=[self.reduce_fn([self.synthesize(note,params['velocity'],params['t']+float(i)/self.rate) for (note,params) in active_notes]) for i in self.chunkrange]
		t=time.time()-t
		#print t
		self.send('sound',out)

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
