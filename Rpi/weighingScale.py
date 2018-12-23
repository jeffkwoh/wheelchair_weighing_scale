#!/usr/bin/env python3
from hx711 import HX711  # import the class HX711
import RPi.GPIO as GPIO  # import GPIO

# Constants
NUMBER_OF_READINGS = 6

try:
    # Create an object hx which represents your real hx711 chip
    # Required input parameters are only 'dout_pin' and 'pd_sck_pin'
    # If you do not pass any argument 'gain_channel_A' then the default value is 128
    # If you do not pass any argument 'set_channel' then the default value is 'A'
    # you can set a gain for channel A even though you want to currently select channel B
    hx = HX711(dout_pin=5, pd_sck_pin=6, gain_channel_A=128, select_channel='A')

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
    hx.set_scale_ratio(scale_ratio=-21.053)  # set ratio for current channel

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
        print(str(hx.get_weight_mean(NUMBER_OF_READINGS)) + ' g')

except (KeyboardInterrupt, SystemExit):
    print('Bye :)')

finally:
    GPIO.cleanup()
