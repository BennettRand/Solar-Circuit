import logging
import time
from circuits import Component, Event, Timer, Worker, task

from .device_type_handlers.modbus_tcp_handler import ModbusTCPHandler

class discover(Event):
	'''Discovery loop event'''

class DeviceManager(Component):
	DISCOVERY_INTERVAL = 60*10
	def __init__(self):
		super(DeviceManager, self).__init__()

		self.modbus_tcp_handler = ModbusTCPHandler().register(self)
		self.active = False
		self.discovery_timer = None
		self.sample_worker = None
		self.discovery_worker = None

	def discover(self):
		logging.info("Discovery tick")
		return

	def started(self, *args):
		logging.info("Initializing DeviceManager")
		logging.info("Initializing discovery")
		self.active = True
		self.sample_worker = Worker(channel="sample_worker").register(self)
		self.discovery_worker = Worker(workers=1, channel="discovery_worker").register(self)
		self.discovery_timer = Timer(self.DISCOVERY_INTERVAL, discover(),
									 persist=True).register(self)
		self.fire(discover())
		return
