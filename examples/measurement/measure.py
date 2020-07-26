#!/usr/bin/python
"""Minimalist example that shows a sin wave being configured."""

import sys
import time

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen()
fy.get_measurement()  # get into the correct mode
time.sleep(1.5)
for k, v in fy.get_measurement().iteritems():
  print('%20s: %s' % (k, v))

