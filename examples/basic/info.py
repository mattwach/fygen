#!/usr/bin/python2
"""Get miscellaneous information"""

import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

fy = fygen.FYGen()

def output(title, data):
  """Formats output."""
  print('--- %s ---' % title)
  for k, v in sorted(data.iteritems()):
    print('  %15s: %s' % (k, v))

output('Device Info', {
    'device_id': fy.get_id(),
    'model': fy.get_model(),
    'buzzer': fy.get_buzzer()})

output('Uplink Status', fy.get_uplink())

output('Synchronization', fy.get_synchronization())
