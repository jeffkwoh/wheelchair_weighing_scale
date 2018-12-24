#!/usr/bin/env python3
import serial


class SerialNfc:

    def __init__(self, port, baudrate=9600):
        self._ser = serial.Serial(port = port, baudrate = baudrate)

    def _read_raw(self):
        '''
        :return: None or Byte String
        '''
        if self._ser.in_waiting > 0:
            return self._ser.readline()
        else:
            return None

    def get_weight(self):
        '''
        :return: None or int
        '''
        raw = self._read_raw()
        if raw:
            weight_array = [weight for weight in raw.decode("utf-8").split() if weight[0] == ':']
            if weight_array:
                return int(weight_array[0].replace(':', ''))

        return None
