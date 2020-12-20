#!/usr/bin/python2
"""Minimalist burst example.

This one sets up a 10Khz sin wave that is triggered by a 1Khz square wave.
For each trigger, 3 sin wave cycles are produced.
"""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.set(channel=0, wave='sin', freq_hz=10000, enable=True)
fy.set(channel=1, wave='square', freq_hz=1000, enable=True)
fy.set_modulation(fygen.MODULATION_BURST, fygen.TRIGGER_CH2, 3)
