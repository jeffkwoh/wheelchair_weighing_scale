#!/usr/bin/env python3
from lib.hx711 import HX711  # import the class HX711
import RPi.GPIO as GPIO  # import GPIO
from lib.arduino_nfc import SerialNfc
from lib.scale_observer import ScaleObserver
from lib.state import State
from time import sleep
# from Adafruit_CharLCD import Adafruit_CharLCD
import lib.lcd_display as LcdDisplay
from lib.tag_data import TagData
from config import (
    NUMBER_OF_READINGS, CHANNEL, GAIN, SCALE,
    NFC_PORT,
    CLOCK_PIN, DATA_PIN, TARE_BTN_PIN, REGISTRATION_BTN_PIN,
    RS_PIN, EN_PIN, D4_PIN, D5_PIN, D6_PIN, D7_PIN)


# RolliePollie integrates both the weighing scale and NFC reader. It acts as the controller.
class RolliePollie:
    EMPTY_TAG = TagData(0, [])

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
        self._state = State.DEFAULT

        # instantiate lcd and specify pins
        self.lcd = LcdDisplay.LcdDisplay(RS_PIN, EN_PIN, D4_PIN, D5_PIN, D6_PIN, D7_PIN)
        self.lcd.init_io()
        self.lcd.init_lcd()

        # setup
        self.setup_gpio()
        self.setup_scale()
        self._observer.on_scale_dismount(self.flush_tag_data_callback)
        self._observer.on_scale_dismount(self.write_patient_weight_callback_clearer)
        self._observer.on_scale_dismount(self.lcd.set_show_nfc_write_indicator_off)
        self._observer.on_scale_mount(self.write_patient_weight_callback_adder)

    # Callbacks ###
    def test_callback(self):
        print("Tested")

    def write_patient_weight_callback_clearer(self):
        print("Callbacks cleared")
        self._observer.on_successful_weighing(self.write_patient_weight_callback, lifetime=0)
        self._observer.on_successful_weighing(self.indicate_nfc_write_callback, lifetime=0)

    def write_patient_weight_callback_adder(self):
        print("Callbacks added")
        self._observer.on_successful_weighing(self.write_patient_weight_callback, lifetime=1)
        self._observer.on_successful_weighing(self.indicate_nfc_write_callback, lifetime=1)

    def indicate_nfc_write_callback(self, total_weight, wheelchair_weight):
        self.lcd.set_show_nfc_write_indicator_on()

    def write_patient_weight_callback(self, total_weight, wheelchair_weight):
        patient_weight = round(total_weight - wheelchair_weight)
        self._ser_nfc.update_patient_weight_with_date(patient_weight)
        print("Attempt to write {} to tag".format(patient_weight))

    def flush_tag_data_callback(self):
        self._memoized_tag_data = RolliePollie.EMPTY_TAG

    def tare_callback(self, channel):
        total_weight = self._scale.get_weight_mean(NUMBER_OF_READINGS)
        self.output_weight_g_to_kg(total_weight)
        self._scale.zero(times=10)
        print("Tared")

    def register_callback(self, channel):
        total_weight = self._scale.get_weight_mean(NUMBER_OF_READINGS)
        self.output_weight_g_to_kg(total_weight)
        wheelchair_weight = self._scale.get_weight_mean(NUMBER_OF_READINGS)
        self._ser_nfc.write_wheelchair_weight(wheelchair_weight)
        print("updated wheelchair weight to {}".format(wheelchair_weight))

    # Setups ###
    def setup_scale(self):
        # Keeps resetting until scale is ready
        while not self._scale.reset():
            print("resetting")
            pass
        # measure tare and save the value as offset for current channel and gain selected.
        # keeps looping until properly zeroed
        while not self._scale.zero(times=10):
            print("zeroing")
            pass
        self._scale.set_scale_ratio(scale_ratio=SCALE)  # set ratio for current channel

    def setup_gpio(self):
        """
        :rtype: void
        """
        GPIO.setmode(GPIO.BCM)

        # Falling edge triggers interrupt #

        # Setup for taring functionality
        GPIO.setup(TARE_BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(TARE_BTN_PIN,
                              GPIO.FALLING,
                              callback=self.tare_callback,
                              bouncetime=300)

        # Setup for registration functionality
        GPIO.setup(REGISTRATION_BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(REGISTRATION_BTN_PIN,
                              GPIO.FALLING,
                              callback=self.register_callback,
                              bouncetime=300)

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
                is_nfc_present = not (tag_data is None)
                total_weight = self._scale.get_weight_mean(NUMBER_OF_READINGS)

                if tag_data:  # Memoizes a new tag data if presented with one
                    self._memoized_tag_data = tag_data
                    weight_in_grams = total_weight - self._memoized_tag_data.wheelchair_weight

                elif self._memoized_tag_data:  # In the absence of tag data, use last memoized tag data
                    weight_in_grams = total_weight - self._memoized_tag_data.wheelchair_weight

                else:  # If there is no available tag data, perform as a normal weighing scale
                    weight_in_grams = total_weight

                self._observer.update(total_weight, self._memoized_tag_data, is_nfc_present)
                self.output_weight_g_to_kg(weight_in_grams)
                print("{:.1f}kg".format(weight_in_grams / 1000))  # for debugging

        except (KeyboardInterrupt, SystemExit):
            print('\nGPIO cleaned up, serial closed(if opened)\n Bye (:')

        finally:
            self._ser_nfc.close()
            self.lcd.display_off()
            GPIO.cleanup()

    def output_weight_g_to_kg(self, weight, decimal_points=1):
        self.lcd.clear_display()

        weight_in_kg = int(round(weight / 1000, decimal_points) * 10)
        weight_in_kg = weight_in_kg if weight_in_kg != 0 else abs(0)  # converts -0 to 0
        isNegative = True if weight_in_kg < 0 else False
        weight_in_kg = abs(weight_in_kg)

        if weight_in_kg < 10:
            w_str = "  {:02}".format(weight_in_kg)
        else:
            w_str = "{:>4}".format(weight_in_kg)
        # Ensures that zeroes are positive
        # formatted_output = "{:.1f}".format(weight_in_kg if weight_in_kg != 0 else abs(weight_in_kg))

        self.lcd.display_weight(w_str, isNegative)


if __name__ == '__main__':
    RolliePollie().run()
