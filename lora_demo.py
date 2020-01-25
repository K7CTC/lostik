#!/usr/bin/env python3

##############################################################################
#                                                                            #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                      #
#       VERSION:  v1.0                                                       #
#   DESCRIPTION:  This utility was written for use with the Ronoth LoStik    #
#                 LoRa transceiver.  It is intended to be run on Linux but   #
#                 can be adapted for Windows with some modification.  The    #
#                 utility connects to the LoStik via its serial interface    #
#                 and instructs it to perform a series of test transmissions #
#                 whilst cycling through various modulation parameters       #
#                 (spreading factor, coding rate and bandwidth).  All test   #
#                 transmissions carry an identical simple text payload       #
#                 that allows the user to observe how the different          #
#                 modulation parameters impact the actual transmission       #
#                 (transmission length/time-on-air, consumed spectral        #
#                 bandwidth, etc.).                                          #
#                                                                            #
##############################################################################

#import required modules
import argparse
import serial
import time
import sys
import pathlib
import os

#establish and parse command line arguments
parser = argparse.ArgumentParser(description='Ronoth LoStik Utility: TX Demonstration',epilog='Created by K7CTC.  This utility will transmit a static message with various modulation settings.')
parser.add_argument('-p', '--port', help='LoStik serial port descriptor (default: /dev/ttyUSB0)', default='/dev/ttyUSB0')
args = parser.parse_args()

#check to see if the port descriptor path exists (determines if device is connected)
lostik_path = pathlib.Path(args.port)
try:
    lostik_abs_path = lostik_path.resolve(strict=True)
except FileNotFoundError:
    print('LoStik serial port descriptor not found!')
    print('Check serial port descriptor and/or device connection.')
    print('Unable to proceed, now exiting!')
    sys.exit(1)

#let's give a brief introduction
os.system('clear')
print('Purpose')
print('-------')
print('This utility connects to the LoStik via its serial interfact and instructs')
print('it to perform a series of test transmissions whilst cycling through')
print('various modulation parameters (spreading factor, coding rate and bandwidth).')
print('All test transmissions carry an identical simple text payload that allows')
print('the user to observe how the different modulation parameters impact the actual')
print('transmission (transmission length/time-on-air, consumed spectral bandwidth,)')
print('etc.).  This test is best accompanied with an SDR so that the received')
print('signals can be properly viewed and analized.\n')
input('Press Enter to continue...')
print()

#connect to lostik
os.system('clear')
try:
    print('Connecting to LoStik...\r', end='')
    lostik = serial.Serial(args.port, baudrate=57600, timeout=5)
except:
    print('Connecting to LoStik... FAIL!  Check port permissions.')
    print('Unable to proceed, now exiting!')
    sys.exit(1)
else:
    if lostik.is_open == True:
        print('Connecting to LoStik... DONE!')
    elif lostik.is_open == False:
        print('Connecting to LoStik... FAIL!  Check port permissions.')
        print('Unable to proceed, now exiting!')
        sys.exit(1)

#pause mac (LoRaWAN) as this is required to access the radio directly
print('Pausing LoRaWAN protocol stack...\r', end='')
lostik.write(b'mac pause\r\n')
if lostik.readline().decode('ASCII') == '4294967245\r\n':
    print('Pausing LoRaWAN protocol stack... DONE!\n')
else:
    print('Pausing LoRaWAN protocol stack...FAIL!\n')

#static settings to be written to LoStik (until device power cycle)
#Modulation Mode (default=lora)
set_mod = b'lora'                      #this exists just in case the radio was mistakenly set to FSK somehow
#Frequency (default=923300000)
set_freq = b'923300000'                #value range: 902000000 to 928000000
#Transmit Power (default=2)
set_pwr = b'4'                         #value range: 2 to 20
#CRC Header (default=on)
set_crc = b'on'                        #values: on, off (not sure why off exists, best to just leave it on)
#IQ Inversion (default=off)
set_iqi = b'off'                       #values: on, off (not sure why on exists, best to just leave it off)
#Watchdog Timer Timeout (default=15000)
set_wdt = b'15000'                     #value range: 0 to 4294967295 (0 disables wdt functionality)
#Sync Word (default=34)
set_sync = b'34'                       #value: one hexadecimal byte
#end of line bytes
end_line = b'\r\n'

#write settings to LoStik
print('Initializing LoStik for Demo')
print('----------------------------')
#set mode (default: lora)
lostik.write(b''.join([b'radio set mod ', set_mod, end_line]))
print('Set Modulation Mode = ' + set_mod.decode('ASCII') + ': ' + lostik.readline().decode('ASCII'), end='')
#set frequency (default: 923300000)
lostik.write(b''.join([b'radio set freq ', set_freq, end_line]))
print('Set Frequency = ' + set_freq.decode('ASCII') + ': ' + lostik.readline().decode('ASCII'), end='')
#set power (default: 2)
lostik.write(b''.join([b'radio set pwr ', set_pwr, end_line]))
print('Set Transmit Power = ' + set_pwr.decode('ASCII') + ': ' + lostik.readline().decode('ASCII'), end='')
#set CRC header usage (default: on)
lostik.write(b''.join([b'radio set crc ', set_crc, end_line]))
print('Set CRC Header = ' + set_crc.decode('ASCII') + ': ' + lostik.readline().decode('ASCII'), end='')
#set IQ inversion (default: off)
lostik.write(b''.join([b'radio set iqi ', set_iqi, end_line]))
print('Set IQ Inversion = ' + set_iqi.decode('ASCII') + ': ' + lostik.readline().decode('ASCII'), end='')
#set watchdog timer timeout (default: 15000)
lostik.write(b''.join([b'radio set wdt ', set_wdt, end_line]))
print('Set Watchdog Timer Timeout = ' + set_wdt.decode('ASCII') + ': ' + lostik.readline().decode('ASCII'), end='')
#set sync word (default: 34)
lostik.write(b''.join([b'radio set sync ', set_sync, end_line]))
print('Set Sync Word = ' + set_sync.decode('ASCII') + ': ' + lostik.readline().decode('ASCII'))
input('Press Enter to continue...')

