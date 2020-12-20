#!/usr/bin/python2
"""Minimalist sweep example that sweeps between 1khz and 10khz."""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.set(0, wave='sin', freq_hz=1000, enable=True)
fy.set_sweep(
    mode=fygen.SWEEP_FREQUENCY,
    start_freq_hz=1000,
    end_freq_hz=10000,
    time_seconds=10)

print('Please presss the adjustment knob on the signal generator to '
      'begin the sweep')
