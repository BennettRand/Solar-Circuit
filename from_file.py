import time
import sys
import socket
import struct
import time
from matplotlib import pyplot
from datetime import datetime

from solar_circuit.libs.pyhighcharts import Chart, ChartTypes
from solar_circuit.libs.tinydb import TinyDB
from solar_circuit.libs.tinydb.storages import CompressedJSONStorage
from solar_circuit.libs.tinydb.middlewares import CachingMiddleware
from solar_circuit.libs.tinydb import Query

_EPOCH = datetime.utcfromtimestamp(0)

def epoch_secs(dt):
	return float((dt - _EPOCH).total_seconds())

def ts_to_dt(ts):
	ts = ts.split('.')[0].rstrip("Z")
	return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")

def ts_hours_ago(ts, hours):
	now = time.mktime(time.gmtime())
	ago = now - (hours * 60 * 60)
	epoch = epoch_secs(ts_to_dt(ts))
	return ago < epoch

def main():
	db = TinyDB("./databases/samples.json.bz2",
				storage=CachingMiddleware(CompressedJSONStorage))
	chart = Chart(title={'text':"Power Measurements"},
				  yAxis={'title': {'text': 'Power (Watts)'}},
				  xAxis={'type': 'datetime'})
	for t in [t for t in db.tables() if t != "_default"]:
		Sample = Query()
		power_samples = db.table(t).search(Sample.utc.test(ts_hours_ago, 24) &\
										   (Sample.channel == "Power"))
		series = []
		power_samples.sort(key=lambda x: ts_to_dt(x['utc']))
		for p in power_samples:
			ts = ts_to_dt(p['utc'])
			if p['value'] < 0:
				print ts, p['value'], p['channel']
			else:
				series.append((ts, p['value']))

		chart.add_data_series(ChartTypes.line, series, name=t, visible=False,
							  marker={'enabled': False})
	db.close()
	chart.show()

	return

if __name__ == "__main__":
	main()
