import logging
import time
import socket
import struct
from circuits import Component, Event, Timer

from solar_circuit.libs.pyModbusTCP.client import ModbusClient
from . import sample, sample_success

def stringify_reg(regs):
	return "".join([struct.pack('!H', r) for r in regs])

class ModbusTCPDevice(Component):
	MODBUS_PORT = 502
	DEFAULT_INTERVAL = 10
	def __init__(self, ip):
		super(ModbusTCPDevice, self).__init__()
		self.sample_timer = None
		self.ip = ip
		self.uuid = self.ip
		self.conn = None

	def started(self, *args):
		self.conn = ModbusClient(host=self.ip, port=self.MODBUS_PORT,
								 auto_open=True, auto_close=True)
		self.fire(sample())
		self.sample_timer = Timer(self.DEFAULT_INTERVAL, sample(),
								  self, persist=True).register(self)
		return

	def sample_success(self, addr, regs):
		logging.info(addr)
		regs = stringify_reg(regs)
		logging.info(regs)

	def sample(self):
		logging.info("sampling from %s", self.uuid)
		to_sample = [(0, 6), (118, 20)]
		for t in to_sample:
			try:
				regs = self.conn.read_holding_registers(t[0], t[1])
			except Exception as e:
				logging.error(e)
			else:
				if regs is None:
					logging.warn("%s sent empty sample", self.uuid)
				else:
					self.fire(sample_success(t[0], regs), self)
		return
