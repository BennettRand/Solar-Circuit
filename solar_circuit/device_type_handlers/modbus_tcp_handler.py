import logging
import time
import socket
import csv
import os
import os.path
from circuits import Component, Event

from solar_circuit.devices import tcp_devices

class ModbusTCPHandler(Component):
	MODBUS_PORT = 502
	MODBUS_TIMEOUT = 5
	TCP_LIST_PATH = os.path.join(os.getcwd(), r"solar_circuit\configuration\tcp_scan_list.txt")

	def __init__(self):
		super(ModbusTCPHandler, self).__init__()
		self.found_ips = set()
		self.ip_scan_list = set()
		self.devices = []
	
	def _load_tcp_list(self, fn):
		ip_set = set()
		logging.info("Loading tcp scan list from %s", fn)
		with open(fn, 'r') as f:
			for ip in f.readlines():
				ip_set.add(ip.rstrip("\n\r"))
		self.ip_scan_list |= ip_set
	
	def _get_ip_scan_list(self):
		return self.ip_scan_list - self.found_ips

	def started(self, *args):
		logging.info("ModbusTCPHandler started")
		self._load_tcp_list(self.TCP_LIST_PATH)

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
