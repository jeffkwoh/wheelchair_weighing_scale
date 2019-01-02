########################################################################
#
# LCD4: Learning how to control an LCD module from Pi
# See w8bh.net for more information.
#
########################################################################
import time  # for timing delays
import RPi.GPIO as GPIO
import random

# OUTPUTS: map GPIO to LCD lines
LCD_RS = 19  # GPIO7 = Pi pin 26
LCD_E = 13  # GPIO8 = Pi pin 24
LCD_D4 = 11  # GPIO17 = Pi pin 11
LCD_D5 = 9  # GPIO18 = Pi pin 12
LCD_D6 = 10  # GPIO21 = Pi pin 13
LCD_D7 = 22  # GPIO22 = Pi pin 15

OUTPUTS = [LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7]

# HD44780 Controller Commands
CLEAR_DISPLAY = 0x01
RETURN_HOME = 0x02
RIGHT_TO_LEFT = 0x04
LEFT_TO_RIGHT = 0x06
DISPLAY_OFF = 0x08
CURSOR_OFF = 0x0C
CURSOR_ON = 0x0E
CURSOR_BLINK = 0x0F
CURSOR_LEFT = 0x10
CURSOR_RIGHT = 0x14
LOAD_SYMBOL = 0x40
SET_CURSOR = 0x80

# Character constants
DOT = chr(0xA1)
WHITESPACE = chr(0x02)

# Line Addresses.
LINE = [0x00, 0x40, 0x14, 0x54]  # for 20x4 display

# Max 8 custom char
digits = [
    [0x01, 0x03, 0x03, 0x07, 0x07, 0x0F, 0x0F, 0x1F],  # lower-rt triangle
    [0x10, 0x18, 0x18, 0x1C, 0x1C, 0x1E, 0x1E, 0x1F],  # lower-lf triangle
    [0x1F, 0x0F, 0x0F, 0x07, 0x07, 0x03, 0x03, 0x01],  # upper-rt triangle
    [0x1F, 0x1E, 0x1E, 0x1C, 0x1C, 0x18, 0x18, 0x10],  # upper-lf triangle
    [0x00, 0x00, 0x00, 0x00, 0x1F, 0x1F, 0x1F, 0x1F],  # lower horiz bar
    [0x1F, 0x1F, 0x1F, 0x1F, 0x00, 0x00, 0x00, 0x00],  # upper horiz bar
    [0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F],  # solid block
    [0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F],  # solid block with first col blank
]

'''
Table order (4x3 matrix)

Each element below is the index of each list in digits. E.g. 3 means digits[3]

0   1   2
3   4   5
6   7   8
9   10  11
'''

bigDigit = [
    [0x00, 0x06, 0x01, 0x06, 0x20, 0x06, 0x06, 0x20, 0x06, 0x02, 0x06, 0x03],  # 0
    [0x20, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06, 0x20],  # 1
    [0x00, 0x06, 0x01, 0x20, 0x00, 0x03, 0x00, 0x03, 0x20, 0x06, 0x06, 0x06],  # 2
    [0x00, 0x06, 0x01, 0x20, 0x20, 0x06, 0x20, 0x05, 0x06, 0x02, 0x06, 0x03],  # 3
    [0x06, 0x20, 0x06, 0x06, 0x06, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06],  # 4
    [0x06, 0x06, 0x06, 0x06, 0x04, 0x04, 0x20, 0x20, 0x06, 0x06, 0x06, 0x03],  # 5
    [0x00, 0x06, 0x01, 0x06, 0x20, 0x20, 0x06, 0x05, 0x01, 0x02, 0x06, 0x03],  # 6
    [0x06, 0x06, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06],  # 7
    [0x00, 0x06, 0x01, 0x06, 0x20, 0x06, 0x06, 0x05, 0x06, 0x02, 0x06, 0x03],  # 8
    [0x00, 0x06, 0x01, 0x02, 0x04, 0x06, 0x20, 0x20, 0x06, 0x20, 0x20, 0x06]  # 9
]

bigKg = [
    [0x06, 0x20, 0x03, 0x06, 0x03, 0x20, 0x06, 0x01, 0x20, 0x06, 0x20, 0x01],  #K
    [0x07, 0x06, 0x06, 0x07, 0x20, 0x20, 0x07, 0x00, 0x06, 0x07, 0x06, 0x06]  #G
]


########################################################################
#
# Low-level routines for configuring the LCD module.
# These routines contain GPIO read/write calls.
#
def init_io():
    # Sets GPIO pins to input & output, as required by LCD board
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for lcdLine in OUTPUTS:
        GPIO.setup(lcdLine, GPIO.OUT)


def pulse_enable_line():
    # Pulse the LCD Enable line; used for clocking in data
    GPIO.output(LCD_E, GPIO.HIGH)  # pulse E high
    GPIO.output(LCD_E, GPIO.LOW)  # return E low


