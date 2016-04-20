import circuits

from . import device_manager

DEBUG = True

def main():
	base_components = device_manager.DeviceManager()
	if DEBUG:
		base_components += circuits.Debugger()

	base_components.run()
	return

if __name__ == "__main__":
	main()
