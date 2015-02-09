'''
This class is the base for every response type reservoir sends out. All the headers for the response should also be defaulted here
'''

import json

class ReservoirResponse:
	data = None
	messages = {
		200: 'OK',
		500: 'ERROR'
	}

	def __init__(self):
		pass

	def set(self, data):
		self.data = data

	def get_message(self, code):
		return self.messages.get(code, 'ERROR')

	def status(self, code):
		pass

	def __str__(self):
		return self.data