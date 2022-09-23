from time import process_time,sleep
from datetime import datetime,timedelta
import subprocess
import re
import pandas as pd 
import matplotlib.pyplot as plt
import sys
import csv 
import time

def gen_current_date():
	now_today = datetime.now()
	now_past  = datetime.now() + timedelta(days=-user_time)
	cd_today  = now_today.strftime("%a %b %d %H:%M:%S %Z %Y")
	cd_past   = now_past.strftime("%a %b %d %H:%M:%S %Z %Y")
	return cd_today,cd_past

t1_start = process_time()
print('start time ',t1_start)

header_names = ['adb_time', 'PID_process','USER_username','PR_priority','NI_nice','VIRT_virtual_mem','RES_resident_mem',
				'SHR_share_mem_size','S_process_status','CPU_cpu_usage','MEM_mem_usage','TIME_cpu_time','ARGS_process_name']


if len(sys.argv) == 1:
	print("Using default 10 days since no argument was passed for days")

if len(sys.argv) > 1:
	user_time = sys.argv[1]

user_time = int(user_time)


with open("formatted_file.txt", "w") as outfile: 
	length_header = len(header_names)
	for idx, name in enumerate(header_names):
		if idx < length_header -1:
			name = name + ','
		outfile.write(name)
	outfile.write('\n')

	with open("top_bq.txt", "r") as infile:
		for line in infile:
			found_date = re.search(r'^(\D{3}).(\D{3})\s+(\d{2})\s+(\d{2}:\d{2}:\d{2})\s+(\S{3})\s+(\d{4})$', line)
						
			if found_date:
				ts_to_insert = found_date.group(0)
				#print('ts_to_insert is',ts_to_insert)
				#datetime_object = datetime.strptime(ts_to_insert, '%a %b %d %H:%M:%S %Z %Y')
				#ts_to_insert = ts_to_insert.strftime("%a %b %d %H:%M:%S %Z %Y")
				#datetime.strptime(ts_to_insert, '%Y-%m-%d')
				continue
			else:
				#This needs refactoring, ran into many issues trying lib tools and other join, split methods blah blah, all have weird issues
				#This monster regex is ugly but works for all cases and allows perfect dataframe construction
				found_valid_row = re.search(r'(\d{2,5})\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+:\S+\.\S+)\s(.*\n)',line)
				
				if found_valid_row:
					outfile.write(ts_to_insert)

					for each_match_group in range(1,13):
						outfile.write(',')
						current_match  = found_valid_row.group(each_match_group)
						#This is necessary as there are ocassionally arguments in column 12 that have commas in them
						#To be sure I'm removing all commas and swapping to a single dash so not issues arise, later on 
						#wtih weird imports in the data frame
						current_match_formatted = current_match.replace(',','-')
						outfile.write(current_match_formatted)

df = pd.read_csv("formatted_file.txt")
#df = df.loc['2020-01-01':'2029-02-01']
#df = df['adb_time']
#df2 = df.set_index('adb_time', drop = True)
print(df.head())
# cd_today,cd_past = gen_current_date()
# print('today is ',cd_today)
# print('data set will include data starting on ',cd_past)
# df2 = df2.loc[df2['adb_time'] <= cd_today]
# df2 = df2.loc[df2['adb_time'] >= cd_past]
# df_in_date_range = df2


ax = plt.gca()
# df.plot(kind='line',x='adb_time',y='MEM_mem_usage', color = 'purple', ax=ax)
# df.plot(kind='line',x='adb_time',y='SHR_share_mem_size',color = 'yellow', ax=ax)
# df.plot(kind='line',x='adb_time',y='PID_process',color = 'black', ax=ax)
df.plot(kind='bar',x='adb_time',y='CPU_cpu_usage', color='red', ax=ax)
#df['CPU_cpu_usage'].plot(kind='hist')
plt.show()

t1_stop = process_time()
print('stop time ', t1_stop)
print('elapsed time in seconds ', (t1_stop-t1_start))
print('elapsed time in minutes ', (t1_stop-t1_start)/60)
print('elapsed time in hours ', (t1_stop - t1_start) / 60 / 60)


