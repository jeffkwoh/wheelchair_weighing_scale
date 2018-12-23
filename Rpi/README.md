# Python code for calculating weights from IKEA scale

The weighing scale used is IKEA Halen scale which supports up to 150kg with 100g increments. We then modified the scale according to the video (first link) in the credits section.

The scale is connected to the Raspberry Pi through the HX711 load cell amplifier.

## Setup

Install python 3 if you haven't.

### Credits:
Setup and modification of scale:
- https://www.youtube.com/watch?v=14YmiEycup4
Code for calibrating and calculating the weight:
- https://github.com/gandalf15/HX711/blob/master/HX711_Python3/example.py