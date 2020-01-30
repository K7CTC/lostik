#!/usr/bin/env python3

##############################################################################
#                                                                            #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                      #
#       VERSION:  v0.9 (beta)                                                #
#   DESCRIPTION:  This utility was written for use with the Ronoth LoStik    #
#                 LoRa transceiver.  The utility connects to the LoStik      #
#                 via its serial interface and listens for incoming packets. #
#                                                                            #
#                 When executed with the "ping" argument, a "ping" message   #
#                 is sent OTA when the watchdog timeout raises the           #
#                 "radio_err" state of the LoStik.  After transmission,      #
#                 the LoStik resumes a receive state.                        #
#                                                                            #
#                 When executed with the "pong" argument, the LoStik will    #
#                 remain in a receive state until such time as a "ping"      #
#                 message is decoded.  At this time, RX is halted and a      #
#                 reply is contructed containing the RX timestamp, RSSI,     #
#                 and SNR of the received ping.  After successful            #
#                 transmission, the LoStik resumes a receive state.          #
#                                                                            #
##############################################################################

#import required modules
import argparse
import serial
import time
import sys
import pathlib
import os

#start with a clear terminal window
os.system('clear')

#establish and parse command line arguments
parser = argparse.ArgumentParser(description='Ronoth LoStik Utility: Ping Pong (connectivity tester)', epilog='Created by K7CTC.  This utility tests communication between two LoRa nodes.')
parser.add_argument('--port', help='LoStik serial port descriptor. (default: /dev/ttyUSB0)', default='/dev/ttyUSB0')
parser.add_argument('--wdt', help='LoStik Watchdog Timer time-out in milliseconds. (range: 0 to 4294967295, default: 15000)', default='15000')
group = parser.add_mutually_exclusive_group()
group.add_argument('--ping', help='Operate in "ping" mode.  TX cycle controlled by WDT timeout value.', action='store_true')
group.add_argument('--pong', help='Operate in "pong" mode.  LoStik will "pong" immediately upon receipt of "ping".', action='store_true')
args = parser.parse_args()

#function for controlling lostik LEDS
def lostik_led_control(led, state): #led values are 'rx' or 'tx' and state values are 'on' or 'off'
    if led == 'rx':
        if state == 'off':
            lostik.write(b'sys set pindig GPIO10 0\r\n') #GPIO10 is the blue rx led
            if lostik.readline().decode('ASCII').rstrip() == 'ok':
                return True
            else:
                return False
        elif state == 'on':
            lostik.write(b'sys set pindig GPIO10 1\r\n') #GPIO10 is the blue rx led
            if lostik.readline().decode('ASCII').rstrip() == 'ok':
                return True
            else:
                return False
    elif led == 'tx':
        if state == 'off':
            lostik.write(b'sys set pindig GPIO11 0\r\n') #GPIO11 is the red tx led
            if lostik.readline().decode('ASCII').rstrip() == 'ok':
                return True
            else:
                return False
        elif state == 'on':
            lostik.write(b'sys set pindig GPIO11 1\r\n') #GPIO11 is the red tx led
            if lostik.readline().decode('ASCII').rstrip() == 'ok':
                return True
            else:
                return False
    else:
        return False

#function that can bypass the print() buffer so the console can be updated in real-time
def incremental_print(text):
    sys.stdout.write(str(text))
    sys.stdout.flush()

#function for controlling lostik receive state
def lostik_rx_control(state): #state values are 'on' or 'off'
    if state == 'on':
        #place LoStik in continuous receive mode
        lostik.write(b'radio rx 0\r\n')
        response = lostik.readline().decode('ASCII').rstrip()
        if response == 'ok':
            lostik_led_control('rx', 'on')
            return True
        else:
            return False
    elif state == 'off':
        #halt LoStik continuous receive mode
        lostik.write(b'radio rxstop\r\n')
        if lostik.readline().decode('ASCII').rstrip() == 'ok':
            lostik_led_control('rx', 'off')
            return True
        else:
            print('ERROR: Unable to halt continuous receive mode.')
            sys.exit(1)
            
#ping function
def ping():
    if lostik_rx_control('off'):
        tx_start_time = 0
        tx_end_time = 0
        print('--ping argument detected, now sending ping!')
        print('PLAIN TEXT: Ping!')
        print('  RAW DATA: radio tx 50696E6721\n')
        lostik.write(b'radio tx 50696E6721\r\n')
        if lostik.readline().decode('ASCII').rstrip() == 'ok':
            tx_start_time = int(round(time.time()*1000))
            lostik_led_control('tx', 'on')
            incremental_print('Transmitting')
        else:
            print('ERROR: Unable to transmit "Ping!" message.')
            sys.exit(1)
        response = ''
        while response == '':
            response = lostik.readline().decode('ASCII').rstrip()
            incremental_print('.')
        else:
            if response == 'radio_tx_ok':
                tx_end_time = int(round(time.time()*1000))
                lostik_led_control('tx', 'off')
                tx_time = tx_end_time - tx_start_time
                incremental_print('DONE!  Transmit time: ' + str(tx_time) + 'ms\n\n')
            elif response == 'radio_err':
                lostik_led_control('tx', 'off')
                incremental_print(' FAILURE!\n')

