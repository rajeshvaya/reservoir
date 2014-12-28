''' This is the playground server for testing out different aspects of the caching system. The realy code will be in ./src '''

import sys
import socket
import os
import resource
import time
import argparse
import pickle
import threading
from ConfigParser import SafeConfigParser

from drop import Drop
from utilities import *


class Server:
    def __init__(self, **configs):
        print 'going to initialize'
        self.configs = configs
        self.host = configs.get('host', 'localhost')
        self.port = configs.get('port', 3142) # respect PI 

        #set the memory limit
        if configs.get('max_memory_allocation') != 0:
            self.memory_limit = size_in_bytes(configs.get('max_memory_allocation', '32M')) # defaults to 32 MB
        else:
            self.memory_limit = None

        #persistance
        self.persistance = True if configs.get('persistance', None) == 'yes' else False
        if self.persistance:
            self.persistance_interval = configs.get('persistance_interval', 300) # persist every 5 minutes by defaut

        self.reservoir = {}

        print 'opening the socket on port %s ' % (self.port)
        self.socket = socket.socket()
        # set the memory limit
        self.set_resource_utilization_limits()
        # load persist data if enabled and start timer
        self.fetch_persistant_data()
        self.persistance_cycle()
        # connect to the server
        self.bind()
        self.listen()
        self.open()

    def set_resource_utilization_limits(self):
    	if not self.memory_limit or self.memory_limit == 0:
    		return

    	# get the soft and hard limits for the heap limit - this is default
    	soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_AS)
    	resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit, hard_limit))

    	soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_DATA)
    	resource.setrlimit(resource.RLIMIT_DATA, (self.memory_limit, hard_limit))

    def persistance_cycle(self):
        if not self.persistance:
            return False

        print 'Enabling persistance cycle at %d seconds' % (self.persistance_interval)
        self.persistance_thread = threading.Timer(self.persistance_interval, self.save_persist_data).start()
        
    def fetch_persistant_data(self):
        if not self.persistance:
            return False
        print 'Loading data from last persistance cycle'
        try:
            with open('data/data.pickle', 'rb') as file_handle:
                data = pickle.load(file_handle)
                if isinstance(data, dict):
                    self.reservoir = data
        except (IOError, EOFError) as error:
            pass

    def save_persist_data(self):
        print "inside save persistance function"
        if not self.persistance:
            return False

        print 'Save cache to persist'
        with open('data/data.pickle', 'wb') as file_handle:
            pickle.dump(self.reservoir, file_handle, 0)

        self.persistance_cycle()

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
        except MemoryError as e:
        	print e
        	# TODO: handle the client data for out of memory issue
        except Exception as e:
            print e
            self.connection.close()


    def process_client_request(self, data):
        print 'received data from client: ' + data
        if len(data) < 3:
            self.response("INVALID_DATA")
            return
        # FORMAT = <PROTOCOL> <KEY>
        if data[:3] == 'GET':
            data_parts = data.split(' ')
            self.response(self.get(data_parts[1]))

        # FORMAT = <PROTOCOL> <EXPIRY> <KEY> <VALUE> 
        if data[:3] in ['SET', 'DEP']:
            data_parts = data.split(' ', 3)
            protocol = data_parts[0]
            expiry = data_parts[1]
            key = data_parts[2]
            value = data_parts[3]
            if protocol == 'DEP':
            	parent_key, key = key.split('::', 1)

            if self.set(key, value, expiry):
            	if protocol == 'DEP':
            		drop = self.reservoir.get(parent_key, None)
            		if drop:
            			drop.add_dependant(key)

                self.response("200 OK")
            else:
                self.response("500 ERROR")

        if data[:3] == 'DEL':
            data_parts = data.split(' ')
            self.delete(data_parts[1])
            self.response("200 OK") # fire and forget

         # Get Or Set
        if data[:3] == 'GOS':
            data_parts = data.split(' ', 3)
            expiry = data_parts[1]
            key = data_parts[2]
            value = data_parts[3]
            self.response(self.get_or_set(key, value, expiry))

    # TODO: batch sets
    # TODO: need to delete the oldest entry when memory is full, currently return false
    def set(self, key, value, expiry=0):
        print 'inside of set function'
        d = Drop()
        d.set(value, expiry)
        self.reservoir[key] = d
        return True
        
    # TODO: batch gets
    # TODO: need to check on expiry later
    def get(self, key):
        drop = self.reservoir.get(key, None)
        if drop:
            return drop.get()
        if self.reservoir.has_key(key):
            self.delete(key)
        return None

    # TODO: batch deletes
    def delete(self, key):
        if self.reservoir.has_key(key):
        	# dependants also include the key in question
        	dependants = set(self.get_dependants_tree(key))
        	for dependant in dependants:
        		if self.reservoir.has_key(dependant):
		            # unset the drop for garbage collection
		            del self.reservoir[dependant]
		            # delete the reference
		            self.reservoir.pop(dependant, None)
    	return

    # recursive
    def get_dependants_tree(self, key):
    	dependants = [key]
    	if self.reservoir.has_key(key):
    		drop = self.reservoir[key]
    		for dependant in drop.dependants:
    			dependants += self.get_dependants_tree(dependant)
    		return dependants
    		
    # TODO: wrapper code to set cache if get fails with optional value
    def get_or_set(self, key, value, expiry=0):
        if self.reservoir.has_key(key):
            return self.get(key)
        else:
            self.set(key, value, expiry)
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
        max_memory_allocation=config.get('server', 'max_memory_allocation'),
        persistance=config.get('server', 'persistance'),
        persistance_interval=config.getint('server', 'persistance_interval'),
    )
