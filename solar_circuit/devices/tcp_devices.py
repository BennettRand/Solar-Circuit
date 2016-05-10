import logging
import time
import random
import datetime
import csv
import base64
from circuits import Component, Timer, task

from solar_circuit.libs.pyModbusTCP.client import ModbusClient
from solar_circuit.libs import prettytable
from solar_circuit.utility.helpers import stringify_reg, power_error, minimize_addresses, make_rtu_pair
from solar_circuit.utility import formats
from solar_circuit.sample_database import store_sample
from . import sample, sample_success

TCP_DEV_NAMES = {}

STORE_COMMAND = 0b10
STORE_RT = 0b01

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
		self.queued_time = time.time()
		self.time_d = 0
		self.sample_pending = False

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
			self.sample_timer.reset(interval + random.uniform(0, stray))
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
		if self.sample_pending:
			logging.warn("%s already has a sample pending.", self.get_dev_id())
		else:
			logging.debug("%s Spawning sample task", self.sn)
			self.queued_time = time.time()
			self.sample_pending = True
			self.fire(task(self._sample), "sample_worker")

	def _sample(self):
		logging.debug("Sampling from %s", self.sn)
		for t in self.registers:
			try:
				regs = self.conn.read_holding_registers(t[0], t[1])
			except Exception as e:
				logging.error(e)
			else:
				if regs is None:
					logging.warn("%s sent empty sample", self.get_dev_id())
				else:
					self.fire(sample_success(t[0], regs), self)
		self.time_d = time.time() - self.queued_time
		logging.debug("Sampling %s took %s", self.get_dev_id(), self.time_d)
		self.sample_pending = False
		if self.time_d > self.sample_timer.interval:
			logging.warn("Sampling %s took %s! (> %s)", self.get_dev_id(),
						 self.time_d, self.sample_timer.interval)
		return

	def get_dev_id(self):
		return "{}-{}".format(self.PREFIX, self.sn)

class ModbusTCPCSVMapDevice(ModbusTCPDevice):
	def __init__(self, ip):
		super(ModbusTCPCSVMapDevice, self).__init__(ip)
		self.map = {}
		self.order = 1
		self.latest_sample = {}
		self.latest_sample_time = None
	def _load_csv_map(self, fname):
		with open(fname, 'r') as f:
			reader = csv.DictReader(f)
			for row in reader:
				if row['address'].startswith('0x'):
					base = 16
				else:
					base = 10
				address = int(row['address'], base)
				registers = int(row['registers'])
				reg_format = getattr(formats, row['format'], lambda x, o: x[::o])
				self.map[address] = {'address': address,
									 'registers': registers,
									 'format': reg_format,
									 'name': row['name'],
									 'store': int(row['store'])}
				self.registers.append((address, registers))
		self.registers = minimize_addresses(self.registers)
		logging.debug("%s will sample: %s", self.get_dev_id(), self.registers)

	def sample_success(self, addr, regs):
		try:
			self.latest_sample.update({a: r for a, r in zip(xrange(addr, addr + len(regs)), regs)})
			self.latest_sample_time = datetime.datetime.utcnow()
			rtu_pair = make_rtu_pair(1, addr, regs)
			parsed = {}
			rt = {}
			keep_pair = False

			for a in self.latest_sample:
				if a in self.map:
					relevent = [self.latest_sample[_] for _ in xrange(a, a + self.map[a]['registers'])]
					parsed[self.map[a]['name']] = self.map[a]['format'](tuple(relevent), self.order)

					keep_pair |= bool(self.map[a]['store'] & STORE_COMMAND)

					if self.map[a]['store'] & STORE_RT:
						rt[self.map[a]['name']] = parsed[self.map[a]['name']]

			self.latest_sample.update(parsed)

			if rt:
				self.fire(store_sample(self.get_dev_id(), self.latest_sample_time, rt))

		except Exception as e:
			logging.exception("Parsing failure: %s", e)



@register_device_type
class Shark100(ModbusTCPCSVMapDevice):
	PREFIX = 'SHRK'
	ERROR_LIMIT = 1.0
	def __init__(self, ip):
		super(Shark100, self).__init__(ip)
		self._load_csv_map(r".\solar_circuit\configuration\shark100_modbus_registers.csv")

	def started(self, *args):
		super(Shark100, self).started(args)
		self.update_interval(10)

	def sample_success(self, addr, regs):
		super(Shark100, self).sample_success(addr, regs)
		self.sn = self.latest_sample['SerialNumber']

@register_device_type
class SEL735(ModbusTCPDevice):
	PREFIX = 'SEL'
	ERROR_LIMIT = 1.0
	def __init__(self, ip):
		super(SEL735, self).__init__(ip)
		self.registers = [(0x0014, 20),
						  (0x015E, 32),
						  (0x0384, 26),
						  (0x0258, 58)]

	def started(self, *args):
		super(SEL735, self).started(args)
		self.update_interval(60)

	def sample_success(self, addr, regs):
		sample = {}
		timestamp = datetime.datetime.utcnow()
		if addr == 0x0014:
			self.sn = formats.modbus_string(regs).strip(" ").strip("\x00")
		elif addr == 0x015E:
			sample["AmpsA"] = float(formats.int32(regs[0:2])) / 100.0
			sample["AmpsB"] = float(formats.int32(regs[2:4])) / 100.0
			sample["AmpsC"] = float(formats.int32(regs[4:6])) / 100.0
			sample["AmpsN"] = float(formats.int32(regs[6:8])) / 100.0
			sample["VoltsA"] = float(formats.int32(regs[8:10])) / 100.0
			sample["VoltsB"] = float(formats.int32(regs[10:12])) / 100.0
			sample["VoltsC"] = float(formats.int32(regs[12:14])) / 100.0
			sample["VoltsAB"] = float(formats.int32(regs[14:16])) / 100.0
			sample["VoltsBC"] = float(formats.int32(regs[16:18])) / 100.0
			sample["VoltsCA"] = float(formats.int32(regs[18:20])) / 100.0
			sample["Power"] = float(formats.int32(regs[20:22])) / 100.0
			sample["VA"] = float(formats.int32(regs[22:24])) / 100.0
			sample["VAR"] = float(formats.int32(regs[24:26])) / 100.0
			sample["PowerA"] = float(formats.int32(regs[26:28])) / 100.0
			sample["PowerB"] = float(formats.int32(regs[28:30])) / 100.0
			sample["PowerC"] = float(formats.int32(regs[30:32])) / 100.0
		elif addr == 0x0258:
			sample["TotalImport"] = formats.int32(regs[0:2])

		self.fire(store_sample(self.get_dev_id(), timestamp, sample))
