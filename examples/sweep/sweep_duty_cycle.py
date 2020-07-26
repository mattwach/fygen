#!/usr/bin/python
"""Minimalist sweep example that changes the duty cycle between 0.1 and 0.9."""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen(debug_level=1)
fy.set(0, wave='square', freq_hz=1000, enable=True)
fy.set_sweep(
    mode=fygen.SWEEP_DUTY_CYCLE,
    start_duty_cycle=0.1,
    end_duty_cycle=0.9,
    time_seconds=2)

print('Please presss the adjustment knob on the signal generator to '
      'begin the sweep')
