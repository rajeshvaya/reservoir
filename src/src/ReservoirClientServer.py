import socket
import os
import argparse
import pickle
from ConfigParser import SafeConfigParser

class Client:
    def __init__(self, **configs):
        self.configs = configs
        self.host = configs.get('server_host', 'localhost') # defaults to localhost
        self.port = configs.get('server_port', 3142)
        self.socket = socket.socket()
    
        # now connect
        self.connect()
        self.prompt()
        
    def connect(self):
        print 'connecting to the server %s' % (self.host)
        self.socket.connect((self.host, self.port))

    def set(self, key, value, expiry):
        data = "SET %d %s %s" % (expiry, key, value)
        return self.send(data)

    def get(self, key):
        data = "GET %s" % (key)
        return self.send(data)

    def delete(self, key):
        data = "DEL %s" % (key)
        return self.send(data)

    def icr(self, key, expiry=0):
        # send expiry=0 for already existing key for ICR
        # need to imporve the evaluation for ICR on the server side
        data = "ICR %d %s" % (expiry, key)
        return self.send(data)

    def icr(self, key, expiry=0):
        # send expiry=0 for already existing key for DCR
        data = "DCR %d %s" % (expiry, key)
        return self.send(data)

    def tmr(self, key):
        data = "TMR %s" % (key)
        return self.send(data)

    def get_or_set(self, key, value, expiry):
        data = "GOS %d %s %s" % (expiry, key, value)
        return self.send(data)

    def ping_server(self):
        data = "PING"
        return True if self.send(data) == 1 else False # this should return boolean only

    # get the entire tree <key> as starting parent
    def get_with_dependants(self, key):
        pass

    def send(self, data, expect_return=True):
        self.socket.send(data)
        if expect_return:
            response = self.socket.recv(self.configs.get('read_buffer', 1024))
            return response
        else:
            return True
        
    def prompt(self):
        try:
            while True:
                # get data from command line
                data = raw_input('=> ')
                if not data:
                    continue
                # send the data to the server
                self.socket.send(data)
                response = self.socket.recv(self.configs.get('read_buffer', 1024))
                print response
        except Exception as e:
            self.socket.close()
            print e
