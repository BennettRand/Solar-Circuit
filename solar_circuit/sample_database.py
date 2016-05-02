import time
import logging
import os
import os.path
from circuits import Component, Event, Timer

from solar_circuit.libs.tinydb import TinyDB, Query
from solar_circuit.libs.tinydb.storages import CompressedJSONStorage
from solar_circuit.libs.tinydb.middlewares import CachingMiddleware
from solar_circuit.utility.helpers import *

DATABASE = None

class store_sample(Event):
	pass
	
class clear_old(Event):
	pass
	
def get_database():
	global DATABASE
	return DATABASE

class SampleDatabase(Component):
	DB_PATH = os.path.join(os.getcwd(), r"databases\samples.json.bz2")
	def __init__(self):
		global DATABASE
		super(SampleDatabase, self).__init__()
		DATABASE = None
		CachingMiddleware.WRITE_CACHE_SIZE = 250
		self.clear_timer = None

	def started(self, *args):
		global DATABASE
		logging.info("Opening database %s", self.DB_PATH)
		DATABASE = TinyDB(self.DB_PATH, storage=CachingMiddleware(CompressedJSONStorage))
		self.clear_timer = Timer(60, clear_old(), self, persist=True).register(self)

	def store_sample(self, dev_id, utctime, sample_dict):
		rows = []

		for k in sample_dict:
			rows.append({"utc": utctime, "channel": k, "value": sample_dict[k]})

		DATABASE.table(dev_id).insert_multiple(rows)
		
	def clear_old(self, hours=24):
		if DATABASE is None:
			return False
			
		eids = []
		
		for t in DATABASE.tables():
			Sample = Query()
			eids += DATABASE.table(t).remove(Sample.utc.test(lambda x, h: not ts_hours_ago(x, h), hours))
		
		logging.info("Removed %s samples that were at least %s hours old", len(eids), hours)
		return len(eids)
