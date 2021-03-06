'''
This is the CLI file which will be command line based
'''

from ReservoirServer import Server
from ReservoirClientServer import Client
from ReservoirClientShell import Client as ClientShell
from ReservoirConsole import ReservoirConsole
import sys
import os
import argparse
import logging
from ConfigParser import SafeConfigParser

# fetch all the arguments through argparser
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("parent", help="start a server/client with default configurations")
    parser.add_argument("--verbose", help="increase the output verbosity", action="store_true")
    parser.add_argument("--skip-persistant-data", help="set this flag to false if you want skip the load of persistant data and start fresh persistance process ", action="store_true")
    args = parser.parse_args()
    return args
    
# if server was asked to start
def start_server():
    logger = logging.getLogger(__name__)
    logger_level = config.get('server', 'logger_level').upper()
    if logger_level == 'INFO':
        logger_level = logging.INFO
    if logger_level == 'DEBUG':
        logger_level = logging.DEBUG
    if logger_level == 'ERROR':
        logger_level = logging.ERROR

    logger.setLevel(logger_level)
    
    # set the console handle
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # set the log file handle
    handler = logging.FileHandler('logs/server.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("Starting reservoir server...")

    s = Server(
        host=config.get('server', 'host'),
        port=config.getint('server', 'port'),
        logger=logger,
        max_clients=config.getint('server', 'max_clients'),
        read_buffer=config.getint('server', 'read_buffer'),
        protocol=config.get('server', 'protocol'),
        max_memory_allocation=config.get('server', 'max_memory_allocation'),
        persistance=config.get('server', 'persistance'),
        persistance_interval=config.getint('server', 'persistance_interval'),
        garbage_collection_interval=config.getint('server', 'garbage_collection_interval'),
        max_depandants_depth=config.getint('server', 'max_depandants_depth'),
        replication=config.get('server', 'replication'),
        replication_type=config.get('server', 'replication_type'),
        replication_master_server=config.get('server', 'replication_master_server'),
        replication_slave_servers=config.get('server', 'replication_slave_servers'),
        replication_max_replay_logs=config.getint('server', 'replication_max_replay_logs'),
        replication_sync_interval=config.getint('server', 'replication_sync_interval'),
        default_data_format=config.get('server', 'default_data_format'),
    )

    logger.info("Started reservoir server")
    
# if client was asked to start
def start_client():
    c = Client(
        server_host=config.get('client', 'server_host'),
        server_port=config.getint('client', 'server_port'),
        protocol=config.get('client', 'protocol'),
    )


# if shell access was requested
def start_shell():
    c = ClientShell(
        server_host=config.get('client', 'server_host'),
        server_port=config.getint('client', 'server_port'),
        protocol=config.get('client', 'protocol'),
    )

def start_console():
    console = ReservoirConsole(
        server_host=config.get('client', 'server_host'),
        server_port=config.getint('client', 'server_port'),
        protocol=config.get('client', 'protocol'),
    )
    console . cmdloop() 
    

if __name__ == '__main__':
    config = SafeConfigParser()
    config.read([
        os.path.join(os.path.dirname(__file__), 'conf/default.conf'),
        # any other files to overwrite defaults here
    ])

    # any custom flags from CLI should be processed here
    args = parse_args()
    if args.parent == 'server':
        start_server()
    if args.parent == 'client':
        start_client()
    if args.parent == 'shell':
        start_shell()
    if args.parent == 'console':
        start_console()


