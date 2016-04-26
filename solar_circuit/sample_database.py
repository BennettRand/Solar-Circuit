import time
import logging
import os
import os.path
from circuits import Component, Event, Timer

from solar_circuit.libs.tinydb import TinyDB
from solar_circuit.libs.tinydb.storages import JSONStorage
from solar_circuit.libs.tinydb.middlewares import CachingMiddleware

class store_sample(Event):
	pass

class SampleDatabase(Component):
	DB_PATH = os.path.join(os.getcwd(), r"databases\samples.json")
	def __init__(self):
		super(SampleDatabase, self).__init__()
		self.database = None
		
	def started(self, *args):
		logging.info("Opening database %s", self.DB_PATH)
		self.database = TinyDB(self.DB_PATH)#, storage=CachingMiddleware(JSONStorage))
		
	def store_sample(self, dev_id, utctime, sample_dict):
		rows = []
		
		for k in sample_dict:
			rows.append({"utc": utctime, "channel": k, "value": sample_dict[k]})
			
		self.database.table(dev_id).insert_multiple(rows)
		