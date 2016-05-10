import time
from datetime import datetime
import hashlib

_EPOCH = datetime.utcfromtimestamp(0)

def stringify_reg(regs):
	if regs is None:
		return ''
	return "0x" + "".join([hex(r)[2:] for r in regs])

def epoch_secs(dt):
	return float((dt - _EPOCH).total_seconds())

def ts_to_dt(ts):
	ts = ts.split('.')[0].rstrip("Z")
	return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")

def ts_hours_ago(ts, hours):
	now = time.mktime(time.gmtime())
	ago = now - (hours * 60.0 * 60.0)
	epoch = epoch_secs(ts_to_dt(ts))
	return ago < epoch

def pct_error(calculated, measured):
	return abs((measured - calculated) / calculated) * 100.0

def power_error(power, va, pf):
	power_c = va * pf
	pf_c = power / va

	error = pct_error(power_c, power)
	error += pct_error(pf_c, pf)

	return error / 2.0

def str_to_color(str_):
	m = hashlib.md5()
	m.update(str_.encode("utf8"))
	hexstr = m.hexdigest()[:6].upper()
	hexstr = [hex((int(x,16) + 0x8) // 2)[2:] for x in hexstr]
	return "#" + "".join(hexstr)


def minimize_addresses(registers):
	min_addrs = []
	min_sizes = []

	next_addr = None
	running_len = 0
	for a,s in registers:
	    if next_addr is None:
	        next_addr = a + s
	        running_len = s
	    else:
	        if a == next_addr:
	            next_addr += s
	            running_len += s
	        else:
	            min_addrs.append(next_addr - running_len)
	            min_sizes.append(running_len)
	            running_len = s
	            next_addr = a + s

	min_addrs.append(next_addr - running_len)
	min_sizes.append(running_len)

	return zip(min_addrs, min_sizes)
