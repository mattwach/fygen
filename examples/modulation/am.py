#!/usr/bin/python2
"""Minimalist AM modulation example.

Setup a 2kz sin wave that is modulated by a 150hz triangle wave
"""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.set(channel=0, wave='sin', freq_hz=2000, enable=True)
fy.set(channel=1, wave='tri', freq_hz=150, enable=True)
fy.set_modulation(
    fygen.MODULATION_AM,
    fygen.TRIGGER_CH2,
    am_attenuation=0.9)
