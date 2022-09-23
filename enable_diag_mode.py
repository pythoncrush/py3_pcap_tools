import subprocess
import pandas as pd
import re
from ADBUtilities import *
import time
import datetime
import sys

def print_error_message(e, cmd):
    print("command " + cmd + " failed")
    print("Unable to execute adb shell command, confirm device is reachable adb shell")
    print("Command Output: " + e.output.decode('utf-8'))


def get_serial_of_adb_device():
    try:
        cmd_rsp = subprocess.check_output(GETPROP_SERIALNO, shell=True)
    except subprocess.CalledProcessError as e:
        print_error_message(e, GETPROP_SERIALNO)
        return

    serial_number = 0
    for line in cmd_rsp.splitlines():
        line = line.decode('utf-8')  # This is necessary because of Python 3.7
        match = re.search(r':\s+\[(\S+)\]', line)
        if match:
            serial_number = match.group(1)
    return serial_number


def check_device_root():
    try:
        if "su: not found" in subprocess.check_output(ROOT_CHECK, shell=True).decode('utf-8'):
            print("Device is not rooted")
            return False
    except subprocess.CalledProcessError:
        print("Device is not rooted")
        return False
    print("Device is rooted")
    return True


def enable_diag_via_adb():
    print("Using adb command to enter diag mode")
    # TODO: some phones, e.g. OnePlus, need to use command setprop sys.usb.config diag,serial_cdev,rmnet,adb
    try:
        subprocess.check_output(ENABLE_DIAG, shell=True)
    except subprocess.CalledProcessError as e:
        print_error_message(e, ENABLE_DIAG)


def wake_device():
    """
    Checks if display is off, setup to enter keypad varies slightly depending on display state
    If device is on lock screen, it must not require password
    """
    display_check = subprocess.check_output(DISPLAY_POWER, shell=True).decode('utf-8')
    if "OFF" in display_check:
        print("Display is off, waking device")
        subprocess.check_output(KEYCODE_POWER, shell=True)


def lookup_diag_mode_dial_code(serial):
    """
    Looks up diag code by first converting VOHX_spreadsheet_og.xlsx to csv
    then finds relevant row by searching for serial number
    returns diag mode dial code as a string
    """
    df = pd.read_excel('INVENTORY_SPREADSHEET')
    #df.to_csv('csvfile.csv', encoding='utf-8')

    serial_list = df['Serial_number'].tolist()
    row_number = None
    for idx, val in enumerate(serial_list):
        if val == serial:
            row_number = idx
            break
    if not row_number:
        raise Exception('serial number not in spreadsheet')
    diag_code_string = df.loc[row_number, 'DIAG_dial_code']
    if diag_code_string == "unknown":
        raise Exception("No record of diag mode dial code")
    return diag_code_string


def get_dial_code_ADB_commands(serial_number):
    """
    gets dial code of specific phone
    or use local dictionary
    """
    dial_code_string = lookup_diag_mode_dial_code(serial_number)
    type_number_ADB_command = {'#': KEYCODE_POUND, '*': KEYCODE_STAR, '8': KEYCODE_NUMPAD_8, '0': KEYCODE_NUMPAD_0,
                               '1': KEYCODE_NUMPAD_1}
    dial_code = [KEYCODE_HOME, KEYCODE_DEL, KEYCODE_CALL] + [KEYCODE_DEL] * 12  # 12 is the longest length of a cell #
    for number in dial_code_string:
        dial_code.append(type_number_ADB_command[number])
    return dial_code


