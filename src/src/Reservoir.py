'''
This is the CLI file which will be command line based
'''

from ReservoirServer import Server
import sys
import os
import argparse
from ConfigParser import SafeConfigParser

# fetch all the arguments through argparser
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("server_or_client", help="start a server/client with default configurations")
    parser.add_argument("--verbose", help="increase the output verbosity", action="store_true")
    parser.add_argument("--skip-persistant-data", help="set this flag to false if you want skip the load of persistant data and start fresh persistance process ", action="store_true")
    args = parser.parse_args()
    pass
    
if __name__ == '__main__':
    config = SafeConfigParser()
    config.read([
        os.path.join(os.path.dirname(__file__), 'conf/default.conf'),
        # any other files to overwrite defaults here
    ])

    # any custom flags from CLI should be processed here
    parse_args()


# if server was asked to start
def start_server():
    s = Server(
        host=config.get('server', 'host'),
        port=config.getint('server', 'port'),
        max_clients=config.getint('server', 'max_clients'),
        read_buffer=config.getint('server', 'read_buffer'),
        max_memory_allocation=config.get('server', 'max_memory_allocation'),
        persistance=config.get('server', 'persistance'),
        persistance_interval=config.getint('server', 'persistance_interval'),
        garbage_collection_interval=config.getint('server', 'garbage_collection_interval'),
        max_depandants_depth=config.getint('server', 'max_depandants_depth'),
        replication=config.get('server', 'replication'),
        replication_slave_servers=config.get('server', 'replication_slave_servers'),
        replication_max_replay_logs=config.getint('server', 'replication_max_replay_logs'),
    )
    

# if client was asked to start
def start_client():
    c = Client(
        server_host=config.get('client', 'server_host'),
        server_port=config.getint('client', 'server_port'),
    )
