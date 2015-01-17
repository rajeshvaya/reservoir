'''
This is the main reserver server and there should be another main file to make it a command line app
as this will be also imported for web based libraries
'''

import sys
import socket
import resource
import time

import pickle
import threading
import linecache

from ReservoirDrop import Drop
from ReservoirUtilities import *

class Server:
    def __init__(self, **configs):
        print 'going to initialize'
        self.configs = configs
        self.host = configs.get('host', 'localhost')
        self.port = configs.get('port', 3142) # respect PI 

        # set the memory limit
        if configs.get('max_memory_allocation') != 0:
            self.memory_limit = size_in_bytes(configs.get('max_memory_allocation', '32M')) # defaults to 32 MB
        else:
            self.memory_limit = None

        # persistance
        self.persistance = True if configs.get('persistance', None) == 'yes' else False
        if self.persistance:
            self.persistance_interval = configs.get('persistance_interval', 300) # persist every 5 minutes by defaut

        # garbage collection
        self.garbage_collection_interval = configs.get('garbage_collection_interval', 0) # by default disable the gc
        # max dependants depth
        self.max_depandants_depth = configs.get('max_depandants_depth', 10) # detaults to 10

        self.reservoir = {}

        # replication
        self.replication = True if configs.get('replication', None) == 'yes' else False
        self.replication_type=configs.get('replication', 'master') # defaults to standard master
        self.replication_master_server = configs.get('replication_master_server', None)
        self.replication_slave_servers = [x.strip() for x in configs.get('replication_max_replay_logs', '').split(',')]
        self.replication_max_replay_logs = configs.get('replication_max_replay_logs', 100) # defaults to 100
        self.replication_sync_interval = configs.get('replication_sync_interval', 10) # defaults to 10

        print 'opening the socket on port %s ' % (self.port)
        self.socket = socket.socket()
        # set the memory limit
        self.set_resource_utilization_limits()
        # load persist data if enabled and start timer
        self.fetch_persistant_data()
        self.persistance_cycle()
        self.garbage_collection_cycle()
        self.sync_replication_replay_logs_cycle()
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

    def garbage_collection_cycle(self):
        if self.garbage_collection_interval > 0:
            print 'going for garbage collection'
            self.garbage_collection_thread = threading.Timer(self.garbage_collection_interval, self.garbage_collection).start()

    def garbage_collection(self):
        for key, drop in self.reservoir.items():
            if drop.is_expired():
                self.delete(key)

        self.garbage_collection_cycle()
    
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

        # confirm connectivity
        if data == 'PING':
            self.response(1)

        # replication replay logs
        if data[:11] == 'REPLICATION':
            data_parts = data.split(' ')
            current_position = data_parts[1]
            self.response(self.get_replication_replay_logs(current_position))

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
            parent_key = None
            if protocol == 'DEP':
                parent_key, key = key.split('::', 1)

            if self.set(key, value, expiry, parent_key=parent_key):
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

        # incrementer and decrementer
        if data[:3] == 'ICR':
            data_parts = data.split(' ')
            if not self.reservoir.has_key(data_parts[2]):
                self.set(data_parts[2], 1, data_parts[1])
            else:
                if not self.icr(data_parts[2]):
                    self.response("500 ERROR")
            self.response("200 OK")

        if data[:3] == 'DCR':
            data_parts = data.split(' ')
            if not self.reservoir.has_key(data_parts[2]):
                self.response("500 ERROR")
            else:
                if not self.dcr(data_parts[2]):
                    self.response("500 ERROR")
                self.response("200 OK")

        # timer as a data type; format <TMR> <key>
        if data[:3] == 'TMR':
            data_parts = data.split(' ')
            if self.reservoir.has_key(data_parts[1]):
                return self.reservoir[data_parts[1]].get_active_time() # in seconds
            else:
                self.response("500 ERROR")

         # Get Or Set
        if data[:3] == 'GOS':
            data_parts = data.split(' ', 3)
            expiry = data_parts[1]
            key = data_parts[2]
            value = data_parts[3]
            self.response(self.get_or_set(key, value, expiry))

    # TODO: batch sets
    # TODO: need to delete the oldest entry when memory is full, currently return false
    # TODO: make the key argument in Drop class required for replication replay logs to work
    def set(self, key, value, expiry=0, parent_key=None):
        print 'inside of set function'
        d = Drop(key=key)
        d.set(value, expiry)
        if parent_key:
            d.parent_key = parent_key
        self.reservoir[key] = d
        self.add_to_replication_replay_logs('SET', d)
        return True
        
    # TODO: batch gets
    # TODO: need to check on expiry later
    def get(self, key):
        drop = self.reservoir.get(key, None)
        if drop:
            return str(drop.get())
        if self.reservoir.has_key(key):
            self.delete(key)
        return None

    # TODO: batch deletes
    def delete(self, key):
        if self.reservoir.has_key(key):
            # dependants also include the key in question
            dependants = set(self.get_dependants_tree(key, self.max_depandants_depth))
            for dependant in dependants:
                if self.reservoir.has_key(dependant):
                    d = self.reservoir[dependant]
                    # unset the drop for garbage collection
                    del self.reservoir[dependant]
                    # delete the reference
                    self.reservoir.pop(dependant, None)
                    self.add_to_replication_replay_logs('DEL', d)
        return

    def icr(self, key):
        drop = self.reservoir.get(key, None)
        if drop:
            if not drop.increment():
                return result
            else:
                self.add_to_replication_replay_logs('ICR', d)
                return True
        else:
            return False

    def dcr(self, key):
        drop = self.reservoir.get(key, None)
        if drop:
            if not drop.decrement():
                return result
            else:
                self.add_to_replication_replay_logs('DCR', d)
                return True
        else:
            return False

    # recursive
    def get_dependants_tree(self, key, depth=10):
        dependants = [key]
        if depth <=0:
            return dependants

        next_depth = depth - 1
        if self.reservoir.has_key(key):
            drop = self.reservoir[key]
            for dependant in drop.dependants:
                dependants += self.get_dependants_tree(dependant, next_depth)
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

    def add_to_replication_replay_logs(self, command_type, drop):
        with open('replication/master/server.replay', 'a') as file_handle:
            log = '%s %s\n' % (command_type, drop.get_replay_log())
            file_handle.write(log)
        return 

    def check_data_changes_permissions(self):
        # replication check, slave cannot have data editing
        if self.replication and self.replication_type == 'slave':
            return False
        return True

    def get_replication_replay_logs(self, position):
        # this check is very necessary
        if not self.replication or self.address not in self.replication_slave_servers:
            return False

        data = []
        fetch_position = position + 1
        result = True

        while log_line and fetch_position < position + self.replication_max_replay_logs:
            log_line = linecache.getline('replication/replay_logs/server.replay', fetch_position)
            if log_line:
                data.append(log_line)
                fetch_position += 1
            else:
                result = False
        return data


    # START OF REPLICATION TASKS FOR SLAVE SERVER
    # TODO : need to have best way through threading like we did for persistance and garbage_collection
    def sync_replication_replay_logs_cycle(self):
        if not self.replication or self.replication_type != 'slave':
            return
        if self.address not in self.replication_slave_servers:
            return

        print "going for replication sync"
        self.replication_thread = threading.Timer(self.replication_sync_interval, self.sync_replication_replay_logs)
        pass

    # TODO: find the best way to sync with file splits like MySQL does
    def sync_replication_replay_logs(self):
        if not self.replication:
            return
        logs = self.send("REPLICATION %d" % self.replication_replay_position)
        with open('replication/slave/server.replay', 'a') as file_handle:
            file_handle.write(logs)
        self.sync_replication_replay_logs_cycle()
        return 
    # END OF REPLICATION TASKS FOR SLAVE SERVER

