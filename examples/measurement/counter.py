#!/usr/bin/python2
"""Minimalist example that shows a sin wave being configured."""

import sys
import time

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen()
fy.get_measurement('counter')  # get into the correct mode
fy.set_measurement(reset_counter=True)
print('Counting for 10 seconds...')
time.sleep(10)
print('Count is %u' % fy.get_measurement('counter'))

