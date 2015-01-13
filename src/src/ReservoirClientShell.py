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