#let's establish the test messages that will be sent OTA
#63 byte message
message_short = "['1','K7CTC','K2SEC','We arrived at camp... Weather is great!']"
message_short_hex = b"['1','K7CTC','K2SEC','We arrived at camp... Weather is great!']".hex()
#255 byte message
message_long = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut augue augue, volutpat quis nisi vitae, venenatis vestibulum justo. Phasellus neque nisi, eleifend sed enim eu, imperdiet faucibus orci. Nam ut lectus velit. Aliquam vel orci a massa semper metus.'
message_long_hex = b'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut augue augue, volutpat quis nisi vitae, venenatis vestibulum justo. Phasellus neque nisi, eleifend sed enim eu, imperdiet faucibus orci. Nam ut lectus velit. Aliquam vel orci a massa semper metus.'.hex()

#function for running test transmissions
def run_test(sf_value, cr_value, bw_value):
    #settings to be written to LoStik
    #Spreading Factor (default=sf12)
    set_sf = sf_value                       #values: sf7, sf8, sf9, sf10, sf11, sf12
    #Coding Rate (default=4/5)
    set_cr = cr_value                        #values: 4/5, 4/6, 4/7, 4/8
    #Radio Bandwidth (default=125)
    set_bw = bw_value                        #values: 125, 250, 500

    #write settings to LoStik
    os.system('clear')
    print('Writing LoStik Settings')
    print('-----------------------')
    #set spreading factor (default: sf12)
    lostik.write(b''.join([b'radio set sf ', set_sf, end_line]))
    print('Set Spreading Factor = ' + set_sf.decode('ASCII') + ': ' + lostik.readline().decode('ASCII'), end='')
    #set coding rate (default: 4/5)
    lostik.write(b''.join([b'radio set cr ', set_cr, end_line]))
    print('      Set Coding Rate = ' + set_cr.decode('ASCII') + ': ' + lostik.readline().decode('ASCII'), end='')
    #set radio bandwidth (default: 125)
    lostik.write(b''.join([b'radio set bw ', set_bw, end_line]))
    print('  Set Radio Bandwidth = ' + set_bw.decode('ASCII') + ': ' + lostik.readline().decode('ASCII'))

    #pause before transmitting
    input('Press Enter to TX short message...')
    print()

    #perform test transmission(s)
    print('Transmitting Short Message (63 bytes)')
    print('-------------------------------------')

    #turn on 'transmit' LED
    lostik.write(b'sys set pindig GPIO11 1\r\n')
    from_lostik = lostik.readline().decode('ASCII')

    #transmit message here
    print('PLAIN TEXT: ' + message_short + '\n')
    assemble_command = 'radio tx ' + str(message_short_hex) + '\r\n'
    command = assemble_command.encode('ASCII')
    print('  RAW DATA: ' + command.decode('ASCII'))
    lostik.write(command)
    print('TX COMMAND: ' + lostik.readline().decode('ASCII'), end='')
    time.sleep(5)
    print(' TX RESULT: ' + lostik.readline().decode('ASCII'))
  
    #turn off 'transmit' LED
    lostik.write(b'sys set pindig GPIO11 0\r\n')
    from_lostik = lostik.readline().decode('ASCII')

    #pause before transmitting
    input('Press Enter to TX long message...')
    print()

    #perform test transmission(s)
    print('Transmitting Long Message (255 bytes)')
    print('-------------------------------------')

    #turn on 'transmit' LED
    lostik.write(b'sys set pindig GPIO11 1\r\n')
    from_lostik = lostik.readline().decode('ASCII')

    #transmit message here
    print('PLAIN TEXT: ' + message_long + '\n')
    assemble_command = 'radio tx ' + str(message_long_hex) + '\r\n'
    command = assemble_command.encode('ASCII')
    print('  RAW DATA: ' + command.decode('ASCII'))
    lostik.write(command)
    print('TX COMMAND: ' + lostik.readline().decode('ASCII'), end='')
    time.sleep(15)
    print(' TX RESULT: ' + lostik.readline().decode('ASCII'))
  
    #turn off 'transmit' LED
    lostik.write(b'sys set pindig GPIO11 0\r\n')
    from_lostik = lostik.readline().decode('ASCII')

    #pause for next test
    input('Press Enter to continue...')

#iterate through tests
run_test(b'sf12', b'4/5', b'125')
#run_test(b'sf7', b'4/5', b'125')
run_test(b'sf12', b'4/8', b'125')
#run_test(b'sf12', b'4/5', b'500')

#disconnect from lostik
print('Disconnecting from LoStik...\r', end='')
lostik.close()
if lostik.is_open == True:
    print('Disconnecting from LoStik... FAIL!')
elif lostik.is_open == False:
    print('Disconnecting from LoStik... DONE!')