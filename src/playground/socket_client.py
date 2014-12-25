''' This is the playground client for testing out different aspects of the caching system. The realy code will be in ./src'''

import socket
import os
import argparse
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



if __name__ == '__main__':
    config = SafeConfigParser()
    config.read([
        os.path.join(os.path.dirname(__file__), 'conf/default.conf'),
        # any other files to overwrite defaults here
    ])

    c = Client(
        server_host=config.get('client', 'server_host'),
        server_port=config.getint('client', 'server_port'),
    )
