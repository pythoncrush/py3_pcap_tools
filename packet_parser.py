import argparse
import logging
import os
from functools import partial
from itertools import count, takewhile
from operator import attrgetter
from time import process_time
import argparse
import queue
import threading
import datetime
import pyshark
import socket
import matplotlib.pyplot as plt
from typing import Tuple, Iterator, AsyncIterable, List, Callable, Iterable, Any, Coroutine
from scapy.utils import RawPcapReader,rdpcap

#added by Brian for plot experiments
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP, UDP
from collections import Counter
from prettytable import PrettyTable
# External Imports
import scapy.all
import scapy_http.http
import plotly
import plotly.graph_objects as go

import re
import random

TIMESTAMP = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

def pcap_url_table(file_name):
    match = re.search(r'(^[^_]+)(?=_|\.)', file_name)
    device_name = None
    if match:
        device_name = match.group(1)
    print('device name is ',device_name)
    print('Opening {}...'.format(file_name))
    t1_start = process_time()
    print('start time ',t1_start)

    #initially all source packets are empty
    srcIP =[]
    dstIP =[]
    arrival_time = []
    arrival_time_cnt = []
    xData_dst=[]
    xData_src=[]
    yData_dst=[]
    yData_src=[]
   
    #DO NOT USE THIS FUNCTION VERY BUGGY WITH BIG FILES!
    #packets = rdpcap(file_name)
    
    for pkt in scapy.all.PcapReader(file_name):
        if IP in pkt:
            try:
                srcIP.append(pkt[IP].src)
                dstIP.append(pkt[IP].dst)
                arrival_time.append(pkt[IP].time)
            except:
                pass

    #Using built in collections counter function
    cnt_src_ip = Counter()
    cnt_dst_ip = Counter()
    cnt_arrival_time = Counter()
    
    for ip in srcIP:
        cnt_src_ip[ip] += 1

    for ip in dstIP:
        cnt_dst_ip[ip] += 1

    for ip in arrival_time:
        cnt_arrival_time[ip] += 1    

    table_src = PrettyTable(["IP_source", "resolved_URL","Count"])
    table_dst = PrettyTable(["IP_dstination", "resolved_URL","Count"])
    table_ts = PrettyTable(["Time_stamp","Time_stamp_formatted","Time_stamp_count"])

    for ts,ts_count in cnt_arrival_time.most_common(20):
        ts_formatted = datetime.datetime.utcfromtimestamp(ts).strftime('%Y_%m_%d_%H_%M_%S')
        arrival_time.append(ts_formatted)
        arrival_time_cnt.append(ts_formatted)
        table_ts.add_row([ts,ts_formatted, ts_count])

    for ip_src, count_src in cnt_src_ip.most_common(20):
        resolved_url_src = resolve_host_from_address(ip_src)
        if 'localhost' not in resolved_url_src:
            table_src.add_row([ip_src, resolved_url_src, count_src])
            xData_src.append(ip_src)
            yData_src.append(count_src)

    for ip_dst,count_dst in cnt_dst_ip.most_common(20):
        resolved_url_dst = resolve_host_from_address(ip_dst)
        if 'localhost' not in resolved_url_dst:
            table_dst.add_row([ip_dst, resolved_url_dst, count_dst])
            xData_dst.append(ip_dst)
            yData_dst.append(count_dst)

    table_src_name = device_name +'_table_data_src.txt'
    with open(table_src_name, 'w') as outfile1:
        outfile1.write(str(table_src))

    table_dst_name = device_name + '_table_data_dst.txt'
    with open(table_dst_name, 'w') as outfile2:
        outfile2.write(str(table_dst))    

    table_ts_name = device_name + '_table_data_ts.txt'
    with open(table_ts_name, 'w') as outfile3:
        outfile3.write(str(table_ts))    

    print("generating plots now")

    plt.figure(figsize=(10, 10))
    plt.tick_params(labelsize=12, pad=6);
    plt.xticks(rotation=90)
    plt.bar(xData_src, yData_src)
    plt.ylabel('Connection count')
    plt.xlabel('resolved IPs')
    plt.yscale('log')
    plt.title('Device name: {}'.format(device_name))
    plt.tight_layout()
    plt.savefig('source_plt_{}'.format(device_name))

    plt.bar(xData_dst, yData_dst)
    plt.ylabel('Connection count')

    plt.xlabel('resolved IPs')
    plt.title('Device name: {}'.format(device_name))
    plt.tight_layout()
    plt.savefig('destination_plt_{}'.format(device_name))

    # plt.bar(arrival_time, arrival_time_cnt)
    # plt.ylabel('arrival count')
    # plt.xlabel('arrival time')
    # plt.tight_layout()
    # plt.savefig('ts_plt_{}'.format(device_name))


    t1_stop = process_time()
    print('stop time ', t1_stop)
    print('elapsed time in seconds ', (t1_stop-t1_start))
    print('elapsed time in minutes ', (t1_stop-t1_start)/60)
    print('elapsed time in hours ', (t1_stop - t1_start) / 60 / 60)

