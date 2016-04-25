import logging
import time
import socket
import struct
import codecs
from circuits import Component, Event, Timer, Worker, task
import random

from solar_circuit.libs.pyModbusTCP.client import ModbusClient
from solar_circuit.libs import prettytable
from solar_circuit.utility.helpers import *
from solar_circuit.utility import formats
from . import sample, sample_success

TCP_DEV_NAMES ={}

def register_device_type(cls):
	global TCP_DEV_NAMES
	TCP_DEV_NAMES[cls.__name__] = cls
	return cls

@register_device_type
class ModbusTCPDevice(Component):
	MODBUS_PORT = 502
	DEFAULT_INTERVAL = 60 * 15
	PREFIX = 'XXXX'
	def __init__(self, ip):
		super(ModbusTCPDevice, self).__init__()
		self.sample_timer = None
		self.ip = ip
		self.sn = ip
		self.registers = []
		self.conn = None
		self._set_channel()

	def _set_channel(self):
		self.channel = self.__class__.__name__ + str(id(self))

	def started(self, *args):
		self.conn = ModbusClient(host=self.ip, port=self.MODBUS_PORT,
								 auto_open=True, auto_close=True)
		self.fire(sample(), self)
		self.sample_timer = Timer(self.DEFAULT_INTERVAL + random.uniform(0,1), sample(),
								  self, persist=True).register(self)
		return

	def update_interval(self, interval, stray=1):
		if self.sample_timer is not None:
			self.sample_timer.reset(interval + random.uniform(0,stray))
			return True
		return False

	def sample_success(self, addr, regs):
		tab = prettytable.PrettyTable()
		# tab.field_names = [str(x) for x in xrange(0xf)]
		num_rows = (len(regs) / 0x10) + 1
		for x in xrange(0x10):
			column = [stringify_reg([_]) for _ in regs[x::0x10]]
			column += [''] * (num_rows - len(column))
			tab.add_column(str(x), column)
		logging.debug("Sample from %s address %s:\n%s", addr, self.sn, tab.get_string())

	def sample(self):
		logging.debug("%s Spawning sample task", self.sn)
		self.fire(task(self._sample), "sample_worker")

	def _sample(self):
		logging.info("Sampling from %s", self.sn)
		start = time.time()
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
		time_d = time.time() - start
		logging.debug("Sampling %s took %s", self.sn, time_d)
		return

@register_device_type
class Shark100(ModbusTCPDevice):
	PREFIX = 'SHRK'
	def __init__(self, ip):
		super(Shark100, self).__init__(ip)
		self.registers = [(0x0000, 47),
						  (0x0383, 6),
						  (0x03E7, 30)]
						  # (0x044B, 18),
						  # (0x07CF, 20),
						  # (0x0BB7, 34),
						  # (0x0C1B, 34),
						  # (0x1003, 6),
						  # (0x1387, 4)]

	def started(self, *args):
		super(Shark100, self).started(args)
		self.update_interval(30)

	def sample_success(self, addr, regs):
		if addr == 0x0000:
			# logging.info("Name: %s", formats.modbus_string(regs[0:8]))
			self.sn = formats.modbus_string(regs[8:16]).strip(" ")
			# logging.info("Type: %s", formats.bitfield(regs[16:17]))
			# logging.info("Firmware: %s", formats.modbus_string(regs[17:19]))
			# logging.info("Map Version: %s", formats.uint16(regs[19:20]))
			# logging.info("Meter Configuration: %s", formats.bitfield(regs[20:21]))
			# logging.info("ASIC Version: %s", formats.uint16(regs[21:22]))
		elif addr == 0x0383:
			logging.info(self.sn.center(60, '-'))
			logging.info("Power: %s", formats.float32(regs[0:2]))
			logging.info("VAR: %s", formats.float32(regs[2:4]))
			logging.info("VA: %s", formats.float32(regs[4:6]))
		elif addr == 0x03E7:
			logging.info(self.sn.center(60, '-'))
			logging.info("Power Factor: %s", formats.float32(regs[24:26]))
			logging.info("Frequency: %s", formats.float32(regs[26:28]))