def send_nibble(data):
    # sends upper 4 bits of data byte to LCD data pins D4-D7
    GPIO.output(LCD_D4, bool(data & 0x10))
    GPIO.output(LCD_D5, bool(data & 0x20))
    GPIO.output(LCD_D6, bool(data & 0x40))
    GPIO.output(LCD_D7, bool(data & 0x80))


def send_byte(data, charMode=False):
    # send one byte to LCD controller
    GPIO.output(LCD_RS, charMode)  # set mode: command vs. char
    send_nibble(data)  # send upper bits first
    pulse_enable_line()  # pulse the enable line
    data = (data & 0x0F) << 4  # shift 4 bits to left
    send_nibble(data)  # send lower bits now
    pulse_enable_line()  # pulse the enable line


########################################################################
#
# Higher-level routines for diplaying data on the LCD.
#
def clear_display():
    # This command requires 1.5mS processing time, so delay is needed
    send_byte(CLEAR_DISPLAY)
    time.sleep(0.0015)  # delay for 1.5mS


def cursor_on():
    send_byte(CURSOR_ON)


def cursor_off():
    send_byte(CURSOR_OFF)


def cursor_blink():
    send_byte(CURSOR_BLINK)


def cursor_left():
    send_byte(CURSOR_LEFT)


def cursor_right():
    send_byte(CURSOR_RIGHT)


def reset_display():
    # This command requires 1.5mS processing time, so delay is needed
    send_byte(RETURN_HOME)
    time.sleep(0.0015)  # delay for 1.5mS


def init_lcd():
    # initialize the LCD controller & clear display
    send_byte(0x33)  # initialize
    send_byte(0x32)  # initialize/4-bit
    send_byte(0x28)  # 4-bit, 2 lines, 5x8 font
    send_byte(LEFT_TO_RIGHT)  # rightward moving cursor
    cursor_off()
    reset_display()
    clear_display()


def send_char(ch):
    send_byte(ord(ch), True)


def show_message(string):
    # Send string of characters to display at current cursor position
    for character in string:
        send_char(character)


def go_to_line(row):
    # Moves cursor to the given row
    # Expects row values 0-1 for 16x2 display; 0-3 for 20x4 display
    addr = LINE[row]
    send_byte(SET_CURSOR + addr)


def go_to_x_y(row, col):
    # Moves cursor to the given row & column
    # Expects col values 0-19 and row values 0-3 for a 20x4 display
    addr = LINE[row] + col
    send_byte(SET_CURSOR + addr)


########################################################################
#
# BIG CLOCK & Custom character generation routines
#
def load_custom_symbol(addr, data):
    # saves custom character data at given char-gen address
    # data is a list of 8 bytes that specify the 5x8 character
    # each byte contains 5 column bits (b5,b4,..b0)
    # each byte corresponds to a horizontal row of the character
    # possible address values are 0-7
    cmd = LOAD_SYMBOL + (addr << 3)
    send_byte(cmd)
    for byte in data:
        send_byte(byte, True)


def load_symbol_block(data):
    # loads a list of symbols into the chargen RAM, starting at addr 0x00
    for i in range(len(data)):
        load_custom_symbol(i, data[i])


def show_big_digit(symbol, startCol):
    # displays a 4-row-high digit at specified column
    for row in range(4):
        go_to_x_y(row, startCol)
        for col in range(3):
            index = row * 3 + col
            send_byte(symbol[index], True)


def show_period(col):
    # displays a period '.' at specified column
    go_to_x_y(3, col)
    send_char(DOT)


def show_kg():
    # displays 'kg' at specified column
    pos = [14, 17]
    for i in range(len(bigKg)):
        symbols = bigKg[i]
        show_big_digit(symbols, pos[i])


def display_weight(weight):
    # displays large digit weight on 20x4 LCD
    # Note: format for weight is in kg to 4 s.f. without the decimal point
    load_symbol_block(digits)
    pos = [0, 3, 6, 10]
    clear_display()
    show_period(9)
    if weight < 10:
        w_str = "  {:02}".format(weight)
    else:
        w_str = "{:>4}".format(weight)
    for i in range(len(w_str)):
        if w_str[i].isdigit():
            value = int(w_str[i])
            symbols = bigDigit[value]
            show_big_digit(symbols, pos[i])
        else:
            send_char(WHITESPACE)
    show_kg()
    time.sleep(1)


########################################################################
#
# Main Program
#
print("Pi LCD4 program starting.")
init_io()  # Initialization
init_lcd()
clear_display()
display_weight(1234)
time.sleep(1)
display_weight(235)
time.sleep(1)
display_weight(23)
time.sleep(1)
display_weight(3)


# END #############################################################
