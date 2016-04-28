import time
import sys
import socket
import struct
import time
from matplotlib import pyplot
from datetime import datetime

# sys.path.append(r'C:\Users\brand\Measurements')

# from measurements import timeseries
# from measurements import energy
# from measurements import si
# from measurements import util
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
	for t in db.tables():
		Sample = Query()
		power_samples = db.table(t).search(Sample.utc.test(ts_hours_ago, 24) &\
										   (Sample.channel == "Power"))
		series = ([], [])
		for p in power_samples:
			ts = ts_to_dt(p['utc'])
			if p['value'] < 0:
				print ts, p['value'], p['channel']
			series[0].append(ts)
			series[1].append(p['value'])

		pyplot.plot(*series)
	db.close()
	pyplot.legend(db.tables())
	pyplot.show()
	# f_str = open(sys.argv[1], 'rb').read()

	# ts = timeseries.Timeseries.decompress(f_str)

	# util.plot_timeseries_with_pyplot(ts)
	# for x in xrange(0xffff):
	# 	if x % 0x100 == 0:
	# 		print "\n[{}]".format(hex(x))
	# 	rs.sendall(read_registers(x, 1))
	# 	resp = rs.recv(11)
	# 	try:
	# 		resp = struct.unpack("!HHHBBBH", resp)[-1]
	# 	except struct.error:
	# 		pass
	# 	else:
	# 		if 32 <= resp <= 127:
	# 			print chr(resp),
	# 		else:
	# 			print hex(resp),
	# 	time.sleep(.01)

	return

if __name__ == "__main__":
	main()
