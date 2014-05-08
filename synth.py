class SynthBlock(SoulBlock):
	INPUTS=['notes']
	OUTPUTS=['samples']

	def init(self):
		pass

	def step(self):
		self.outputs['samples'].put([0*self.chunksize])

if __name__=='__main__':
	from multiprocessing import Queue
	import time
	s=SynthBlock()
	s.start()
	q=s.outputs['samples']
	try:
		while True:
			s.clock()
			print q.get()
			s.handle_errors()
	except KeyboardInterrupt:
		print "caught ctrl-c"
		s.stop()
		s.join()
