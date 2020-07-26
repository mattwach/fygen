#!/usr/bin/python
"""Minimalist PSK modulation example.

Setup a 1kz CMOS wave that changes inverts at 100hz
"""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.set(channel=0, wave='cmos', freq_hz=1000, volts=2.5, enable=True)
fy.set(channel=1, wave='square', freq_hz=100, volts=3, enable=True)
fy.set_modulation(fygen.MODULATION_PSK, fygen.TRIGGER_CH2)
