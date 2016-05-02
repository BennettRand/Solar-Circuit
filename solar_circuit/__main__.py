import circuits
import logging

from . import device_manager
from . import sample_database
from . import graph_web_ui

DEBUG = False

def main():
	logging.getLogger().setLevel(logging.INFO)
	base_components = device_manager.DeviceManager()
	base_components += sample_database.SampleDatabase()
	base_components += graph_web_ui.WebUIServer
	if DEBUG:
		base_components += circuits.Debugger()

	base_components.run()
	return

if __name__ == "__main__":
	main()
