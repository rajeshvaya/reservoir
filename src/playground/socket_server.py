''' This is the playground server for testing out different aspects of the caching system. The realy code will be in ./src '''

import socket
import os
import argparse
from ConfigParser import SafeConfigParser

from drop import Drop

class Server:
	def __init__(self, **configs):
		print 'going to initialize'
		self.configs = configs
		self.host = configs.get('host', 'localhost')
		self.port = configs.get('port', 3142) # respect PI 
		self.reservoir = {}

		print 'opening the socket on port %s ' % (self.port)
		self.socket = socket.socket()
		# connect to the server
		self.bind()
		self.listen()
		self.open()

	def bind(self):
		self.socket.bind((self.host, self.port))

	def listen(self):
		self.socket.listen(self.configs.get('max_clients', 2)) # allow max of 2 clients by default

	# TODO: check to implement UDP protocol - fire and forget
	def open(self):
		try:
			# let there be connectivity 
			while True:
				print 'Waiting for connections from client...'
				self.connection, self.address = self.socket.accept()
				print '%s:%s connected to the server' % (self.address)

				while True:
					data = self.connection.recv(self.configs.get('read_buffer', 1024))
					if not data:
						break;
					self.process_client_request(data)
			# lets close the connection for now
			self.connection.close()
		# for testing need to close the connection on keyboard interrupt
		except Exception as e:
			print e
			self.connection.close()


	def process_client_request(self, data):
		print 'received data from client: ' + data
		if len(data) < 3:
			self.response("INVALID_DATA")
			return

		if data[:3] == 'GET':
			data_parts = data.split(' ')
			self.response(self.get(data_parts[1]))

		if data[:3] == 'SET':
			data_parts = data.split(' ', 2)
			if self.set(data_parts[1], data_parts[2]):
				self.response("200 OK")
			else:
				self.response("500 ERROR")

		if data[:3] == 'DEL':
			data_parts = data.split(' ')
			self.delete(data_parts[1])
			self.response("200 OK") # fire and forget

		 # Get Or Set
		if data[:3] == 'GOS':
			data_parts = data.split(' ', 2)
			self.response(self.get_or_set(data_parts[1], data_parts[2]))

	# TODO: need to add expiry
	# TODO: batch sets
	def set(self, key, value):
		d = Drop()
		d.set(value)
		self.reservoir[key] = d
		return True

	# TODO: batch gets
	# TODO: need to check on expiry later
	def get(self, key):
		drop = self.reservoir.get(key, None)
		if drop:
			return drop.get()
		return None

	# TODO: batch deletes
	def delete(self, key):
		if self.reservoir.has_key(key):
			del self.reservoir[key]
		return 

	# TODO: wrapper code to set cache if get fails with optional value
	def get_or_set(self, key, value):
		if self.reservoir.has_key(key):
			return self.get(key)
		else:
			self.set(key, value)
			return value

	def response(self, data):
		if data:
			self.connection.send(data)
		else:
			self.connection.send("None") # No data
		



if __name__ == '__main__':
	config = SafeConfigParser()
	config.read([
		os.path.join(os.path.dirname(__file__), 'conf/default.conf'),
		# any other files to overwrite defaults here
	])

	s = Server(
		host=config.get('server', 'host'),
		port=config.getint('server', 'port'),
		max_clients=config.getint('server', 'max_clients'),
		read_buffer=config.getint('server', 'read_buffer'),
	)
