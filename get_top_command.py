from time import process_time,sleep
import subprocess
import re

def get_serial_of_adb_device():
	try:
		cmd_rsp = subprocess.check_output('adb devices', shell=True)
	except subprocess.CalledProcessError as e:
		print_error_message(e, 'error')
		return

	serial_number = 0
	serial_list = []
	for line in cmd_rsp.splitlines():
		print(line)
		line = line.decode('utf-8')  # This is necessary because of Python 3.7
		match = re.search(r'^(\S+)\s+device$', line)
		if match:
			serial_number = match.group(1)
			serial_list.append(serial_number)
		serial_len = len(serial_list)
		if serial_len > 1:
			print('found ',serial_len, ' devices')
	return serial_list

serial_list =get_serial_of_adb_device()
print(serial_list)

while True:
	for serial in serial_list:
		formatted_serial = serial + '_top_logs.txt'
		print('Collection adb top logs on device ',serial)

		with open(formatted_serial, "a") as outfile:
			print('opened log file ',formatted_serial)
			date_command = 'adb -s '+serial +' shell date'
			top_command = 'adb -s '+serial +' shell top -n1 -bq'
			subprocess.call(date_command, shell=True, stdout=outfile)
			subprocess.call(top_command, shell=True, stdout=outfile)
	
