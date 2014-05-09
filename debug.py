import block
from ooo import CandyBlock

class PrintBlock(CandyBlock):
	def __init__(self):
		self.INPUTS=[('print',self.print_to_screen)]
		self.OUTPUTS=[]

		CandyBlock.__init__(self)

	def print_to_screen(self,value):
		print value

