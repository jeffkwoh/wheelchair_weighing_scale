#!/usr/bin/env python3
from lib.hx711 import HX711  # import the class HX711
import RPi.GPIO as GPIO  # import GPIO
from lib.arduino_nfc import SerialNfc
from config import (
    NUMBER_OF_READINGS,
    NFC_PORT,
    CLOCK_PIN, DATA_PIN, TARE_BTN_PIN,
    CHANNEL, GAIN, SCALE)


# Used for debug purposes
def test_callback(channel):
    """
    :type int: channel // to be supplied by callback's caller
    :rtype: void
    """
    print("Callback has been called on GPIO {}".format(channel))


def tare_callback(scale):
    """
    :type int: channel // to be supplied by callback's caller
    :rtype: void
    """
    def helper(channel):
        scale.zero()
        print("Tared")

    return helper


def setup_Gpio():
    """
    :rtype: void
    """
    GPIO.setmode(GPIO.BCM)
    # Falling edge triggers interrupt
    # Sets up GPIO for taring functionality
    GPIO.setup(TARE_BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(TARE_BTN_PIN, GPIO.FALLING, callback=tare_callback(hx), bouncetime=300)


def print_serial(ser):
    if (ser.in_waiting > 0):
        print(ser.readline())


try:
    # Create an object hx which represents your real hx711 chip
    # Required input parameters are only 'dout_pin' and 'pd_sck_pin'
    # If you do not pass any argument 'gain_channel_A' then the default value is 128
    # If you do not pass any argument 'set_channel' then the default value is 'A'
    # you can set a gain for channel A even though you want to currently select channel B
    hx = HX711(dout_pin=DATA_PIN, pd_sck_pin=CLOCK_PIN, gain_channel_A=GAIN, select_channel=CHANNEL)

    # setups GPIO for event callbacks
    setup_Gpio()
    ser_nfc = SerialNfc(NFC_PORT, baudrate=9600)

    result = hx.reset()  # Before we start, reset the hx711 ( not necessary)
    if result:  # you can check if the reset was successful
        print('Ready to use')
    else:
        print('not ready')

    # Read data several, or only one, time and return mean value
    # it just returns exactly the number which hx711 sends
    # argument times is not required default value is 1
    data = hx.get_raw_data_mean(times=1)

    if data != False:  # always check if you get correct value or only False
        print('Raw data: ' + str(data))
    else:
        print('invalid data')

    input('Remove any weights from the scale. Press ENTER to continue')
    # measure tare and save the value as offset for current channel
    # and gain selected. That means channel A and gain 64
    result = hx.zero(times=10)

    input('Taring done. Put weight on scale. Press ENTER to continue')
    hx.set_scale_ratio(scale_ratio=SCALE)  # set ratio for current channel

    # Read data several, or only one, time and return mean value
    # subtracted by offset and converted by scale ratio to
    # desired units. In my case in grams.
    print('Current weight on the scale in grams is: ')
    print(str(hx.get_weight_mean(6)) + ' g')

    # if you need the data fast without doing average or filtering them.
    # do some kind of loop and do not pass any argument. Default 'times' is 1
    # be aware that HX711 sometimes return invalid or wrong data.
    # you can probably see it now
    print('Weight taking the average of {} reading(s):'.format(NUMBER_OF_READINGS))
    while True:
        # the value will vary because it is only one immediate reading.
        # the default speed for hx711 is 10 samples per second
        tag_data = ser_nfc.get_weight()
        total_weight = hx.get_weight_mean(NUMBER_OF_READINGS)
        # TODO: This does not work as NFC reader gives weight reading slower than request for weight
        if tag_data:
            print('{}g'.format(total_weight - tag_data.wheelchair_weight))
        else:
            print('{}g'.format(total_weight))

except (KeyboardInterrupt, SystemExit):
    print('\nGPIO cleaned up, serial closed(if opened)\n Bye (:')

finally:
    GPIO.cleanup()
    if 'ser_nfc' in globals():
        ser_nfc.close()
