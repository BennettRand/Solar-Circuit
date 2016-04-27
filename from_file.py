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
from solar_circuit.libs.tinydb import Query

_EPOCH = datetime.utcfromtimestamp(0)

def epoch_secs(dt):
    return float((dt - _EPOCH).total_seconds())

def main():
    db = TinyDB("./databases/samples.json.bz2", storage=CompressedJSONStorage)
    for t in db.tables():
        power_samples = db.table(t).search(Query().channel == "PowerFactor")
        series = ([], [])
        for p in power_samples:
            ts = p['utc'].split('.')[0].rstrip("Z")
            ts = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
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
