''' This is the playground client for testing out different aspects of the caching system. The realy code will be in ./src'''

import socket

class client:
	def __init__(self):
		self.port = 3142
		self.socket = socket.socket()
		self.host = 'localhost'

		# now connect
		self.connect()
		
	def connect(self):
		print 'connecting to the server %s' % (self.host)
		self.socket.connect((self.host, self.port))
		print self.socket.recv(1024)
		self.socket.close()

if __name__ == '__main__':
	c = client()
