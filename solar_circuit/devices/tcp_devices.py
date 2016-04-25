import logging
import time
import socket
import struct
import codecs
from circuits import Component, Event, Timer
import random

from solar_circuit.libs.pyModbusTCP.client import ModbusClient
from solar_circuit.libs import prettytable
from . import sample, sample_success

TCP_DEV_NAMES ={}

def stringify_reg(regs):
	return "0x" + "".join([hex(r)[2:] for r in regs])

def register_device_type(cls):
	global TCP_DEV_NAMES
	TCP_DEV_NAMES[cls.__name__] = cls
	return cls

@register_device_type
class ModbusTCPDevice(Component):
	MODBUS_PORT = 502
	DEFAULT_INTERVAL = 60
	def __init__(self, ip):
		super(ModbusTCPDevice, self).__init__()
		self.sample_timer = None
		self.ip = ip
		self.sn = ip
		self.channel = id(self)
		self.registers = []
		self.conn = None
		
	def started(self, *args):
		self.conn = ModbusClient(host=self.ip, port=self.MODBUS_PORT,
								 auto_open=True, auto_close=True)
		self.fire(sample(), self)
		self.sample_timer = Timer(self.DEFAULT_INTERVAL + random.uniform(0,1), sample(),
								  self, persist=True).register(self)
		return
	
	def update_interval(self, interval):
		if self.sample_timer is not None:
			self.sample_timer.reset(interval + random.uniform(0,1))
			return True
		return False
	
	def sample_success(self, addr, regs):
		tab = prettytable.PrettyTable()
		# tab.field_names = [str(x) for x in xrange(0xf)]
		num_rows = (len(regs) / 0xf) + 1
		for x in xrange(0xf):
			column = [stringify_reg([_]) for _ in regs[x::0xf]]
			column += [''] * (num_rows - len(column))
			tab.add_column(str(x), column)
		logging.info("Sample from %s address %s:\n%s", addr, self.sn, tab.get_string())

	def sample(self):
		logging.info("sampling from %s", self.sn)
		for t in self.registers:
			try:
				regs = self.conn.read_holding_registers(t[0], t[1])
			except Exception as e:
				logging.error(e)
			else:
				if regs is None:
					logging.warn("%s sent empty sample", self.sn)
				else:
					self.fire(sample_success(t[0], regs), self)
		return
