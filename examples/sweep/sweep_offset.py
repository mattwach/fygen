#!/usr/bin/python
"""Minimalist sweep example that changes the offset between -1 and 1 volts."""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.set(0, wave='square', freq_hz=1000, volts=4, enable=True)
fy.set_sweep(
    mode=fygen.SWEEP_OFFSET,
    start_offset_volts=-1,
    end_offset_volts=1,
    time_seconds=1.5)

print('Please presss the adjustment knob on the signal generator to '
      'begin the sweep')
print('-- PLEASE VERIFY VOLTAGES --')