def resolve_host_from_address(ip_address):
    name = ip_address
    try:
        (name, _, ip_address_list) = socket.gethostbyaddr(ip_address)
        #print("name is ",name)

        if 'akama' in name:
            name = 'Akamai'
        if 'lax' in name:
            name = 'Google'
        if '1e100' in name:
            name = 'Google'
        if 'insta' in name:
            name = 'Instagram'
        if 'facebook' in name:
            name = 'Facebook'
        if 'fbcdn' in name:
            name = 'Facebook'
        if 'amazon' in name:
            name = 'Amazon'

    except:
        pass
    if '104.193.88.123' in name:
        name = '104.193.88.123'

    if '117.34.34' in name:
        name = 'ChinaNet'

    if '218.60.78' in name:
        name = 'Chian Unicom'

    if '182.61.200' in name:
        name = 'DiGi'

    if '182.62.200' in name:
        name = 'Alibaba'

    if '140.205.252' in name:
        name = 'Alibaba'

    if '47.100.106' in name:
        name = 'Alibaba'

    if '220.181.107' in name:
        name = 'ChinaNet'

    if '119.167.201' in name:
        name = 'China Unicom'

    if '104.193.88' in name:
        name = 'Baidu'

    if '205.204.101' in name:
        name = 'Alibaba'

    if '104.193.88' in name:
        name = 'Baidu'

    if '204.11.56.48' in name:
        name = 'Confluence Networks Inc'

    if '8.37.239.4' in name:
        name = 'Quantil'

    if '117.34.34.221' in name:
        name = 'ChinaNet'

    if '220.242.143' in name:
        name = 'ChinaNet'

    if '47.89.76.73' in name:
        name = 'Alibaba'

    if '203.119.2' in name:
        name = 'Alibaba'

    if '120.221.30' in name:
        name = 'China Mobile'

    if '198.11.136' in name:
        name = 'China Mobile'

    if '49.7.61.193' in name:
        name = 'China Telecom'

    if '36.104.139.82' in name:
        name = 'China Telecom'

    if '198.11.132' in name:
        name = 'Alibaba'

    if '111.206' in name:
        name = 'China Unicom'

    if '123.138' in name:
        name = 'China Unicom'

    if '198.11.135' in name:
        name = 'Alibaba'

    if '49.51.65' in name:
        name = 'China Mobile'

    if '183.232' in name:
        name = 'China Mobile'

    if '183.36.108' in name:
        name = 'Baidu'

    if '117.161.2' in name:
        name = 'Baidu'

    if '113.96.109' in name:
        name = 'Baidu'

    if '103.235.47' in name:
        name = 'Baidu'

    if '255.255.255.255' in name:
        name = 'Alibaba'

    if '46.246' in name:
        name = 'Alibaba'

    if '47.246' in name:
        name = 'Alibaba'

    if '14.215' in name:
        name = 'China Telecom'

    if '183.61.51.77' in name:
        name = 'ChinaNet'

    if '180.97.66' in name:
        name = 'ChinaNet'

    if '182.61.62' in name:
        name = 'Baidu'

    if '124.239' in name:
        name = 'ChinaNet'

    if '122.225' in name:
        name = 'ChinaNet'

    if '111.62' in name:
        name = 'ChinaNet'

    if '118.123' in name:
        name = 'ChinaNet'

    if '223.202' in name:
        name = ' China Unicom'

    if '150.109.206' in name:
        name = ' Tencent'

    if '113.96.208' in name:
        name = ' China Telecom'

    if '45.60.11' in name:
        name = "Incapsula Inc"

    if '239.255.255' in name:
        name = "IANA"

    if '103.73' in name:
        name = "TouchPal HK Co"

    if '0.0.0.0' in name:
        name = 'localhost'

    if '14.29.106' in name:
        name = "ChinaNet"

    if '192.168' in name:
        name = 'localhost'

    if '172.56' in name:
        name = 'T-Mobile'
        
    if '152.' in name:
        name = 'Asus'

    if '151.101' in name:
        name = 'Fastly_CDN'

    if '157.185' in name:
        name = 'Quantil'

    if '123.53' in name:
        name = 'nearme.com.cn'
    
    if '173.194' in name:
        name = 'Google'

    if '74.125' in name:
        name = 'Google'        

    if '218.77' in name:
        name = 'Hunan_Telecom'        

    if '124.115' in name:
        name = 'zxdy.cc'

    if '67.158' in name:
        name = 'akamai'

    if '65.131' in name:
        name = 'akaima'

    if '47.88' in name:
        name = 'Alibaba'

    if '198.172' in name:
        name = 'Baidu'

    if '13.107' in name:
        name = 'Microsoft'

    if '108.128' in name:
        name = 'Amazon'

    if '203.205' in name:
        name = 'COM Telecom'

    if '67.131' in name:
        name = 'Akamai'

    if '204.79' in name:
        name = 'Microsoft'

    if '64.4.54' in name:
        name = 'Microsoft'

    if '65.158' in name:
        name = 'Century_Link'

    if '224.0.0.251' in name:
        name = 'Bonjour Services'

    #print("ip address ",ip_address,"maps to url ",name)
    return(name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Packet Parser")
    subparsers = parser.add_subparsers(help='sub-command help')

    logcat_pcap_parser = subparsers.add_parser('combine', help="Get a running log from device")
    logcat_pcap_parser.add_argument("--pcap", help="pcap filepath", type=str)
    logcat_pcap_parser.add_argument("--logcat", help="logcat filepath", type=str)

    logcat_pcap_parser = subparsers.add_parser('plot', help="plot something from the pcap file")
    logcat_pcap_parser.add_argument("--pcap", help="pcap filepath", type=str)

    args = vars(parser.parse_args())

    pcap_file = args.get("pcap")
    logcat_file = args.get("logcat")

    if pcap_file and not logcat_file:
        print('pcap file name is ', pcap_file)
        pcap_url_table(pcap_file)