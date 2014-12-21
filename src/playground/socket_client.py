''' This is the playground client for testing out different aspects of the caching system. The realy code will be in ./src'''

import socket

class client:
	def __init__(self):
		self.port = 3142
		self.socket = socket.socket()
		self.host = 'localhost'

		# now connect
		self.connect()
		self.prompt()
		
	def connect(self):
		print 'connecting to the server %s' % (self.host)
		self.socket.connect((self.host, self.port))

	def prompt(self):
		try:
			while True:
				# get data from command line
				data = raw_input('=> ')
				if not data:
					continue
				# send the data to the server
				self.socket.send(data)
				response = self.socket.recv(1024)
				print response
		except Exception as e:
			self.socket.close()
			print e



if __name__ == '__main__':
	c = client()
