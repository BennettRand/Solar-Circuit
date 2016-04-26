import circuits
import logging

from . import device_manager
from . import sample_database

DEBUG = False

def main():
	logging.getLogger().setLevel(logging.INFO)
	base_components = device_manager.DeviceManager()
	base_components += sample_database.SampleDatabase()
	if DEBUG:
		base_components += circuits.Debugger()

	base_components.run()
	return

if __name__ == "__main__":
	main()
