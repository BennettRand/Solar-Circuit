# -*- coding: utf-8 -*-

# Python module: Some functions for modbus data mangling

import struct

###############
# bits function
###############

def get_bits_from_int(val_int, val_size=16):
    """Get the list of bits of val_int integer (default size is 16 bits)

        Return bits list, least significant bit first. Use list.reverse() if
        need.

        :param val_int: integer value
        :type val_int: int
        :param val_size: bit size of integer (word = 16, long = 32) (optional)
        :type val_size: int
        :returns: list of boolean "bits" (least significant first)
        :rtype: list
    """
    # allocate a bit_nb size list
    bits = [None] * val_size
    # fill bits list with bit items
    for i, item in enumerate(bits):
        bits[i] = bool((val_int>>i)&0x01)
    # return bits list
    return bits

#########################
# floating-point function
#########################

def decode_ieee(val_int):
    """Decode Python int (32 bits integer) as an IEEE single precision format

        Support NaN.

        :param val_int: a 32 bit integer as an int Python value
        :type val_int: int
        :returns: float result
        :rtype: float
    """
    return struct.unpack("f",struct.pack("I", val_int))[0]

def encode_ieee(val_float):
    """Encode Python float to int (32 bits integer) as an IEEE single precision

        Support NaN.

        :param val_float: float value to convert
        :type val_float: float
        :returns: IEEE 32 bits (single precision) as Python int
        :rtype: int
    """
    return struct.unpack("I",struct.pack("f", val_float))[0]

################################
# long format (32 bits) function
################################

def word_list_to_long(val_list, big_endian=True):
    """Word list (16 bits int) to long list (32 bits int)

        By default word_list2long() use big endian order. For use little endian, set
        big_endian param to False.

        :param val_list: list of 16 bits int value
        :type val_list: list
        :param big_endian: True for big endian/False for little (optional)
        :type big_endian: bool
        :returns: 2's complement result
        :rtype: list
    """
    # allocate list for long int
    long_list = [None] * int(len(val_list)/2)
    # fill registers list with register items
    for i, item in enumerate(long_list):
        if big_endian:
            long_list[i] = (val_list[i*2]<<16) + val_list[(i*2)+1]
        else:
            long_list[i] = (val_list[(i*2)+1]<<16) + val_list[i*2]
    # return long list
    return long_list

#########################################################
# 2's complement of int value (scalar and list) functions
#########################################################

def get_2comp(val_int, val_size=16):
    """Get the 2's complement of Python int val_int

        :param val_int: int value to apply 2's complement
        :type val_int: int
        :param val_size: bit size of int value (word = 16, long = 32) (optional)
        :type val_size: int
        :returns: 2's complement result
        :rtype: int
    """
    # test MSBit (1 for negative)
    if (val_int&(1<<(val_size-1))):
        # do complement
        val_int = val_int - (1<<val_size)
    return val_int

def get_list_2comp(val_list, val_size=16):
    """Get the 2's complement of Python list val_list

        :param val_list: list of int value to apply 2's complement
        :type val_list: list
        :param val_size: bit size of int value (word = 16, long = 32) (optional)
        :type val_size: int
        :returns: 2's complement result
        :rtype: list
    """
    return [get_2comp(val, val_size) for val in val_list]
