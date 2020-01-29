#!/usr/bin/env python3

##############################################################################
#                                                                            #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                      #
#       VERSION:  v0.5 (beta)                                                #
#   DESCRIPTION:  This utility was written for use with the Ronoth LoStik    #
#                 LoRa transceiver.  It is intended to be run on Linux but   #
#                 can be adapted for Windows with some modification.  The    #
#                 utility connects to the LoStik via its serial interface    #
#                 and listens for incoming packets.  When a packet is        #
#                 received, it is displayed on the console.                  #
#                                                                            #
#                 Script will listen until the watchdod timer timeout is     #
#                 triggered.  At this time, the LoStik will transmit a       #
#                 ping.                                                      #
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
parser = argparse.ArgumentParser(description='Ronoth LoStik Utility: TX Demonstration',epilog='Created by K7CTC.  This utility will transmit a static message with various modulation settings.')
parser.add_argument('-p', '--port', help='LoStik serial port descriptor (default: /dev/ttyUSB0)', default='/dev/ttyUSB0')
args = parser.parse_args()

##### BEGIN LOSTIK STARTUP #####

#check to see if the port descriptor path exists (determines if device is connected on linux systems)
lostik_path = pathlib.Path(args.port)
try:
    print('Looking for LoStik...\r', end='')
    lostik_abs_path = lostik_path.resolve(strict=True)
except FileNotFoundError:
    print('Looking for LoStik... FAIL!')
    print('ERROR: LoStik serial port descriptor not found!')
    print('HELP: Check serial port descriptor and/or device connection.')
    print('Unable to proceed, now exiting!')
    sys.exit(1)
else:
    print('Looking for LoStik... DONE!')

#connect to lostik
try:
    print('Connecting to LoStik...\r', end='')
    lostik = serial.Serial(args.port, baudrate=57600, timeout=1)
except:
    print('Connecting to LoStik... FAIL!')
    print('HELP: Check port permissions. Current user must be in "dialout" group.')
    print('Unable to proceed, now exiting!')
    sys.exit(1)
#at this point we're already connected, but we can call the is_open method just to be sure
else:
    if lostik.is_open == True:
        print('Connecting to LoStik... DONE!')
    elif lostik.is_open == False:
        print('Connecting to LoStik... FAIL!')
        print('HELP: Check port permissions. Current user must be in "dialout" group.')
        print('Unable to proceed, now exiting!')
        sys.exit(1)

#make sure both LEDs are off before continuing
rx_led_off = False
tx_led_off = False
print('Checking status LEDs...\r', end='')
lostik.write(b'sys set pindig GPIO10 0\r\n') #GPIO10 is the blue rx led
if lostik.readline().decode('ASCII').rstrip() == 'ok':
    rx_led_off = True
lostik.write(b'sys set pindig GPIO11 0\r\n') #GPIO11 is the red tx led
if lostik.readline().decode('ASCII').rstrip() == 'ok':
    tx_led_off = True
if rx_led_off == True and tx_led_off == True:
    print('Checking status LEDs... DONE!')
else:
    print('Checking status LEDs...FAIL!')
    print('ERROR: Error communicating with LoStik.')
    print('Unable to proceed, now exiting!')
    sys.exit(1)

#pause mac (LoRaWAN) as this is required to access the radio directly
print('Pausing LoRaWAN protocol stack...\r', end='')
lostik.write(b'mac pause\r\n')
if lostik.readline().decode('ASCII').rstrip() == '4294967245':
    print('Pausing LoRaWAN protocol stack... DONE!\n')
else:
    print('Pausing LoRaWAN protocol stack...FAIL!')
    print('ERROR: Error communicating with LoStik.')
    print('Unable to proceed, now exiting!')
    sys.exit(1)

##### END LOSTIK STARTUP #####

##### BEGIN LOSTIK FUNCTIONS #####

#function for controlling LEDS
def led_control(led, state):
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

##### END LOSTIK FUNCTIONS #####

##### BEGIN OTHER FUNCTIONS #####

#function that can bypass the print() buffer so the console can be updated in real-time
def incremental_print(text):
    sys.stdout.write(str(text))
    sys.stdout.flush()

##### END OTHER FUNCTIONS #####

