########################################################################
#
# LCD4: Learning how to control an LCD module from Pi
# See w8bh.net for more information.
#
########################################################################
import RPi.GPIO as GPIO
import random
from time import sleep


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

negative_sign = [0x20, 0x20, 0x20, 0x04, 0x04, 0x04, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20]

class LcdDisplay:

    def __init__(self, rs, en, d4, d5, d6, d7):
        """
        :param pins: int
        """
        self.LCD_RS = rs
        self.LCD_E = en
        self.LCD_D4 = d4
        self.LCD_D5 = d5
        self.LCD_D6 = d6
        self.LCD_D7 = d7

        self.OUTPUTS = [self.LCD_RS, self.LCD_E, self.LCD_D4, self.LCD_D5, self.LCD_D6, self.LCD_D7]
        
    ########################################################################
    #
    # Low-level routines for configuring the LCD module.
    # These routines contain GPIO read/write calls.
    #
    def init_io(self):
        # Sets GPIO pins to input & output, as required by LCD board
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(True)
        for lcdLine in self.OUTPUTS:
            GPIO.setup(lcdLine, GPIO.OUT)


    def pulse_enable_line(self):
        # Pulse the LCD Enable line; used for clocking in data
        GPIO.output(self.LCD_E, GPIO.HIGH)  # pulse E high
        GPIO.output(self.LCD_E, GPIO.LOW)  # return E low


    def send_nibble(self, data):
        # sends upper 4 bits of data byte to LCD data pins D4-D7
        GPIO.output(self.LCD_D4, bool(data & 0x10))
        GPIO.output(self.LCD_D5, bool(data & 0x20))
        GPIO.output(self.LCD_D6, bool(data & 0x40))
        GPIO.output(self.LCD_D7, bool(data & 0x80))


    def send_byte(self, data, charMode=False):
        # send one byte to LCD controller
        GPIO.output(self.LCD_RS, charMode)  # set mode: command vs. char
        self.send_nibble(data)  # send upper bits first
        self.pulse_enable_line()  # pulse the enable line
        data = (data & 0x0F) << 4  # shift 4 bits to left
        self.send_nibble(data)  # send lower bits now
        self.pulse_enable_line()  # pulse the enable line


    ########################################################################
    #
    # Higher-level routines for diplaying data on the LCD.
    #
    def clear_display(self):
        # This command requires 1.5mS processing time, so delay is needed
        self.send_byte(CLEAR_DISPLAY)
        sleep(0.0015)  # delay for 1.5mS

    
    def display_off(self):
        self.send_byte(DISPLAY_OFF)


    def cursor_on(self):
        self.send_byte(CURSOR_ON)


    def cursor_off(self):
        self.send_byte(CURSOR_OFF)


    def cursor_blink(self):
        self.send_byte(CURSOR_BLINK)


    def cursor_left(self):
        self.send_byte(CURSOR_LEFT)


    def cursor_right(self):
        self.send_byte(CURSOR_RIGHT)


    def reset_display(self):
        # This command requires 1.5mS processing time, so delay is needed
        self.send_byte(RETURN_HOME)
        sleep(0.0015)  # delay for 1.5mS


    def init_lcd(self):
        # initialize the LCD controller & clear display
        self.send_byte(0x33)  # initialize
        self.send_byte(0x32)  # initialize/4-bit
        self.send_byte(0x28)  # 4-bit, 2 lines, 5x8 font
        self.send_byte(LEFT_TO_RIGHT)  # rightward moving cursor
        self.cursor_off()
        self.clear_display()
        self.reset_display()
       

    def send_char(self, ch):
        self.send_byte(ord(ch), True)


    def show_message(self, string):
        # Send string of characters to display at current cursor position
        for character in string:
            self.send_char(character)


    def go_to_line(self, row):
        # Moves cursor to the given row
        # Expects row values 0-1 for 16x2 display; 0-3 for 20x4 display
        addr = LINE[row]
        self.send_byte(SET_CURSOR + addr)


    def go_to_x_y(self, row, col):
        # Moves cursor to the given row & column
        # Expects col values 0-19 and row values 0-3 for a 20x4 display
        addr = LINE[row] + col
        self.send_byte(SET_CURSOR + addr)


    ########################################################################
    #
    # BIG CLOCK & Custom character generation routines
    #
    def load_custom_symbol(self, addr, data):
        # saves custom character data at given char-gen address
        # data is a list of 8 bytes that specify the 5x8 character
        # each byte contains 5 column bits (b5,b4,..b0)
        # each byte corresponds to a horizontal row of the character
        # possible address values are 0-7
        cmd = LOAD_SYMBOL + (addr << 3)
        self.send_byte(cmd)
        for byte in data:
            self.send_byte(byte, True)


    def load_symbol_block(self, data):
        # loads a list of symbols into the chargen RAM, starting at addr 0x00
        for i in range(len(data)):
            self.load_custom_symbol(i, data[i])


    def show_big_digit(self, symbol, startCol):
        # displays a 4-row-high digit at specified column
        for row in range(4):
            self.go_to_x_y(row, startCol)
            for col in range(3):
                index = row * 3 + col
                self.send_byte(symbol[index], True)


    def show_period(self, col):
        # displays a period '.' at specified column
        self.go_to_x_y(3, col)
        self.send_char(DOT)


    def show_kg(self):
        # displays 'kg' at specified column
        pos = [18, 19]
        self.go_to_x_y(0,pos[0])
        self.send_char('k')
        self.go_to_x_y(0,pos[1])
        self.send_char('g')


    def display_weight(self, weight, isNegative):
        # displays large digit weight on 20x4 LCD
        # Note: format for weight is a string in kg without decimal point
        self.load_symbol_block(digits)
        pos = [3, 6, 10, 14]
        self.clear_display()
        self.show_period(13)

        if isNegative:
            self.show_big_digit(negative_sign, 0)

        for i in range(len(weight)):
            if weight[i].isdigit():
                value = int(weight[i])
                symbols = bigDigit[value]
                self.show_big_digit(symbols, pos[i])
            else:
                continue
        self.show_kg()
        sleep(1)

