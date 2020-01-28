#!/usr/bin/env python3

##############################################################################
#                                                                            #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                      #
#       VERSION:  v1.2                                                       #
#   DESCRIPTION:  This utility was written for use with the Ronoth LoStik    #
#                 LoRa transceiver.  It is intended to be run on Linux but   #
#                 can be adapted for Windows with some modification.  The    #
#                 utility connects to the LoStik via its serial interface    #
#                 and polls all of the current LoRa mode configuration       #
#                 parameters.  Also presented are the device defaults as     #
#                 described within the Microchip RN2903 command reference    #
#                 document.                                                  #
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
parser = argparse.ArgumentParser(description='Ronoth LoStik Utility: Get Configuration', epilog='Created by K7CTC.  This utility will output relevant LoRa settings from the LoStik device.')
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

#turn on both LEDs
led_control('rx', 'on')
led_control('tx', 'on')

#get a bunch of stuff from the radio
print('Current LoStik Configuration')
print('----------------------------')
#get firmware version (RN2903 1.0.5 Nov 06 2018 10:45:27)
lostik.write(b'sys get ver\r\n')
print('                       Firmware Version: ' + lostik.readline().decode('ASCII'), end='')
#get mode (default: lora)
lostik.write(b'radio get mod\r\n')
print('         Modulation Mode (default=lora): ' + lostik.readline().decode('ASCII'), end='')
#get frequency (default: 923300000)
lostik.write(b'radio get freq\r\n')
print('          Frequency (default=923300000): ' + lostik.readline().decode('ASCII'), end='')
#get power (default: 2)
lostik.write(b'radio get pwr\r\n')
print('             Transmit Power (default=2): ' + lostik.readline().decode('ASCII'), end='')
#get spreading factor (default: sf12)
lostik.write(b'radio get sf\r\n')
print('        Spreading Factor (default=sf12): ' + lostik.readline().decode('ASCII'), end='')
#get CRC header usage (default: on)
lostik.write(b'radio get crc\r\n')
print('                CRC Header (default=on): ' + lostik.readline().decode('ASCII'), end='')
#get if IQ inversion is used (default: off)
lostik.write(b'radio get iqi\r\n')
print('             IQ Inversion (default=off): ' + lostik.readline().decode('ASCII'), end='')
#get coding rate (default: 4/5)
lostik.write(b'radio get cr\r\n')
print('              Coding Rate (default=4/5): ' + lostik.readline().decode('ASCII'), end='')
#get watchdog timer timeout (default: 15000)
lostik.write(b'radio get wdt\r\n')
print(' Watchdog Timer Timeout (default=15000): ' + lostik.readline().decode('ASCII'), end='')
#get sync word (default: 34)
lostik.write(b'radio get sync\r\n')
print('                 Sync Word (default=34): ' + lostik.readline().decode('ASCII'), end='')
#get radio bandwidth (default: 125)
lostik.write(b'radio get bw\r\n')
print('          Radio Bandwidth (default=125): ' + lostik.readline().decode('ASCII'), end='')
#get SNR from last received packet (default: -128)
lostik.write(b'radio get snr\r\n')
print('Last Received Packet SNR (default=-128): ' + lostik.readline().decode('ASCII'), end='')
#get RSSI from last received frame (default: -128)
lostik.write(b'radio get rssi\r\n')
print('Last Received Frame RSSI (default=-128): ' + lostik.readline().decode('ASCII'))

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
