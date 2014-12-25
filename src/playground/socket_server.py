''' This is the playground server for testing out different aspects of the caching system. The realy code will be in ./src '''

import sys
import socket
import os
import time
import argparse
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
        # FORMAT = <PROTOCOL> <KEY>
        if data[:3] == 'GET':
            data_parts = data.split(' ')
            self.response(self.get(data_parts[1]))

        # FORMAT = <PROTOCOL> <EXPIRY> <KEY> <VALUE> 
        if data[:3] == 'SET':
            data_parts = data.split(' ', 3)
            expiry = data_parts[1]
            key = data_parts[2]
            value = data_parts[3]
            if self.set(key, value, expiry):
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
        if self.check_memory_limit(d):
            self.reservoir[key] = d
            print sys.getsizeof(self.reservoir)
            print self.reservoir
            return True
        else:
            return False
        

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
            # unset the drop for garbage collection
            del self.reservoir[key]
            # delete the reference
            self.reservoir.pop(key, None)
        return 

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

    def check_memory_limit(self, drop):
        if self.memory_limit == None:
            return True
            
        memory_in_use = sys.getsizeof(self.reservoir)
        memory_of_drop = sys.getsizeof(drop)

        if (memory_of_drop + memory_in_use) >= self.memory_limit:
            return False
        else:
            return True
        

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
    )
