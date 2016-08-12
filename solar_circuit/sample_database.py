import time
import logging
import os
import os.path
import sqlite3
from circuits import Component, Event, Timer

from solar_circuit.libs.tinydb import TinyDB, Query
from solar_circuit.libs.tinydb.storages import CompressedJSONStorage
from solar_circuit.libs.tinydb.middlewares import CachingMiddleware
from solar_circuit.utility.helpers import *

DATABASE = None

class store_sample(Event):
	pass

class store_cr_pair(Event):
	pass

class clear_old(Event):
	pass

def get_database():
	global DATABASE
	return DATABASE

DB_SCHEMA = """CREATE TABLE IF NOT EXISTS samples
(sid INTEGER PRIMARY KEY ASC,
dev_id TEXT,
utc TIMESTAMP,
channel TEXT,
value REAL)"""

CR_DB_SCHEMA = """CREATE TABLE IF NOT EXISTS commandresponse
(crid INTEGER PRIMARY KEY ASC,
dev_id TEXT,
utc TIMESTAMP,
command TEXT,
response TEXT)"""

INSERT_TEMPLATE = """INSERT INTO samples
(dev_id, utc, channel, value)
VALUES (?, ?, ?, ?)"""

CR_INSERT_TEMPLATE = """INSERT INTO commandresponse
(dev_id, utc, command, response)
VALUES (?, ?, ?, ?)"""

DELETE_TEMPLATE = """DELETE FROM samples
WHERE utc < datetime('now', '-{} hours')"""

class SampleDatabase(Component):
	DB_PATH = os.path.join(os.getcwd(), r"databases/samples.db")
	def __init__(self):
		global DATABASE
		super(SampleDatabase, self).__init__()
		DATABASE = None
		CachingMiddleware.WRITE_CACHE_SIZE = 250
		self.clear_timer = None

	def started(self, *args):
		global DATABASE
		logging.info("Opening database %s", self.DB_PATH)
		DATABASE = sqlite3.connect(self.DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
		DATABASE.cursor().execute(DB_SCHEMA)
		DATABASE.cursor().execute(CR_DB_SCHEMA)
		DATABASE.commit()
		self.clear_timer = Timer(60, clear_old(), self, persist=True).register(self)

	def store_sample(self, dev_id, utctime, sample_dict):
		try:
			rows = []

			for k in sample_dict:
				rows.append((dev_id, utctime, k, sample_dict[k]))

			DATABASE.cursor().executemany(INSERT_TEMPLATE, rows)
			DATABASE.commit()
		except Exception as e:
			logging.exception("RT Sample Store Error: %s, %s", e, sample_dict)

	def store_cr_pair(self, dev_id, utctime, command, response):
		try:
			DATABASE.cursor().execute(CR_INSERT_TEMPLATE,
									  (dev_id, utctime, command, response))
			DATABASE.commit()
		except Exception as e:
			logging.exception("Command Response Store Error: %s, %s", e, dev_id)

	def clear_old(self, hours=24):
		if DATABASE is None:
			return False

		try:
			curr = DATABASE.cursor()
			curr.execute(DELETE_TEMPLATE.format(hours))
			DATABASE.commit()
		except Exception as e:
			logging.exception(e)

		logging.info("Removed %s samples that were at least %s hours old",
					 curr.rowcount, hours)
		return