#pong function
def pong(send_rssi, send_snr):
    if lostik_rx_control('off'):
        tx_start_time = 0
        tx_end_time = 0
        send_rssi_bytes = send_rssi.encode('ASCII')
        send_snr_bytes = send_snr.encode('ASCII')
        send_msg_bytes = b''.join([b'Pong!  RSSI: ', send_rssi_bytes, b'dBm  SNR: ', send_snr_bytes, b'dB'])
        send_msg_hex = send_msg_bytes.hex()
        assemble_command = 'radio tx ' + send_msg_hex + '\r\n'
        command = assemble_command.encode('ASCII')
        print('PLAIN TEXT: radio tx ' + send_msg_bytes.decode('ASCII'))
        print('  RAW DATA: ' + command.decode('ASCII').rstrip() + '\n')
        lostik.write(command)
        if lostik.readline().decode('ASCII').rstrip() == 'ok':
            tx_start_time = int(round(time.time()*1000))
            lostik_led_control('tx', 'on')
            incremental_print('Transmitting')
        else:
            print('ERROR: Unable to transmit "Pong!" message.')
            sys.exit(1)
        response = ''
        while response == '':
            response = lostik.readline().decode('ASCII').rstrip()
            incremental_print('.')
        else:
            if response == 'radio_tx_ok':
                tx_end_time = int(round(time.time()*1000))
                lostik_led_control('tx', 'off')
                tx_time = tx_end_time - tx_start_time
                incremental_print(' DONE!  Transmit time: ' + str(tx_time) + 'ms\n\n')
            elif response == 'radio_err':
                lostik_led_control('tx', 'off')
                incremental_print(' FAILURE!\n')

#function to obtain rssi of last received packet
def lostik_get_rssi():
    lostik.write(b'radio get rssi\r\n')
    rssi = lostik.readline().decode('ASCII').rstrip()
    return rssi
                
#function to obtain snr of last received packet
def lostik_get_snr():
    lostik.write(b'radio get snr\r\n')
    snr = lostik.readline().decode('ASCII').rstrip()
    return snr

##### BEGIN LOSTIK INITIALIZATION #####

#network settings to be written to LoStik (all network nodes must share the same settings)
#Frequency (default=923300000)
set_freq = b'923300000'                #value range: 902000000 to 928000000
#Modulation Mode (default=lora)
set_mod = b'lora'                      #this exists just in case the radio was mistakenly set to FSK somehow
#CRC Header (default=on)
set_crc = b'on'                        #values: on, off (not sure why off exists, best to just leave it on)
#IQ Inversion (default=off)
set_iqi = b'off'                       #values: on, off (not sure why on exists, best to just leave it off)
#Sync Word (default=34)
set_sync = b'34'                       #value: one hexadecimal byte
#Spreading Factor (default=sf12)
set_sf = b'sf12'                       #values: sf7, sf8, sf9, sf10, sf11, sf12
#Radio Bandwidth (default=125)
set_bw = b'125'                        #values: 125, 250, 500

#node settings to be written to LoStik (these settings are adjustable per node)
#Transmit Power (default=2)
set_pwr = b'2'                         #value range: 2 to 20
#Coding Rate (default=4/5)
set_cr = b'4/5'                        #values: 4/5, 4/6, 4/7, 4/8
#Watchdog Timer Timeout (default=15000)
set_wdt = bytes(args.wdt, 'ASCII')     #value range: 0 to 4294967295 (0 disables wdt functionality)

#check to see if the port descriptor path exists (determines if device is connected)
lostik_path = pathlib.Path(args.port)
try:
    print('Looking for LoStik...\r', end='')
    lostik_abs_path = lostik_path.resolve(strict=True)
except FileNotFoundError:
    print('Looking for LoStik... FAILURE!')
    print('ERROR: LoStik serial port descriptor not found!')
    print('HELP: Check serial port descriptor and/or device connection.')
    sys.exit(1)
else:
    print('Looking for LoStik... FOUND!')

#connect to lostik
try:
    print('Connecting to LoStik...\r', end='')
    lostik = serial.Serial(args.port, baudrate=57600, timeout=1)
except:
    print('Connecting to LoStik... FAILURE!')
    print('HELP: Check port permissions. Current user must be member of "dialout" group.')
    sys.exit(1)
#at this point we're already connected, but we can call the is_open method just to be sure
else:
    if lostik.is_open == True:
        print('Connecting to LoStik... CONNECTED!')
    elif lostik.is_open == False:
        print('Connecting to LoStik... FAILURE!')
        print('HELP: Check port permissions. Current user must be member of "dialout" group.')
        sys.exit(1)

