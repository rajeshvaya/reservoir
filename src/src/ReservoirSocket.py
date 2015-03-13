'''
This is the wrapper for socket class which will contain creation of TCP & UDP sockets and interactions wit the sockets.
It should als maintain the threads for each client connections
'''
 
import socket
import threading
import json
import logging
from thread import start_new_thread

from ReservoirResponse import ReservoirResponse


class ReservoirSocket:

    def __init__(self, reservoir, configs):
        self.configs = configs
        self.reservoir = reservoir

        self.host = self.reservoir.host
        self.port = self.reservoir.port

        self.connections = []

        # set the protocol to follow
        protocol = self.configs.get('protocol', 'TCP')
        self.protocol = protocol if protocol in ['TCP', 'UDP'] else 'TCP'

        # lets go
        self.socket = self.create_socket()
        pass

    def create_socket(self):
        self.reservoir.logger.info("creating %s socket now" % (self.protocol))
        if self.protocol == 'TCP':
            return socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif self.protocol == 'UDP':
            return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            return socket.socket
    
    def bind(self):
        if self.protocol == 'TCP':
            return self.tcp_bind();
        elif self.protocol == 'UDP':
            return self.udp_bind();
        return False

    def listen(self):
        if self.protocol == 'TCP':
            return self.tcp_listen();
        elif self.protocol == 'UDP':
            return self.udp_listen();

    def open(self):
        if self.protocol == 'TCP':
            self.tcp_open();
        elif self.protocol == 'UDP':
            self.udp_open();
    
    # TCP functions here
    def tcp_bind(self):
        self.reservoir.logger.info("binding the socket on %s:%d" % (self.host, self.port))
        try:
            self.socket.bind((self.host, self.port))
            return True
        except Exception as e:
            self.reservoir.logger.error(str(e))
            return False

    def tcp_listen(self):
        self.socket.listen(self.configs.get('max_clients', 2)) # allow max of 2 clients by default

    def tcp_open(self):
        # let there be connectivity 
        while True:
            self.reservoir.logger.info("Waiting for client connections")
            connection, address = self.socket.accept()
            self.connections.append(connection)
            self.reservoir.logger.info('%s:%s connected to the server' % (address))
            start_new_thread(self.start_tcp_client_thread, (connection,))

    # Create new thread for each client. don't let the thread die
    def start_tcp_client_thread(self, connection):
        try:
            while True:
                data = connection.recv(self.configs.get('read_buffer', 1024))
                if not data:
                    break;
                self.reservoir.process_client_request(connection, data)
            connection.close()
        # for testing need to close the connection on keyboard interrupt
        except MemoryError as e:
            print e
            # TODO: handle the client data for out of memory issue
        except Exception as e:
            self.reservoir.logger.error("Error occurred while starting TCP client thread : %s" % (str(e)))
            connection.close()

    # UDP functions here
    def udp_bind(self):
        try:
            self.socket.bind((self.host, self.port))
            return True
        except Exception as e:
            self.reservoir.logger.error("Error occurred while starting UDP client thread : %s" % (str(e)))

    def udp_listen(self):
        # there is no listening in UDP, only fire and forget
        pass

    def udp_open(self):
        while True:
            packet = self.socket.recvfrom(self.configs.get('read_buffer', 1024))
            data = packet[0]
            address = packet[1]
            start_new_thread(self.start_udp_client_thread, (address, data))

    def start_udp_client_thread(self, address, data):
        try:
            self.reservoir.process_client_request(address, data)
        except MemoryError as e:
            self.reservoir.logger.error("Out of memory while processing client request: %s" % (str(e)))
            # TODO: handle the client data for out of memory issue
        except Exception as e:
            self.reservoir.logger.error("Error occurred while processing client request : %s" % (str(e)))

    def response(self, connection, response):
        if not isinstance(response, ReservoirResponse):
            connection.send("None")

        if self.protocol == 'TCP':
            connection.send(response.get_output())
        if self.protocol == 'UDP':
            self.socket.sendto(response.get_output(), connection) # over here connection is the host address


