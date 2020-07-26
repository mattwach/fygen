#!/usr/bin/python
"""Minimalist example that should a custom waveform being programmed.

The waveform generated here is a simple stairstep.
"""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)

fy.set_waveform(1, values=[n / 8192.0 for n in range(8192)])
fy.set(channel=0, wave='arb1', freq_hz=1000, volts=3, enable=True)
