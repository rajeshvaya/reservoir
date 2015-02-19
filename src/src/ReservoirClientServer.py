import socket
import os
import argparse
import pickle
import json
from ConfigParser import SafeConfigParser

class Client:
    def __init__(self, **configs):
        self.configs = configs
        self.host = configs.get('server_host', 'localhost') # defaults to localhost
        self.port = configs.get('server_port', 3142)

        # set the protocol to follow
        self.protocol = configs.get('protocol', 'TCP') # defaults to reliable one - TCP
        if self.protocol not in ['TCP', 'UDP']:
            self.protocol = 'TCP' 

        # self.socket = socket.socket()
        self.create_socket()

        # now connect
        self.connect()

    def create_socket(self):
        if self.protocol == 'TCP':
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif self.protocol == 'UDP':
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self.socket = socket.socket()
        
    def connect(self):
        if self.protocol == 'TCP':
            print 'connecting to the server %s' % (self.host)
            self.socket.connect((self.host, self.port))

        if self.protocol == 'UDP':
            print 'No connection required for UDP'

    def set(self, key, value, expiry):
        batch = [{
            'key': key,
            'data': value,
            'expiry': expiry
        }]
        data_string = json.dumps(batch)
        data = "SET %s" % (data_string,)
        return self.send(data)

    def get(self, key):
        batch = [{
            'key': key
        }]
        data = "GET %s" % (data_string,)
        return self.send(data)

    def delete(self, key):
        batch = [{
            'key': key
        }]
        data = "DEL %s" % (data_string,)
        return self.send(data)

    def icr(self, key, expiry=0):
        # send expiry=0 for already existing key for ICR
        # need to imporve the evaluation for ICR on the server side
        batch = [{
            'key': key,
            'expiry': expiry
        }]
        data_string = json.dumps(batch)
        data = "ICR %s" % (data_string,)
        return self.send(data)

    def dcr(self, key, expiry=0):
        # send expiry=0 for already existing key for DCR
        batch = [{
            'key': key,
            'expiry': expiry
        }]
        data_string = json.dumps(batch)
        data = "DCR %s" % (data_string,)
        return self.send(data)

    def tmr(self, key):
        batch = [{
            'key': key,
        }]
        data_string = json.dumps(batch)
        data = "TMR %s" % (data_string,)
        return self.send(data)

    def ota(self, key, value, expiry):
        batch = [{
            'key': key,
            'data': value,
            'expiry': expiry
        }]
        data_string = json.dumps(batch)
        data = "OTA %s" % (data_string,)
        return self.send(data)

    def tpl(self, key, value, expiry):
        batch = [{
            'key': key,
            'data': value,
            'expiry': expiry
        }]
        data_string = json.dumps(batch)
        data = "TPL %s" % (data_string,)
        return self.send(data)

    def get_or_set(self, key, value, expiry):
        batch = [{
            'key': key,
            'data': value,
            'expiry': expiry
        }]
        data_string = json.dumps(batch)
        data = "GOS %s" % (data_string,)
        return self.send(data)

    def ping_server(self):
        data = "PING"
        return True if self.send(data) == 1 else False # this should return boolean only

    # get the entire tree <key> as starting parent
    def get_with_dependants(self, key):
        pass

    def send(self, data, expect_return=True):
        if protocol == 'TCP':
            self.socket.send(data)
            if expect_return:
                response = self.socket.recv(self.configs.get('read_buffer', 1024))
                return response
            else:
                return True

        if self.protocol == 'UDP':
            self.socket.sendto(data, (self.host, self.port))
            if expect_return:
                packet = self.socket.recvfrom(self.configs.get('read_buffer', 1024))
                response = packet[0]
                address = packet[1]
                return response
