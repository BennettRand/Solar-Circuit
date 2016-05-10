import logging
import socket
import csv
import os
import os.path
from circuits import Component, task

from solar_circuit.devices import tcp_devices
from solar_circuit.libs.pyModbusTCP.client import ModbusClient
from solar_circuit.utility.helpers import stringify_reg

class ModbusTCPHandler(Component):
	MODBUS_PORT = 502
	MODBUS_TIMEOUT = 5
	TCP_LIST_PATH = os.path.join(os.getcwd(), r"solar_circuit\configuration\tcp_scan_list.txt")
	TCP_DISCOVERY_PATH = os.path.join(os.getcwd(), r"solar_circuit\configuration\tcp_discovery_rules.csv")

	def __init__(self):
		super(ModbusTCPHandler, self).__init__()
		self.found_ips = set()
		self.ip_scan_list = set()
		self.devices = []

	def _load_tcp_list(self, fn):
		ip_set = set()
		logging.debug("Loading tcp scan list from %s", fn)
		with open(fn, 'r') as f:
			for ip in f.readlines():
				if not ip.startswith("#"):
					ip_set.add(ip.rstrip("\n\r"))
		self.ip_scan_list |= ip_set

	def _get_ip_scan_list(self):
		return self.ip_scan_list - self.found_ips

	def _load_discovery_rules(self):
		with open(self.TCP_DISCOVERY_PATH, 'r') as f:
			d = csv.DictReader(f)
			ret = [r for r in d]
			return ret

	def started(self, *args):
		logging.info("ModbusTCPHandler started")
		self._load_tcp_list(self.TCP_LIST_PATH)

	def discover(self):
		logging.info("Discovering ModbusTCP devices.")
		for ip in self._get_ip_scan_list():
			self.fire(task(self._discover, ip), "discovery_worker")

	def _discover(self, ip):
		logging.info("Discovering %s", ip)
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(self.MODBUS_TIMEOUT)
		try:
			s.connect((ip, self.MODBUS_PORT))
		except socket.error as e:
			logging.warn("No connection at %s port %s", ip, self.MODBUS_PORT)
		else:
			logging.info("%s has port %s open.", ip, self.MODBUS_PORT)
			s.close()
			mbc = ModbusClient(host=ip, port=self.MODBUS_PORT,
							   auto_open=True, auto_close=True)
			for rule in self._load_discovery_rules():
				logging.debug("Trying %s on %s", rule['dev_name'], ip)
				regs = mbc.read_holding_registers(int(rule['addr']), int(rule['size']))
				logging.debug("Is %s in %s", rule['expected'], stringify_reg(regs))
				if rule['expected'].upper() in stringify_reg(regs).upper():
					logging.info("%s is of type %s", ip, rule['dev_name'])
					try:
						d = tcp_devices.TCP_DEV_NAMES[rule['dev_name']](ip)
						d.started()
						d.register(self) # Be sure to register _after_ running
						self.devices.append(d)
					except Exception as e:
						logging.exception("Error during device creation: %s", e)
			self.found_ips.add(ip)
