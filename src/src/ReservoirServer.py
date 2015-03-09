'''
This is the main reserver server and there should be another main file to make it a command line app
as this will be also imported for web based libraries

TODO: change the replication log data to JSON
TODO: support multiple buckets/tags
TODO: convert the buckets to its own class later
'''

import sys
import resource
import time

import pickle
import threading
from thread import start_new_thread
import linecache
import json

from ReservoirSocket import ReservoirSocket
from ReservoirDrop import Drop
from ReservoirUtilities import *
from ReservoirResponse import ReservoirResponse
from ReservoirClientServer import Client as ReplicationClient


class Server:
    def __init__(self, **configs):
        print 'going to initialize'
        self.configs = configs
        self.host = configs.get('host', 'localhost')
        self.port = configs.get('port', 3142) # respect PI
        self.reservoir = {}
        self.buckets = {} # like tags and buckets for cache
        self.connections = []

        self.default_data_format = configs.get('default_data_format', 'raw') # defaults to raw

        # create a new reservoir socket
        self.socket = ReservoirSocket(reservoir=self, configs=configs)

        # set the memory limit
        if configs.get('max_memory_allocation') != 0:
            self.memory_limit = size_in_bytes(configs.get('max_memory_allocation', '128M')) # defaults to 128 MB (minimum 50M required)
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

        # replication
        self.replication = True if configs.get('replication', None) == 'yes' else False
        self.replication_type=configs.get('replication_type', 'master') # defaults to standard master
        self.replication_master_server = configs.get('replication_master_server', None)
        self.replication_slave_servers = [x.strip() for x in configs.get('replication_slave_servers', '').split(',')]
        self.replication_max_replay_logs = configs.get('replication_max_replay_logs', 100) # defaults to 100
        self.replication_sync_interval = configs.get('replication_sync_interval', 10) # defaults to 10
        if self.replication and self.replication_type == 'slave':
            self.replication_replay_position = self.fetch_replication_replay_position()
        else:
            self.replication_replay_position = 0

        # print 'opening the socket on port %s ' % (self.port)
        # self.socket = socket.socket()
        # self.socket.create_socket()

        # set the memory limit
        self.set_resource_utilization_limits()

        # load persist data if enabled and start timer
        self.fetch_persistant_data()

        # start the thread cycles
        self.persistance_cycle()
        self.garbage_collection_cycle()
        self.sync_replication_replay_logs_cycle()

        # let there be socket connectivity
        self.socket.bind()
        self.socket.listen()
        self.socket.open()

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

    def process_client_request(self, connection, data):
        print 'received data from client: ' + data
        response = ReservoirResponse()
        if len(data) < 3:
            response.set("INVALID_DATA")
            self.response(connection, response)
            return

        # confirm connectivity
        if data == 'PING':
            response.set(1)
            self.response(connection, response)

        # replication replay logs
        if data[:11] == 'REPLICATION':
            data_parts = data.split(' ')
            current_position = data_parts[1]
            print self.get_replication_replay_logs(current_position)
            response.set(''.join(self.get_replication_replay_logs(current_position)))
            self.response(connection, response)

        if data[:3] == 'BKT':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            bucket = batch[0].get('bucket', None)
            return_batch = self.get_bucket_batch(bucket)
            return_batch_string = json.dumps(return_batch)
            response.set(return_batch_string)
            self.response(connection, response)

        if data[:3] == 'GET':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            return_batch = self.get_batch(batch)
            return_batch_string = json.dumps(return_batch)
            response.set(return_batch_string)
            self.response(connection, response)

        # FORMAT = <PROTOCOL> <EXPIRY> <KEY> <VALUE> 
        if data[:3] in ['SET', 'DEP']:
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            return_batch = self.set_batch(batch)
            response.set(json.dumps(return_batch))
            self.response(connection, response)

        if data[:3] == 'TPL':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            return_batch = self.tpl_batch(batch)
            response.set(json.dumps(return_batch))
            self.response(connection, response)
    
        if data[:3] == 'DEL':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            return_batch = self.delete_batch(batch)
            response.set(json.dumps(return_batch))
            self.response(connection, response)

        if data[:3] == 'OTA':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            return_batch = self.ota_batch(batch)
            response.set(json.dumps(return_batch))
            self.response(connection, response)

        # incrementer and decrementer
        if data[:3] == 'ICR':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            batch_data = []
            for element in batch:
                if not element.get("key", None):
                    continue

                if not self.reservoir.has_key(element.get("key")):
                    self.set(element.get("key"), 1, element.get("expiry"))
                else:
                    if not self.icr(element.get("key")):
                        batch_data.append({"key": element.get("key"), "data": "500 ERROR"})
                    else:
                        batch_data.append({"key": element.get("key"), "data": "200 OK"})

            return_batch_string = json.dumps(batch_data)
            response.set(return_batch_string)
            self.response(connection, response)


        if data[:3] == 'DCR':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            batch_data = []
            for element in batch:
                if not element.get("key", None):
                    continue

                if not self.reservoir.has_key(element.get("key")):
                    batch_data.append({"key": element.get("key"), "data": "500 ERROR"})
                else:
                    if not self.dcr(element.get("key")):
                        batch_data.append({"key": element.get("key"), "data": "500 ERROR"})
                    else:
                        batch_data.append({"key": element.get("key"), "data": "200 OK"})

            return_batch_string = json.dumps(batch_data)
            response.set(return_batch_string)
            self.response(connection, response)


        # timer as a data type; format <TMR> <key>
        if data[:3] == 'TMR':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            batch_data = []
            for element in batch:
                if not element.get("key", None):
                    continue
                if self.reservoir.has_key(element.get("key")):
                    t = self.reservoir[element.get("key")].get_active_time() # in seconds
                    element_data = {"key":element.get("key"), "data":t}
                    batch_data.append(element_data)

            return_batch_string = json.dumps(batch_data)
            response.set(return_batch_string)
            self.response(connection, response)

         # Get Or Set
        if data[:3] == 'GOS':
            data_parts = data.split(' ', 3)
            expiry = data_parts[1]
            key = data_parts[2]
            value = data_parts[3]
            response.set(self.get_or_set(key, value, expiry))
            self.response(connection, response)

    def get_bucket_batch(self, bucket):
        batch_data = []
        if not self.buckets.get(bucket, None):
            return batch_data

        for drop in self.buckets.get(bucket, []):
            value = self.get(drop)
            element_data = {"key":drop, "data":value}
            batch_data.append(element_data)

        return batch_data

    def get_batch(self, batch):
        batch_data = []
        for element in batch:
            if not element.get("key", None):
                continue
                
            print "element key is ", element.get("key")
            value = self.get(element.get("key"))
            element_data = {"key":element.get("key"), "data":value}
            batch_data.append(element_data)

        return batch_data
        
    # TODO: batch gets - Done
    # TODO: need to check on expiry later
    def get(self, key):
        drop = self.reservoir.get(key, None)
        if drop:
            value = drop.get()
            if drop.get_type() == 'ota':
                self.delete(key)
            return str(value)

        # if orphans are roaming around with no data, delete it
        if self.reservoir.has_key(key):
            self.delete(key)
        return None


    def set_batch(self, batch):
        batch_data = []
        for element in batch:
            expiry = element.get('expiry')
            key = element.get('key')
            value = element.get('data')
            parent_key = element.get('parent_key', None)
            buckets = element.get('buckets', [])

            if self.set(key, value, expiry, parent_key=parent_key, buckets=buckets):
                if parent_key:
                    drop = self.reservoir.get(parent_key, None)
                    if drop:
                        drop.add_dependant(key)
                batch_data.append({"key":key,"data": "200 OK"})
            else:
                batch_data.append({"key":key,"data": "500 ERROR"})
        return batch_data

    # TODO: batch sets - Done
    # TODO: need to delete the oldest entry when memory is full, currently return false
    # TODO: make the key argument in Drop class required for replication replay logs to work
    # TODO: add bucket info to replication log as well
    def set(self, key, value, expiry=0, parent_key=None, buckets=[]):
        print 'inside of set function'
        d = Drop(key=key)
        if not d.set(value, expiry):
            return False
        if parent_key:
            d.parent_key = parent_key

        d.buckets = buckets
        self.reservoir[key] = d
        for bucket in buckets:
            if not self.buckets.get(bucket, None):
                self.buckets[bucket] = []
            self.buckets[bucket].append(key)

        self.add_to_replication_replay_logs('SET', d)
        return True

    def tpl_batch(self, batch):
        batch_data = []
        for element in batch:
            expiry = element.get('expiry')
            key = element.get('key')
            value = element.get('data')

            if self.tpl(key, value, expiry):
                batch_data.append({"key":key,"data": "200 OK"})
            else:
                batch_data.append({"key":key,"data": "500 ERROR"})
                
        return batch_data        

    def tpl(self, key, value, expiry=0):
        print 'inside of tpl function'
        if self.resource.has_key(key):
            if self.reservoir[key].get_type() == 'tpl':
                return False

        d = Drop(key=key)
        d.set(value, expiry)
        d.set_type('tpl')
        self.reservoir[key] = d
        self.add_to_replication_replay_logs('TPL', d)
        return True

    def delete_batch(self, batch):
        batch_data = []
        for element in batch:
            if not element.get("key", None):
                continue

            value = self.delete(element.get("key"))
            element_data = {"key":element.get("key"), "data":"200 OK"}
            batch_data.append(element_data)

        return batch_data

    # TODO: batch deletes - Done
    def delete(self, key):
        if self.reservoir.has_key(key):
            # dependants also include the key in question
            dependants = set(self.get_dependants_tree(key, self.max_depandants_depth))
            for dependant in dependants:
                if self.reservoir.has_key(dependant):
                    d = self.reservoir[dependant]
                    buckets = d.buckets
                    # unset the drop for garbage collection
                    del self.reservoir[dependant]
                    # delete the reference
                    self.reservoir.pop(dependant, None)
                    # delete the referece of bucket as well, if any
                    for bucket in buckets:
                        if not self.buckets.get(bucket, None):
                            continue
                        if dependant in self.buckets[bucket]:
                            self.buckets[bucket].remove(dependant)

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


    def ota_batch(self, protocol, batch):
        batch_data = []
        for element in batch:
            expiry = element.get('expiry')
            key = element.get('key')
            value = element.get('data')
            parent_key = element.get('data', None)
            
            if self.ota(key, value, expiry):
                batch_data.append({"key":key,"data": "200 OK"})
            else:
                batch_data.append({"key":key,"data": "500 ERROR"})
        return batch_data

    # TODO : add parent child relations like we did for self.set()
    # This can be used specifically for one time passwords, forgot/reset password links, read notifications etc
    def ota(self, key, value, expiry=0):
        print 'inside of ota function'
        d = Drop(key=key)
        d.set(value, expiry)
        d.set_type('ota') 
        self.reservoir[key] = d
        self.add_to_replication_replay_logs('OTA', d)
        return True

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

    def response(self, connection, response):
        self.socket.response(connection, response)
                
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
        print "inside the get_replication_replay_logs..."
        # this check is very necessary
        if not self.replication:
            return False

        data = []
        fetch_position = int(position) + 1
        result = True
        log_line = True

        print "initializing the fetch linecache loop... "
        while log_line and fetch_position < (int(position) + self.replication_max_replay_logs):
            print "getting replication replay log through linecache..."
            log_line = linecache.getline('replication/master/server.replay', fetch_position)
            print log_line
            if log_line:
                data.append(log_line)
                fetch_position += 1
            else:
                result = False
        return data

    # START OF REPLICATION TASKS FOR SLAVE SERVER
    def fetch_replication_replay_position(self):
        def blocks(file_object, chunk_size=65535):
            while True:
                b = file_object.read(chunk_size)
                if not b:
                    break
                yield b

        with open('replication/slave/server.replay', 'r') as file_handle:
            total_lines = sum(block.count("\n") for block in blocks(file_handle))

        return total_lines

    # TODO : need to have best way through threading like we did for persistance and garbage_collection - DONE
    def sync_replication_replay_logs_cycle(self):
        print "going to start the replication replay logs cycle"
        print self.replication_type, self.replication
        if not self.replication or self.replication_type != 'slave':
            return
    
        print "going for replication sync"
        # self.sync_replication_replay_logs()
        self.replication_thread = threading.Timer(self.replication_sync_interval, self.sync_replication_replay_logs).start()
        pass

    # TODO: find the best way to sync with file splits like MySQL does
    def sync_replication_replay_logs(self):
        print "inside the threaded replication child"
        if not self.replication:
            return
        print "creating replication client socket connection"
        replication_client = ReplicationClient(
            server_host=self.replication_master_server,
            server_port=self.port,
        )

        self.replication_replay_position = self.fetch_replication_replay_position()

        logs = replication_client.send("REPLICATION %d" % int(self.replication_replay_position))
        with open('replication/slave/server.replay', 'a') as file_handle:
            file_handle.write(logs)
        self.run_replication_replay_logs()
        self.sync_replication_replay_logs_cycle()
        return 

    # should be called from the sync function only and not directly
    def run_replication_replay_logs(self):
        print "inside the run replication replay logs"
        if not self.replication:
            return 

        data = []
        fetch_position = self.replication_replay_position
        result = True
        log_line = True

        print "initializing the fetch linecache loop... "
        while log_line and fetch_position < (int(self.replication_replay_position) + self.replication_max_replay_logs):
            print "getting replication replay log through linecache..."
            log_line = linecache.getline('replication/slave/server.replay', fetch_position)
            print log_line
            if log_line:
                data.append(log_line)
                fetch_position += 1
            else:
                result = False

        for data_line in data:
            self.process_replicated_client_request(data_line)
            pass

    def process_replicated_client_request(self, data):
        if data[:3] in ['SET', 'DEP']:
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            return_batch = self.set_batch(batch)

        if data[:3] == 'TPL':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            return_batch = self.tpl_batch(batch)

        if data[:3] == 'OTA':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            return_batch = self.ota_batch(batch)

        if data[:3] == 'DEL':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            return_batch = self.delete_batch(batch)

        if data[:3] == 'ICR':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            batch_data = []
            for element in batch:
                if not element.get("key", None):
                    continue
                if not self.reservoir.has_key(element.get("key")):
                    self.set(element.get("key"), 1, element.get("expiry"))
                else:
                    self.icr(element.get("key"))

        if data[:3] == 'DCR':
            data_parts = data.split(' ', 1)
            batch = json.loads(data_parts[1])
            batch_data = []
            for element in batch:
                if not element.get("key", None):
                    continue
                self.dcr(element.get("key"))

                    

    # END OF REPLICATION TASKS FOR SLAVE SERVER

