# py3_pcap_tools
functions to parse, filter, and merge pcap and logcat files

#set up work environment like this:
#create a virtual environment using Python 3.10.1
virtualenv venv_pcap_tools
source source venv_pcap_tools/bin/activate
pip install -r requirements.txt


#To add new devices to inventory sheet:
python check_device_inventory.py

Syntax for pcap parsing:
python packet_parser.py plot --pcap=10_mins_vivo.pcapng        (This will parse packets and output plots and csv metric files)

Syntax for pcap filtering
python enable_diag_mode.py R5CN80FWJEP  att_log.pcapng  (the R5CN80FWJEP is the adb serial number which will have a wi-fi mac address if check_inventory is run first)