##### BEGIN INITIALIZE LOSTIK SETTINGS #####
#settings to be written to LoStik
#Modulation Mode (default=lora)
set_mod = b'lora'                      #this exists just in case the radio was mistakenly set to FSK somehow
#Frequency (default=923300000)
set_freq = b'923300000'                #value range: 902000000 to 928000000
#Transmit Power (default=2)
set_pwr = b'2'                         #value range: 2 to 20
#Spreading Factor (default=sf12)
set_sf = b'sf12'                       #values: sf7, sf8, sf9, sf10, sf11, sf12
#CRC Header (default=on)
set_crc = b'on'                        #values: on, off (not sure why off exists, best to just leave it on)
#IQ Inversion (default=off)
set_iqi = b'off'                       #values: on, off (not sure why on exists, best to just leave it off)
#Coding Rate (default=4/5)
set_cr = b'4/5'                        #values: 4/5, 4/6, 4/7, 4/8
#Watchdog Timer Timeout (default=15000)
set_wdt = b'15000'                     #value range: 0 to 4294967295 (0 disables wdt functionality)
#Sync Word (default=34)
set_sync = b'34'                       #value: one hexadecimal byte
#Radio Bandwidth (default=125)
set_bw = b'125'                        #values: 125, 250, 500
#end of line bytes
end_line = b'\r\n'

#write settings to LoStik
print('Restoring dafault settings...\r', end='')
#set mode (default: lora)
lostik.write(b''.join([b'radio set mod ', set_mod, end_line]))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Restoring default settings...FAIL!')
    sys.exit(1)
#set frequency (default: 923300000)
lostik.write(b''.join([b'radio set freq ', set_freq, end_line]))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Restoring default settings...FAIL!')
    sys.exit(1)
#set power (default: 2)
lostik.write(b''.join([b'radio set pwr ', set_pwr, end_line]))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Restoring default settings...FAIL!')
    sys.exit(1)
#set spreading factor (default: sf12)
lostik.write(b''.join([b'radio set sf ', set_sf, end_line]))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Restoring default settings...FAIL!')
    sys.exit(1)
#set CRC header usage (default: on)
lostik.write(b''.join([b'radio set crc ', set_crc, end_line]))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Restoring default settings...FAIL!')
    sys.exit(1)
#set IQ inversion (default: off)
lostik.write(b''.join([b'radio set iqi ', set_iqi, end_line]))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Restoring default settings...FAIL!')
    sys.exit(1)
#set coding rate (default: 4/5)
lostik.write(b''.join([b'radio set cr ', set_cr, end_line]))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Restoring default settings...FAIL!')
    sys.exit(1)
#set watchdog timer timeout (default: 15000)
lostik.write(b''.join([b'radio set wdt ', set_wdt, end_line]))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Restoring default settings...FAIL!')
    sys.exit(1)
#set sync word (default: 34)
lostik.write(b''.join([b'radio set sync ', set_sync, end_line]))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Restoring default settings...FAIL!')
    sys.exit(1)
#set radio bandwidth (default: 125)
lostik.write(b''.join([b'radio set bw ', set_bw, end_line]))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('Restoring default settings...FAIL!')
    sys.exit(1)
#if we made it this far, things are peachy
print('Restoring default settings...DONE!\n')
##### BEGIN INITIALIZE LOSTIK SETTINGS #####

##### EXPERIMENTAL TX CODE #####
#we're going to break from the RX loop and try to send a packet
def send_pong(send_rx_time, send_rssi, send_snr):
    tx_start_time = 0
    tx_end_time = 0
    lostik.write(b'radio rxstop\r\n')
    if lostik.readline().decode('ASCII').rstrip() != 'ok':
        print('ERROR: Error communicating with LoStik.')
        print('Unable to proceed, now exiting!')
        sys.exit(1)
    else:
        led_control('rx', 'off')
        #build message and convert to hex
        send_rx_time_bytes = send_rx_time.encode('ASCII')
        send_rssi_bytes = send_rssi.encode('ASCII')
        send_snr_bytes = send_snr.encode('ASCII')
        send_msg_bytes = b''.join([b"['",send_rx_time_bytes,b"'],['",send_rssi_bytes,b"'],['",send_snr_bytes,b"']"])
        send_msg_hex = send_msg_bytes.hex()
        assemble_command = 'radio tx ' + send_msg_hex + '\r\n'
        command = assemble_command.encode('ASCII')
        #print('PLAIN TEXT: ' + send_msg_bytes)
        print('  RAW DATA: ' + command.decode('ASCII').rstrip() + '\n')
        lostik.write(command)
        if lostik.readline().decode('ASCII').rstrip() == 'ok':
            tx_start_time = int(round(time.time()*1000)) #get current unix epoch time in milliseconds
            led_control('tx', 'on')
            incremental_print('Transmitting')
        else:
            print('ERROR: Error communicating with LoStik.')
            print('Unable to proceed, now exiting!')
            sys.exit(1)
        response = ''
        while response == '':
            response = lostik.readline().decode('ASCII').rstrip()
            incremental_print('.')
        else:
            if response == 'radio_tx_ok':
                tx_end_time = int(round(time.time()*1000))
                led_control('tx', 'off')
                time_on_air = tx_end_time - tx_start_time
                incremental_print('DONE!  Total time on air: ' + str(time_on_air) + 'ms\n\n')
            elif response == 'radio_err':
                led_control('tx', 'off')
                incremental_print('FAIL!\n')




