#!/usr/bin/python2
"""Minimalist FSK modulation example.

Setup a triangular wave that alternates between 1Khz and 2Khz each second
"""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.set(channel=0, wave='tri', freq_hz=1000, enable=True)
fy.set(channel=1, wave='square', freq_uhz=500000, enable=True)
fy.set_modulation(fygen.MODULATION_FSK, fygen.TRIGGER_CH2, hop_freq_hz=2000)