#make sure both LEDs are off before continuing
rx_led_initialized = False
tx_led_initialized = False
print('Initializing status LEDs...\r', end='')
lostik.write(b'sys set pindig GPIO10 0\r\n') #GPIO10 is the blue rx led
if lostik.readline().decode('ASCII').rstrip() == 'ok':
    rx_led_initialized = True
lostik.write(b'sys set pindig GPIO11 0\r\n') #GPIO11 is the red tx led
if lostik.readline().decode('ASCII').rstrip() == 'ok':
    tx_led_initialized = True
if rx_led_initialized == True and tx_led_initialized == True:
    print('Initializing status LEDs... DONE!')
else:
    print('Initializing status LEDs...FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)

#pause mac (LoRaWAN) as this is required to access the radio directly
print('Pausing LoRaWAN protocol...\r', end='')
lostik.write(b'mac pause\r\n')
if lostik.readline().decode('ASCII').rstrip() == '4294967245':
    print('Pausing LoRaWAN protocol... DONE!')
else:
    print('Pausing LoRaWAN protocol...FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)

#turn on both LEDs to indicate we are entering "configuration" mode
lostik_led_control('rx', 'on')
lostik_led_control('tx', 'on')

#write "network" settings to LoStik
print('Initializing LoRa mesh network settings...\r', end='')
#set frequency (default: 923300000)
lostik.write(b''.join([b'radio set freq ', set_freq, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Initializing LoRa mesh network settings... FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)
#set mode (default: lora)
lostik.write(b''.join([b'radio set mod ', set_mod, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Initializing LoRa mesh network settings... FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)
#set CRC header usage (default: on)
lostik.write(b''.join([b'radio set crc ', set_crc, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Initializing LoRa mesh network settings... FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)
#set IQ inversion (default: off)
lostik.write(b''.join([b'radio set iqi ', set_iqi, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Initializing LoRa mesh network settings... FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)
#set sync word (default: 34)
lostik.write(b''.join([b'radio set sync ', set_sync, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Initializing LoRa mesh network settings... FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)
#set spreading factor (default: sf12)
lostik.write(b''.join([b'radio set sf ', set_sf, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Initializing LoRa mesh network settings... FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)
#set radio bandwidth (default: 125)
lostik.write(b''.join([b'radio set bw ', set_bw, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Initializing LoRa mesh network settings... FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)
#if we made it this far, things are peachy
print('Initializing LoRa mesh network settings... DONE!')

#write "node" settings to LoStik
print('Initializing LoRa node settings...\r', end='')
#set power (default: 2)
lostik.write(b''.join([b'radio set pwr ', set_pwr, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Initializing LoRa node settings... FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)
#set coding rate (default: 4/5)
lostik.write(b''.join([b'radio set cr ', set_cr, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Initializing LoRa node settings... FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)
#set watchdog timer timeout (default: 15000)
lostik.write(b''.join([b'radio set wdt ', set_wdt, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Initializing LoRa node settings... FAILURE!')
    print('ERROR: Unexpected response from LoStik.')
    sys.exit(1)
#if we made it this far, things are peachy
print('Initializing LoRa node settings... DONE!\n')

#turn off both LEDs to indicate we have exited "configuration" mode
lostik_led_control('rx', 'off')
lostik_led_control('tx', 'off')

##### END LOSTIK INITIALIZATION #####

#the listen loop
while True:
    if lostik_rx_control('on'):
        incremental_print('Listening')
        rx_data = ''
        while rx_data == '':
            rx_data = lostik.readline().decode('ASCII').rstrip()
            incremental_print('.')
        else:
            if rx_data == 'radio_err':
                print('\n' + 'Radio Watchdog Timer Timeout' + '\n')
                if args.ping:
                    ping()
            else:
                rx_data_array = rx_data.split()
                if rx_data_array[0] == 'radio_rx':
                    rssi = lostik_get_rssi()
                    snr = lostik_get_snr()
                    if args.pong:
                        if bytes.fromhex(rx_data_array[1]).decode('ASCII') == 'Ping!':
                            print('\n')
                            print('Ping! Pong! (Heard a ping, now sending a pong!)')
                            pong(rssi, snr)
                    else:
                        print('\n')
                        print('    MSG: ' + bytes.fromhex(rx_data_array[1]).decode('ASCII'))
                        print('   RSSI: ' + rssi + 'dBm')
                        print('    SNR: ' + snr + 'dB\n')
    else:
        lostik_rx_control('off')

#disconnect from lostik
print('Disconnecting from LoStik...\r', end='')
lostik.close()
if lostik.is_open == True:
    print('Disconnecting from LoStik... FAILURE!')
elif lostik.is_open == False:
    print('Disconnecting from LoStik... DONE!')
