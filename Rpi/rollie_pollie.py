#!/usr/bin/env python3
from lib.hx711 import HX711  # import the class HX711
import RPi.GPIO as GPIO  # import GPIO
from lib.arduino_nfc import SerialNfc
from lib.scale_observer import ScaleObserver
from config import (
    NUMBER_OF_READINGS,
    NFC_PORT,
    CLOCK_PIN, DATA_PIN, TARE_BTN_PIN,
    CHANNEL, GAIN, SCALE)


class RolliePollie:

    def __init__(self):
        # Create an object hx which represents your real hx711 chip
        # Required input parameters are only 'dout_pin' and 'pd_sck_pin'
        # If you do not pass any argument 'gain_channel_A' then the default value is 128
        # If you do not pass any argument 'set_channel' then the default value is 'A'
        # you can set a gain for channel A even though you want to currently select channel B
        self._scale = HX711(dout_pin=DATA_PIN, pd_sck_pin=CLOCK_PIN, gain_channel_A=GAIN, select_channel=CHANNEL)
        self._ser_nfc = SerialNfc(NFC_PORT, baudrate=9600)
        self._observer = ScaleObserver()
        self._memoized_tag_data = None

        # setup
        self.setup_gpio()
        self.setup_scale()
        self._observer.on_scale_dismount(self.flush_tag_data_callback)

    # Callbacks ###

    def flush_tag_data_callback(self):
        self._memoized_tag_data = None

    def tare_callback(self, channel):
        self._scale.zero(times=10)
        print("Tared")

    # Setups ###
    def setup_scale(self):
        # Keeps resetting until scale is ready
        while self._scale.reset() is not True:
            print("resetting")
            pass
        # measure tare and save the value as offset for current channel and gain selected.
        # keeps looping until properly zeroed
        while self._scale.zero(times=10) is not True:
            print("zeroing")
            pass
        self._scale.set_scale_ratio(scale_ratio=SCALE)  # set ratio for current channel

    def setup_gpio(self):
        """
        :rtype: void
        """
        GPIO.setmode(GPIO.BCM)
        # Falling edge triggers interrupt
        # Sets up GPIO for taring functionality
        GPIO.setup(TARE_BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(TARE_BTN_PIN, GPIO.FALLING, callback=self.tare_callback, bouncetime=300)

    def run(self):
        """
        Main logic for RolliePollie weighing scale
        """
        try:
            result = self._scale.reset()  # Before we start, reset the hx711 ( not necessary)
            if result:  # you can check if the reset was successful
                print('Ready to use')
            else:
                print('not ready')

            # if you need the data fast without doing average or filtering them.
            # do some kind of loop and do not pass any argument. Default 'times' is 1
            # be aware that HX711 sometimes return invalid or wrong data.
            # you can probably see it now
            print('Weight taking the average of {} reading(s):'.format(NUMBER_OF_READINGS))
            while True:
                # the value will vary because it is only one immediate reading.
                # the default speed for hx711 is 10 samples per second
                tag_data = self._ser_nfc.get_weight()
                total_weight = self._scale.get_weight_mean(NUMBER_OF_READINGS)
                self._observer.weight = total_weight

                if tag_data:  # Memoizes a new tag data if presented with one
                    self._memoized_tag_data = tag_data
                    print('{}g'.format(total_weight - self._memoized_tag_data.wheelchair_weight))

                elif self._memoized_tag_data:  # In the absence of tag data, use last memoized tag data
                    print('{}g'.format(total_weight - self._memoized_tag_data.wheelchair_weight))

                else:  # If there is no available tag data, perform as a normal weighing scale
                    print('{}g'.format(total_weight))

        except (KeyboardInterrupt, SystemExit):
            print('\nGPIO cleaned up, serial closed(if opened)\n Bye (:')

        finally:
            GPIO.cleanup()
            self._ser_nfc.close()


if __name__ == '__main__':
    RolliePollie().run()
