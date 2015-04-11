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
        result = self.client.set("test_pk_movie", "awesome movie", 0)
        self.assertEqual(result, "200 OK")

    def test_get_cache_item(self):
        v = self.client.get("test_pk_movie")
        self.assertEqual(v, "awesome movie")

    def test_delete_cache_item(self):
        result = self.client.delete("test_pk_movie")
        self.assertEqual(result, "200 OK")

    def test_icr_cache_item(self):
        result = self.client.set("test_pk_votes", "100", 0)
        self.assertEqual(result, "200 OK")

        result = self.client.icr("test_pk_votes")
        self.assertEqual(result, "200 OK")

        result = self.client.get("test_pk_votes")
        self.assertEqual(result, "101")

    def test_dcr_cache_item(self):
        result = self.client.set("test_pk_votes", "500", 0)
        self.assertEqual(result, "200 OK")

        result = self.client.dcr("test_pk_votes")
        self.assertEqual(result, "200 OK")

        result = self.client.get("test_pk_votes")
        self.assertEqual(result, "499")

    def test_ota_cache_item(self):
        result = self.client.set("test_ota_pk_movie", "awesome movie with ota", 0)
        self.assertEqual(result, "200 OK")
        result = self.client.get("test_ota_pk_movie")
        self.assertEqual(result, "awesome movie with ota")
        # getting the value again should give you 500 ERROR
        result = self.client.get("test_ota_pk_movie")
        self.assertEqual(result, "500 ERROR")

    def test_tpl_cache_item(self):
        result = self.client.set("test_tpl_pk_movie", "awesome movie with tpl", 0)
        self.assertEqual(result, "200 OK")
        # setting the value again should give you 500 ERROR
        result = self.client.set("test_tpl_pk_movie", "awesome movie with tpl", 0)
        self.assertEqual(result, "500 ERROR")
        
    def get_configs(self):
        config = SafeConfigParser()
        config.read([
            os.path.join('../src/conf/default.conf'),
        ])
        return config


if __name__ == '__main__':
    unittest.main(verbosity=2)