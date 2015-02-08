'''
This class is the base for every response type reservoir sends out. All the headers for the response should also be defaulted here
'''

import json

class ReservoirResponse:
	data = None
	def __init__(self):
		pass

	def set(self, data):
		self.data = data
		
	def __str__(self):
		return self.data