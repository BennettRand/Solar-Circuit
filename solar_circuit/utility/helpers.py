import time
from datetime import datetime
import hashlib
import formats

_EPOCH = datetime.utcfromtimestamp(0)

def stringify_reg(regs):
	if regs is None:
		return ''
	ret = "".join([hex(r)[2:].rjust(4, '0') for r in regs])
	return "0x" + ret

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
	hexstr = [hex((int(x, 16) + 0x8) // 2)[2:] for x in hexstr]
	return "#" + "".join(hexstr)


def minimize_addresses(registers):
	min_addrs = []
	min_sizes = []

	next_addr = None
	running_len = 0
	for a, s in registers:
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

CRC16_TABLE = None

def init_table():
	global CRC16_TABLE

	if CRC16_TABLE is not None:
		return

	lst = []
	i = 0
	while i < 256:
		data = (i << 1)
		crc = 0
		j = 8
		while j > 0:
			data >>= 1
			if (data ^ crc) & 0x0001:
				crc = (crc >> 1) ^ 0xA001
			else:
				crc >>= 1
			j -= 1

		lst.append(crc)
		i += 1

	CRC16_TABLE = tuple(lst)
	return

def calcByte(ch, crc):
	"""Given a Byte, Calc a modbus style CRC-16 by look-up table"""
	init_table()
	if isinstance(ch, str):
		by = ord(ch)
	else:
		by = ch
	crc = (crc >> 8) ^ CRC16_TABLE[(crc ^ by) & 0xFF]
	return crc & 0xFFFF

def calcString(st, crc):
	"""Given a string, Calc a modbus style CRC-16 by look-up table"""
	init_table()
	for ch in st:
		crc = (crc >> 8) ^ CRC16_TABLE[(crc ^ ord(ch)) & 0xFF]
	return crc

def make_rtu_pair(dev, addr, regs):
	query_frame = ((dev << 8) + 0x03, addr, len(regs))
	q_crc = calcString(formats.modbus_string(query_frame), 0)
	response_frame = (dev, (0x03 << 8) + len(regs) * 2) + tuple(regs)
	r_crc = calcString(formats.modbus_string(response_frame), 0)
	query = query_frame + (q_crc,)
	response = response_frame + (r_crc,)

	return query, response
