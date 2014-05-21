import block
from ooo import CandyBlock
from looper import LooperBlock

class PrintBlock(CandyBlock):
	def __init__(self):
		self.INPUTS=[('print',self.print_to_screen)]
		self.OUTPUTS=[]

		CandyBlock.__init__(self)

	def print_to_screen(self,value):
		print value

class MidiControlBlock(CandyBlock):
	def __init__(self):
		self.INPUTS=[('notes',self.recieve_note)]
		self.OUTPUTS=['notes', 'control']

		CandyBlock.__init__(self)

	def recieve_note(self,value):
		if value["note"] == 21: # start/stop record
			if value["event_type"] == "note_on":
				self.outputs["control"].put({"command": LooperBlock.RECORD_START})
			elif value["event_type"] == "note_off":
				self.outputs["control"].put({"command": LooperBlock.RECORD_STOP})
		elif value["note"] == 23: # start/stop record
			if value["event_type"] == "note_on":
				self.outputs["control"].put({"command": LooperBlock.LOOP_FOREVER})
			elif value["event_type"] == "note_off":
				self.outputs["control"].put({"command": LooperBlock.LOOP_STOP})
		else:
			self.outputs["notes"].put(value)

