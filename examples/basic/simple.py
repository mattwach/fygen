#!/usr/bin/python
"""Minimalist example that shows a sin wave being configured."""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.set(channel=0, wave='square', freq_hz=1000, volts=3, enable=True)
