#!/usr/bin/env python3
import serial
from .tag_data import TagData


class SerialNfc:
    UPDATE_PATIENT_WEIGHT_DELIMITER = '@'

    def __init__(self, port, baudrate=9600):
        self._ser = serial.Serial(port=port, baudrate=baudrate)

    def close(self):
        self._ser.close()

    def _read_raw(self):
        """
        :return: None or Byte String
        """
        if self._ser.in_waiting > 0:
            return self._ser.readline()
        else:
            return None

    def _is_prefixed_by(self, string, prefix):
        """
        :param string: Formatted string (not a byte string)
        :param prefix: Can be a one character, or multiple characters (in a String)
        :return: True if string is prefixed by given prefix
        """
        return isinstance(string, str) and len(string) > 0 and isinstance(prefix, str) and string[0] == prefix

    def _is_wheelchair_weight(self, string):
        """
        :param string: Formatted string (not a byte string)
        :return: True if string represents wheelchair weight (prefixed by :), else False
        """
        return self._is_prefixed_by(string, ':')

    def get_weight(self):
        """
        :return: None or TagData
        """
        raw = self._read_raw()

        return self._parse(raw)

    def update_patient_weight(self, value):
        if not (isinstance(value, int) or isinstance(value, float)):
            return False
        to_write = SerialNfc.UPDATE_PATIENT_WEIGHT_DELIMITER + str(value) \
                   + SerialNfc.UPDATE_PATIENT_WEIGHT_DELIMITER

        try:
            self._ser.write(to_write.encode('utf-8'))
            return True
        except (SerialTimeoutException):
            return False

    def write_wheelchair_weight(self, value):
        if not (isinstance(value, int) or isinstance(value, float)):
            return False
        to_write = '!' + str(value) + '!'
        try:
            self._ser.write(to_write.encode('utf-8'))
            return True
        except (SerialTimeoutException):
            return False

    def _parse(self, byte_string):
        """
        :param byte_string: byte
        :return: TagData
        """
        # Return none if an invalid byte_string is passed
        if byte_string is None or not isinstance(byte_string, bytes):
            return None

        try:
            # \x02, start of line control character is replaced
            string_arr = byte_string.decode("utf-8").replace("\x02", "").split()  # May have decode errors
        except UnicodeDecodeError:
            print("Unicode Decode Error")
            return None

        print(string_arr)
        # There should only be one wheelchair_weight (TODO: needs assertion)
        wheelchair_weight = ([float(w.replace(':', ''))
                              for w in string_arr
                              if self._is_wheelchair_weight(w)]
                             + [None])[0]
        # order is preserved
        weight_history = [float(w.replace('^', ''))
                          for w in string_arr
                          if self._is_prefixed_by(w, '^')]

        # Return none if byte_string does not represent a valid tag
        if wheelchair_weight is None:
            return None

        # {wheelchair_weight is not None, weight_history can be []}
        return TagData(wheelchair_weight, weight_history)
