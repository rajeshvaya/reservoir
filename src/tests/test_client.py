import sys
import os
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(here, '../src/')))

import unittest
from ConfigParser import SafeConfigParser
import logging

from ReservoirServer import Server as ReservoirServer
from ReservoirSocket import ReservoirSocket
from ReservoirConsole import ReservoirConsole
from ReservoirClientShell import Client as ReservoirClientShell
from ReservoirClientServer import Client

class test_socket_creation(unittest.TestCase):

    def setUp(self):
        config = self.get_configs()
        logger = logging.getLogger(__name__)
        self.server = ReservoirServer(
            host=config.get('server', 'host'),
            port=config.getint('server', 'port'),
            protocol=config.get('server', 'protocol'),
            logger=logger,
            init_socket=False
        )

        c = Client(
            server_host=config.get('client', 'server_host'),
            server_port=config.getint('client', 'server_port'),
            protocol=config.get('client', 'protocol'),
        )

    def test_set_cache_item(self):
        result = self.client.set("pk_movie", "awesome movie", 0)
        self.assertEqual(result, "200 OK")

    def test_get_cache_item(self):
        v = self.client.get("pk_movie")
        self.assertEqual(v, "awesome movie")

    def test_delete_cache_item(self):
        result = self.client.delete("pk_movie")
        self.assertEqual(result, "200 OK")
        
    def get_configs(self):
        config = SafeConfigParser()
        config.read([
            os.path.join('../src/conf/default.conf'),
        ])
        return config


if __name__ == '__main__':
    unittest.main(verbosity=2)