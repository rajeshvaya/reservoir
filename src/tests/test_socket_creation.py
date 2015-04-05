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

class test_socket_creation(unittest.TestCase):

	def test_read_configs(self):
		config = self.get_configs()

		self.assertIsNotNone(config.get('server', 'host'))
		self.assertGreater(config.get("server", "port"), 1024) # valid port
		self.assertTrue(config.get("server", "protocol") in ['TCP', 'UDP'], 1024)

	def test_server_socket(self):
		config = self.get_configs()
		logger = logging.getLogger(__name__)
		s = ReservoirServer(
	        host=config.get('server', 'host'),
	        port=config.getint('server', 'port'),
	        protocol=config.get('server', 'protocol'),
	        logger=logger,
	        init_socket=False
        )
		self.assertEqual(s.host, config.get('server', 'host'))
		self.assertEqual(str(s.port), config.get('server', 'port'))
		self.assertIsNotNone(s.socket)
		self.assertEqual(s.socket.protocol, config.get('server', 'protocol'))
		self.assertIsInstance(s.socket, ReservoirSocket)

		self.assertIsInstance(s.reservoir, dict)

	def test_shell_socket(self):
		return
		config = self.get_configs()
		c = ReservoirClientShell(
		    server_host=config.get('client', 'server_host'),
		    server_port=config.getint('client', 'server_port'),
		    protocol=config.get('client', 'protocol'),
		)

	def test_console_socket(self):
		pass

	def get_configs(self):
		config = SafeConfigParser()
		config.read([
		    os.path.join('../src/conf/default.conf'),
		])
		return config


if __name__ == '__main__':
    unittest.main(verbosity=2)