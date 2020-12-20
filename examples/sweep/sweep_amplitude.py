#!/usr/bin/python2
"""Minimalist sweep example that sweeps between 3.3 and 5V."""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.set(0, wave='square', freq_hz=1000, enable=True)
fy.set_sweep(
    mode=fygen.SWEEP_AMPLITUDE,
    start_volts=3.3,
    end_volts=5,
    time_seconds=2)

print('Please presss the adjustment knob on the signal generator to '
      'begin the sweep')
