#!/usr/bin/python

# Low-level example for square wave
#
# The rough equivalent of:
#
# fy = fygen.FYGen(init_state=False, read_before_write=False)
# fy.set(wave='square', freq_hz=1000, volts=3.3, enable=True)

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.send('WMF00001000000000')   # freq_hz = 1000
fy.send('WMA3.30')  # volts = 3.3
fy.send('WMW01')  # wave = square
fy.send('WMN1')  # enable channel



