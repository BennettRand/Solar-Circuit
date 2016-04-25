import struct

def modbus_string(registers, order=1):
	ret = ""
	for r in registers[::order]:
		ret += struct.pack("!H", r)
	return ret
	
def bitfield(registers, order=1):
	data_str = modbus_string(registers, order)
	ret = "".join([bin(ord(c))[2:].rjust(8, '0') for c in data_str])
	return map(lambda x: x == '1', ret)
	
def uint8(registers, order=1):
	if len(registers) != 1:
		raise ValueError("Incorrect number of registers.")
	data_str = modbus_string(registers, order)
	return struct.unpack("!xB", data_str)[0]
	
def int8(registers, order=1):
	if len(registers) != 1:
		raise ValueError("Incorrect number of registers.")
	data_str = modbus_string(registers, order)
	return struct.unpack("!xb", data_str)[0]
	
def uint16(registers, order=1):
	if len(registers) != 1:
		raise ValueError("Incorrect number of registers.")
	data_str = modbus_string(registers, order)
	return struct.unpack("!H", data_str)[0]
	
def int16(registers, order=1):
	if len(registers) != 1:
		raise ValueError("Incorrect number of registers.")
	data_str = modbus_string(registers, order)
	return struct.unpack("!h", data_str)[0]
	
def uint32(registers, order=1):
	if len(registers) != 2:
		raise ValueError("Incorrect number of registers.")
	data_str = modbus_string(registers, order)
	return struct.unpack("!I", data_str)[0]
	
def int32(registers, order=1):
	if len(registers) != 2:
		raise ValueError("Incorrect number of registers.")
	data_str = modbus_string(registers, order)
	return struct.unpack("!i", data_str)[0]
	
def uint64(registers, order=1):
	if len(registers) != 4:
		raise ValueError("Incorrect number of registers.")
	data_str = modbus_string(registers, order)
	return struct.unpack("!Q", data_str)[0]
	
def int64(registers, order=1):
	if len(registers) != 4:
		raise ValueError("Incorrect number of registers.")
	data_str = modbus_string(registers, order)
	return struct.unpack("!q", data_str)[0]
	
def float32(registers, order=1):
	if len(registers) != 2:
		raise ValueError("Incorrect number of registers.")
	data_str = modbus_string(registers, order)
	return struct.unpack("!f", data_str)[0]
	
def float64(registers, order=1):
	if len(registers) != 4:
		raise ValueError("Incorrect number of registers.")
	data_str = modbus_string(registers, order)
	return struct.unpack("!d", data_str)[0]