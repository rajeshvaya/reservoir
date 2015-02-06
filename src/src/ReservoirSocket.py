'''
This is the wrapper for socket class which will contain creation of TCP & UDP sockets and interactions wit the sockets.
It should als maintain the threads for each client connections
'''
 
import socket

class ReservoirSocket:
    def __init__(self, reservoir, **configs):
        self.configs = configs
        self.reservoir = reservoir

        self.connections = []
        
        protocol = self.configs.get('protocol', 'TCP')
        self.protocol = protocol if protocol in ['TCP', 'UDP'] else 'TCP'

        self.socket = self.create_socket()
        pass

    def create_socket(self):
        if self.protocol == 'TCP':
            return socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif self.protocol == 'UDP':
            return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            return socket.socket()

    # TCP functions here
    def tcp_bind(self):
        self.socket.bind((self.host, self.port))

    def tcp_listen(self):
        self.socket.listen(self.configs.get('max_clients', 2)) # allow max of 2 clients by default

    def tcp_open(self):
        # let there be connectivity 
        while True:
            print 'Waiting for connections from client...'
            connection, address = self.socket.accept()
            self.connections.append(connection)
            print '%s:%s connected to the server' % (address)
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
            print e
            connection.close()

    # UDP functions here
    def udp_bind(self):
        self.socket.bind((self.host, self.port))

    def udp_listen(self):
        # there is no listening in UDP, only fire and forget
        pass

    def udp_open(self):
        while True:
            print 'Waiting for UDP packets'
            packet = self.socket.recvfrom(self.configs.get('read_buffer', 1024))
            data = packet[0]
            address = packet[1]
            start_new_thread(self.start_udp_client_thread, (address, data))

    def start_udp_client_thread(self, address, data):
        try:
            self.reservoir.process_client_request(address, data)
        except MemoryError as e:
            print e
            # TODO: handle the client data for out of memory issue
        except Exception as e:
            print e

    def response(self, connection, data):
        if self.protocol == 'TCP':
            connection.send(data if data else "None")
        if self.protocol == 'UDP':
            self.socket.sendto(data if data else "None", connection) # over here connection is the host address