def enable_diag_via_keycode():
    """
    runs adb keycode commands to set diag mode
    """
    print("Using key codes to enter diag mode")
    try:
        wake_device()
        serial_number = get_serial_of_adb_device()
        for cmd in get_dial_code_ADB_commands(serial_number):
            subprocess.check_output(cmd, shell=True)
        # ran into an issue on Galaxy S8 where phone dialer app had a walkthrough
        # OPPO A71k: KEYCODE_STAR, KEYCODE_POUND, KEYCODE NUMPAD_8, KEYCODE_NUMPAD_0, KEYCODE_NUMPAD_1 didn't work
        # SAMSUNG Galaxy S8: KEYCODE_CALL didn't work
        # I don't know if keycode failures are due to manufacturer or API version

    except subprocess.CalledProcessError as e:
        print_error_message(e, KEYCODE_POWER)


def check_usb_debugging(func):
    """
    decorator function that checks whether usb debugging is enabled
    """

    def wrapper():
        if subprocess.call(DEBUGGING_CHECK, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL) == 0:
            func()
        else:
            print("Enable USB Debugging manually in phone's developer mode settings")

    return wrapper


@check_usb_debugging
def enter_diag_mode():
    """
    If device is rooted, puts device into DIAG mode which is necessary for QPST/QXDM interface
    If not rooted, inputs keycode and prompts user to enable DIAG mode via GUI
    """
    rooted = check_device_root()
    if rooted:
        enable_diag_via_adb()
        return
    enable_diag_via_keycode()
    print('Enable DIAG mode via the GUI by toggling "Full-port switch".')


def parse_command_line_arguments():
    """
    parses command line arguments and error checks inputs
    """
    if len(sys.argv) == 1:
        print("Did not find a dmc file to load into qxdm, will use default log mask")
        enter_diag_mode()

    if len(sys.argv) == 2:
        match_diag = re.search(r'(\.dmc)', sys.argv[1])
        if match_diag:
            print("found a dmc file to load into qxdm")
            enter_diag_mode()
        else:
            sys.exit("Did not find a dmc or pcap file")

    if len(sys.argv) == 3:
        match_pcap = re.search(r'(pcapng|pcap)', sys.argv[2])
        if match_pcap:
            print("found a pcap file to filter!")
            filter_log_with_tshark()
        return True


def lookup_generic_element(serial, element):
    """
    Looks up element based on serial passed in, by first converting current_device_inventory_spreadsheet_og.xlsx to csv
    then finds relevant row by searching for serial number
    returns record desired as a string. The most common use of this at the moment is passing in
    the serial and the Wi-Fi_MAC_address element and the mac address is returned
    """
    print("Serial passed in is ",serial)
    print("element passed in is ",element)
    df = pd.read_excel(INVENTORY_SPREADSHEET)
    #df.to_csv('csvfile.csv', encoding='utf-8')

    serial_list = df['Serial_number'].tolist()
    row_number = None
    for idx, val in enumerate(serial_list):
        if str(val) == str(serial):
            row_number = idx
            print("row number is ",row_number)
            break
    
    if row_number is None or element == "unknown":
       return False
    else:
        record = df.loc[row_number, element]
        return record


def filter_log_with_tshark():
    serial = sys.argv[1]
    pcap_file_name = sys.argv[2]

    # time stamp stuff
    ts = time.time()
    stamp = datetime.datetime.fromtimestamp(ts).strftime('%m-%d-%Y-%H-%M-%S')

    # get mac address from panda data frame
    mac_address = lookup_generic_element(serial=serial, element='Wi-Fi_MAC_address')

    # prepare file name
    filtered_pcap_file_name = serial + "_filtered_" + pcap_file_name
    filtered_pcap_file_name = filtered_pcap_file_name.replace(":", "-")

    # build tshark command
    tshark_call = "C:\\Program Files\\Wireshark\\tshark.exe "
    tshark_call = tshark_call + "-r " + pcap_file_name + " -w " + filtered_pcap_file_name + " eth.addr==" + mac_address
    print("filtering ", pcap_file_name, " for MAC address ", mac_address)
    try:
        subprocess.call(tshark_call)
    except IOError:
        print('An error occured trying to start tshark.exe confirm it is installed on the windows machine.')
    return True


if __name__ == "__main__":
    parse_command_line_arguments()

