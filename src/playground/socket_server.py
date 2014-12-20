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
		# let there be connectivity 
		while True:
			print 'Waiting for connections from client...'
			connection, address = self.socket.accept()
			print '%s:%s connected to the server' % (address)

			while True:
				data = connection.recv(1024)
				if not data:
					break;
				self.process_client_request(data)
				connection.send('200 OK')
		# lets close the connection for now
		connection.close()

	def process_client_request(self, data):
		print 'received data from client: ' + data
		pass


if __name__ == '__main__':
	s = server()