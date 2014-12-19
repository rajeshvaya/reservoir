''' This is the playground server for testing out different aspects of the caching system. The realy code will be in ./src'''

import socket

class server:
	def __init__(self):
		print 'going to initialize'
		self.host = 'localhost'
		self.port = 3142 # respect PI 

		print 'opening the socket on port %s ' % (self.port)
		self.socket = socket.socket()
		# connect to the server
		self.bind()
		self.listen()
		self.open()

	def bind(self):
		self.socket.bind((self.host, self.port))

	def listen(self):
		self.socket.listen(2) # allow max of 2 clients

	def open(self):
		print 'All set to accept clients now ... '
		# let there be connectivity 
		while True:
			connection, address = self.socket.accept()
			print '%s:%s connected to the server' % (address)
			connection.send('You are not connected to server.')
			#lets close the connection for now
			connection.close()


if __name__ == '__main__':
	s = server()