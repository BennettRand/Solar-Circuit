def stringify_reg(regs):
	if regs is None:
		return ''
	return "0x" + "".join([hex(r)[2:] for r in regs])