def send_ping():
    tx_start_time = 0
    tx_end_time = 0
    lostik.write(b'radio rxstop\r\n')
    if lostik.readline().decode('ASCII').rstrip() != 'ok':
        print('ERROR: Error communicating with LoStik.')
        print('Unable to proceed, now exiting!')
        sys.exit(1)
    else:
        led_control('rx', 'off')
        print('PLAIN TEXT: ping')
 #       assemble_command = 'radio tx ' + send_msg_hex + '\r\n'
        print('  RAW DATA: 70696E67\n')
        lostik.write(b'radio tx 70696E67\r\n')
        if lostik.readline().decode('ASCII').rstrip() == 'ok':
            tx_start_time = int(round(time.time()*1000)) #get current unix epoch time in milliseconds
            led_control('tx', 'on')
            incremental_print('Transmitting')
        else:
            print('ERROR: Error communicating with LoStik.')
            print('Unable to proceed, now exiting!')
            sys.exit(1)
        response = ''
        while response == '':
            response = lostik.readline().decode('ASCII').rstrip()
            incremental_print('.')
        else:
            if response == 'radio_tx_ok':
                tx_end_time = int(round(time.time()*1000))
                led_control('tx', 'off')
                time_on_air = tx_end_time - tx_start_time
                incremental_print('DONE!  Total time on air: ' + str(time_on_air) + 'ms\n\n')
            elif response == 'radio_err':
                led_control('tx', 'off')
                incremental_print('FAIL!\n')









#listen for incoming packets
while True:
    lostik.write(b'radio rx 0\r\n')
    response = lostik.readline().decode('ASCII').rstrip()
    if response == 'ok':
        led_control('rx', 'on')
        incremental_print('Listening')
        rx_data = ''
        while rx_data == '':
            rx_data = lostik.readline().decode('ASCII').rstrip()
            incremental_print('.')
        else:
            if rx_data == 'radio_err':
                print('\n' + 'Radio Watchdog Timer Timeout' + '\n')
            else:
                rx_data_array = rx_data.split()
                if rx_data_array[0] == 'radio_rx':
                    rx_time = int(round(time.time()*1000)) #get current unix epoch time in milliseconds
                    rx_time_str = str(rx_time)
                    lostik.write(b'radio get rssi\r\n')
                    rssi = lostik.readline().decode('ASCII').rstrip()
                    print(rssi)
                    lostik.write(b'radio get snr\r\n')
                    snr = lostik.readline().decode('ASCII').rstrip()
                    print(snr)
                    if bytes.fromhex(rx_data_array[1]).decode('ASCII') == 'ping':
                        print('Received a ping!!!  Now sending reply!!!')
                        send_pong(rx_time_str, rssi, snr)
                    else:
                        print('\n' + '    MSG: ' + bytes.fromhex(rx_data_array[1]).decode('ASCII'))
                        lostik.write(b'radio get rssi\r\n')
                        print('   RSSI: ' + rssi + 'dBm')
                        lostik.write(b'radio get snr\r\n')
                        print('    SNR: ' + snr + 'dB')
                        print('RX TIME: ' + str(rx_time) + '\n')
    elif response == 'busy':
        lostik.write(b'radio rxstop\r\n')
        if lostik.readline().decode('ASCII').rstrip() != 'ok':
            print('ERROR: Error communicating with LoStik.')
            print('Unable to proceed, now exiting!')
            sys.exit(1)

#disconnect from lostik
print('Disconnecting from LoStik...\r', end='')
lostik.close()
if lostik.is_open == True:
    print('Disconnecting from LoStik... FAIL!')
elif lostik.is_open == False:
    print('Disconnecting from LoStik... DONE!')
