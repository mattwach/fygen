#!/usr/bin/python2
"""Minimalist PM modulation example.

Setup a 1kz sin wave that is modulated by a 500hz square wave
"""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.set(channel=0, wave='sin', freq_hz=1000, enable=True)
fy.set(channel=1, wave='square', freq_hz=500, enable=True)
fy.set_modulation(
    fygen.MODULATION_PM,
    fygen.TRIGGER_CH2,
    pm_bias_degrees=90.0)
