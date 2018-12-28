# Python code for calculating weights from IKEA scale

The weighing scale used is IKEA Halen scale which supports up to **150kg with 100g increments**. We then modified the scale according to the video (first link) in the credits section.

The scale is connected to the Raspberry Pi through the HX711 load cell amplifier.

## Config

Configurations of:
- serial port
- GPIO pins
- hx711(weighing scale) parameters
are to be configured in config.py before use

## Setup

1. Install python 3.5 (or later) if you haven't.
2. Install Adafruit's Char_LCD python library using `sudo pip3 install adafruit-charlcd`.

## Usage

### Without NFC tags:
Without any NFC tags, the weighing scale functions like a normal weighing scale

### With NFC tags:
When Wisca scans an NFC tag, it will read the wheelchair's weight off it and deduct the weight from the outputted value
_untill_ the person steps off the weighing scale

## Files
- `example.py` : example code provided by library. Does scaling of the readings to give weights **in grams**. Other functions are explained in this program as well. **Recommended to read through this before starting to code**

- `weighingScale.py` : the actual code that will be used. Currently, the argument passed to the scaling function is hardcoded. It would be good to include a function to allow for calibration whenever it is needed.

## Functions to be implemented
- calibrate_scale()
- calibrate_wheelchair() - manual input of the wheelchair weight to update the NFC tag and calculate the weight of the user
- clear() - clear weight from display
- hold() - I'm not sure if this is needed since we can display the weight then reset the whole on timeout.

**Other TO DOs:**
- write the weight of the patient to NFC tag
- interface with arduino to read and write to NFC tag (resource: https://www.hackster.io/gatoninja236/raspberry-pi-nfc-clothes-tracker-a90d2a)
- settle the flow of the program

### Credits:
Setup and modification of scale:
- https://www.youtube.com/watch?v=14YmiEycup4

Code for calibrating and calculating the weight:
- https://github.com/gandalf15/HX711/blob/master/HX711_Python3/example.py

Code for RPi-Arduino communication:
- https://www.hackster.io/gatoninja236/raspberry-pi-nfc-clothes-tracker-a90d2a
