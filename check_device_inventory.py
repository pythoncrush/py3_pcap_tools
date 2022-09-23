import subprocess
import re
import os
from enable_diag_mode import *
import pandas as pd
import openpyxl

def find_devices_on_adb():
    device_ids = [line.decode('utf-8') for line in subprocess.check_output(['adb', 'devices']).split() if len(line) >=10]
    return device_ids  

def get_wifi_hw_address_from_adb(device_id):
	command = 'adb ' + '-s ' + device_id + ' shell ' + 'ip ' + 'address ' + 'show ' + 'wlan0'
	wifi_mac_address = subprocess.check_output(command).decode('utf-8')
	found_mac = re.search(r'(link\/ether)\s+(.+)',wifi_mac_address)
	found_mac = found_mac.group(2) 
	return found_mac[:17]

#needs root permission on device to work
def get_blutooth_address_from_adb():
	device_list = find_devices_on_adb()
	bt_mac_list = []
	for device in device_list:
		command = 'adb ' + '-s ' + device + ' shell ' + 'get ' + 'secure ' + 'bluetooth_address'
		bt_mac_address = subprocess.check_output(command).decode('utf-8')
	return bt_mac_address


if __name__ == "__main__":
	devices_active = find_devices_on_adb()
	for device in devices_active:
		#call function from enable_diag module to check existing inventory
		check_if_serial_exists = lookup_generic_element(serial=device, element='Wi-Fi_MAC_address')
		if check_if_serial_exists:
			print('found this device in spreadsheet already, mac address is',check_if_serial_exists)
		else:
			wifi_mac = get_wifi_hw_address_from_adb(device)
			df = pd.read_excel(INVENTORY_SPREADSHEET)
			df2 = {'Serial_number': device, 'Wi-Fi_MAC_address': wifi_mac}
			df = df.append(df2, ignore_index = True)
			df.to_excel(INVENTORY_SPREADSHEET)