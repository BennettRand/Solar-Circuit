import logging
import time
import socket
from circuits import Component, Event

from solar_circuit.devices import tcp_devices

class ModbusTCPHandler(Component):
	MODBUS_PORT = 502
	MODBUS_TIMEOUT = 5

	def __init__(self):
		super(ModbusTCPHandler, self).__init__()
		self.found_ips = set()
		self.devices = []

	def _get_ip_scan_list(self):
		return {'128.193.47.4', '128.193.47.6', '128.193.47.46', '128.193.47.47'} - self.found_ips

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
				d = tcp_devices.ModbusTCPDevice(ip)
				d.started()
				d.register(self) # Be sure to register _after_ running
				self.devices.append(d)
				self.found_ips.add(ip)
