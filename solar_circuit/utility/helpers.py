import time
from datetime import datetime

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
	ago = now - (hours * 60 * 60)
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