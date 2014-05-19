import os
from ctypes import *
import threading
from ooo import CandyBlock
import time

class SynthBlock(CandyBlock):
	def __init__(self,chunksize,rate,maxnotes=100):
		self.INPUTS=[('notes',self.recv_note),('clock',self.step)]
		self.OUTPUTS=['sound']

		CandyBlock.__init__(self)

		self.maxnotes=maxnotes
		self.synth_c=cdll.LoadLibrary(os.path.join(os.path.dirname(os.path.abspath(__file__)),'synth.o'))
		c_int.in_dll(self.synth_c,'rate').value=rate
		c_int.in_dll(self.synth_c,'chunksize').value=chunksize
		self.c_buf=(c_float*chunksize)()
		self.c_note_arr=(self.NOTE*maxnotes)()
		self.notes={}
		self.notelock=threading.Lock()

	class NOTE(Structure):
		_fields_ = [
			('active',c_char),
			('note',c_int),
			('velocity',c_float),
			('t',c_float),
			('hit',c_float),
			('release',c_float)]

	def recv_note(self,e):
		with self.notelock:
			et=e['event_type']
			if et=='note_on':
				n=e['note']
				v=e['velocity']
				if n not in self.notes:
					if len(self.notes)<self.maxnotes:
						self.notes[n]={'velocity':v,'t':0.,'hit':0.,'release':-1.}
				else:
					self.notes[n]['velocity']=v
					self.notes[n]['hit']=self.notes[n]['t']
			elif et=='note_off':
				n=e['note']
				self.notes[n]['release']=self.notes[n]['t']

	def synth(self):
		with self.notelock:
			n_n=0
			for (n,note) in self.notes.items():
				self.c_note_arr[n_n].active=chr(1)
				self.c_note_arr[n_n].note=n
				self.c_note_arr[n_n].velocity=note['velocity']
				self.c_note_arr[n_n].t=note['t']
				self.c_note_arr[n_n].hit=note['hit']
				self.c_note_arr[n_n].release=note['release']
				n_n+=1

			self.synth_c.synth(pointer(self.c_buf),pointer(self.c_note_arr),c_int(n_n))

			self.notes.clear()
			for i in range(n_n):
				c_note=self.c_note_arr[i]
				if not ord(c_note.active):
					continue
				self.notes[c_note.note]={'velocity':c_note.velocity,'t':c_note.t,'hit':c_note.hit,'release':c_note.release}

		return list(self.c_buf)

	def step(self,value):
		out=self.synth()
		self.send('sound',out)
