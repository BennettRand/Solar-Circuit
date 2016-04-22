import logging
import time
import socket
from circuits import Component, Event

class ModbusTCPHandler(Component):
	MODBUS_PORT = 502
	MODBUS_TIMEOUT = 5

	def __init__(self):
		super(ModbusTCPHandler, self).__init__()
		self.found_ips = set()

	def _get_ip_scan_list(self):
		return {'127.0.0.1', '0.0.0.0'} - self.found_ips

	def started(self, *args):
		logging.info("ModbusTCPHandler started")

	def discover(self):
		logging.info("Discovering ModbusTCP devices.")
		for ip in self._get_ip_scan_list():
			logging.info("Scanning %s", ip)
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(self.MODBUS_TIMEOUT)
			try:
				s.connect((ip, self.MODBUS_PORT))
			except socket.error as e:
				logging.info("No connection at %s port %s", ip, self.MODBUS_PORT)
			else:
				logging.info("%s has port %s open.", ip, self.MODBUS_PORT)
				s.close()
				self.found_ips.add(ip)
