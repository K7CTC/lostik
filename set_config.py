#!/usr/bin/env python3

##############################################################################
#                                                                            #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                      #
#       VERSION:  v1.1                                                       #
#   DESCRIPTION:  This utility was written for use with the Ronoth LoStik    #
#                 LoRa transceiver.  It is intended to be run on Linux but   #
#                 can be adapted for Windows with some modification.  The    #
#                 utility connects to the LoStik via its serial interface    #
#                 and writes all desired LoRa configuration parameters to    #
#                 the device.  The device will generally respond with 'ok'   #
#                 when a parameter is successully written.                   #
#                                                                            #
#                                                                            #
#   INFORMATION:  Ronoth LoStik does not retain radio settings between       #
#                 power cycles.                                              #
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
parser = argparse.ArgumentParser(description='Ronoth LoStik Utility: Set Configuration', epilog='Created by K7CTC.  This utility will write specified LoRa settings to the LoStik device.')
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
if lostik.readline().decode('ASCII') == '4294967245\r\n':
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
            if lostik.readline().decode('ASCII') == 'ok':
                return True
            else:
                return False
        elif state == 'on':
            lostik.write(b'sys set pindig GPIO10 1\r\n') #GPIO10 is the blue rx led
            if lostik.readline().decode('ASCII') == 'ok':
                return True
            else:
                return False
    elif led == 'tx':
        if state == 'off':
            lostik.write(b'sys set pindig GPIO11 0\r\n') #GPIO11 is the red tx led
            if lostik.readline().decode('ASCII') == 'ok':
                return True
            else:
                return False
        elif state == 'on':
            lostik.write(b'sys set pindig GPIO11 1\r\n') #GPIO11 is the red tx led
            if lostik.readline().decode('ASCII') == 'ok':
                return True
            else:
                return False
    else:
        return False

##### END LOSTIK FUNCTIONS #####

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

#turn on both LEDs
led_control('rx', 'on')
led_control('tx', 'on')

#write settings to LoStik
print('Writing LoStik Settings')
print('-----------------------')
#set mode (default: lora)
lostik.write(b''.join([b'radio set mod ', set_mod, end_line]))
print('        Set Modulation Mode (default=lora): ' + set_mod.decode('ASCII') + ' ... ' + lostik.readline().decode('ASCII'), end='')
#set frequency (default: 923300000)
lostik.write(b''.join([b'radio set freq ', set_freq, end_line]))
print('         Set Frequency (default=923300000): ' + set_freq.decode('ASCII') + ' ... ' + lostik.readline().decode('ASCII'), end='')
#set power (default: 2)
lostik.write(b''.join([b'radio set pwr ', set_pwr, end_line]))
print('            Set Transmit Power (default=2): ' + set_pwr.decode('ASCII') + ' ... ' + lostik.readline().decode('ASCII'), end='')
#set spreading factor (default: sf12)
lostik.write(b''.join([b'radio set sf ', set_sf, end_line]))
print('       Set Spreading Factor (default=sf12): ' + set_sf.decode('ASCII') + ' ... ' + lostik.readline().decode('ASCII'), end='')
#set CRC header usage (default: on)
lostik.write(b''.join([b'radio set crc ', set_crc, end_line]))
print('               Set CRC Header (default=on): ' + set_crc.decode('ASCII') + ' ... ' + lostik.readline().decode('ASCII'), end='')
#set IQ inversion (default: off)
lostik.write(b''.join([b'radio set iqi ', set_iqi, end_line]))
print('            Set IQ Inversion (default=off): ' + set_iqi.decode('ASCII') + ' ... ' + lostik.readline().decode('ASCII'), end='')
#set coding rate (default: 4/5)
lostik.write(b''.join([b'radio set cr ', set_cr, end_line]))
print('             Set Coding Rate (default=4/5): ' + set_cr.decode('ASCII') + ' ... ' + lostik.readline().decode('ASCII'), end='')
#set watchdog timer timeout (default: 15000)
lostik.write(b''.join([b'radio set wdt ', set_wdt, end_line]))
print('Set Watchdog Timer Timeout (default=15000): ' + set_wdt.decode('ASCII') + ' ... ' + lostik.readline().decode('ASCII'), end='')
#set sync word (default: 34)
lostik.write(b''.join([b'radio set sync ', set_sync, end_line]))
print('                Set Sync Word (default=34): ' + set_sync.decode('ASCII') + ' ... ' + lostik.readline().decode('ASCII'), end='')
#set radio bandwidth (default: 125)
lostik.write(b''.join([b'radio set bw ', set_bw, end_line]))
print('         Set Radio Bandwidth (default=125): ' + set_bw.decode('ASCII') + ' ... ' + lostik.readline().decode('ASCII'))

#sleep for half second
time.sleep(.5)

#turn of both LEDs
led_control('rx', 'off')
led_control('tx', 'off')

#disconnect from lostik
print('Disconnecting from LoStik...\r', end='')
lostik.close()
if lostik.is_open == True:
    print('Disconnecting from LoStik... FAIL!')
elif lostik.is_open == False:
    print('Disconnecting from LoStik... DONE!')

#user notice
print('NOTE: Settings do not persist after device power cycle.')
