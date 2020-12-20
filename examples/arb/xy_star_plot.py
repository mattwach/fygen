#!/usr/bin/python2
"""Interpolates points to draw a star on an oscilloscope (when set to XY mode"""

import math
import sys

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

DATA_LENGTH = 8192

POINTS = [
    (0.3090, 0.9511),  # Pt 1
    (-0.8090, -0.5878),  # Pt 3
    (1.0000, 0.0000),  # Pt 5
    (-0.8090, 0.5878),  # Pt 2
    (0.3090, -0.9511),  # Pt 4
    (0.3090, 0.9511),  # Pt 1
]

def interpolate_segment(x1, y1, x2, y2, steps):
  """Create interpolated points along a line."""
  dx = x2 - x1
  dy = y2 - y1
  dx_step = dx / steps
  dy_step = dy / steps

  i = 0
  while i < steps:
    yield x1, y1
    x1 += dx_step
    y1 += dy_step
    i += 1

def interpolate(data):
  """Fills in interpolated points."""
  # first determine relative lengths for point weights
  lengths = []
  for i in range(len(data) - 1):
    j = i+1
    x1, y1 = data[i]
    x2, y2 = data[j]
    dx = x2 - x1
    dy = y2 - y1
    lengths.append(math.sqrt(dx * dx + dy * dy))

  sum_length = sum(lengths)
  step = sum_length / DATA_LENGTH
  print('lengths=%s' % lengths)

  interpolated = []
  for i in range(len(data) - 1):
    j = i+1
    x1, y1 = data[i]
    x2, y2 = data[j]
    interpolated.extend(
        interpolate_segment(x1, y1, x2, y2, int(lengths[i] / step)))

  return interpolated

def pad(data):
  """Ensures the data length is correct."""
  if len(data) == DATA_LENGTH:
    print('data is %d points' % DATA_LENGTH)
    return data

  if len(data) > DATA_LENGTH:
    print('Trim data from %d points to %d' % (len(data), DATA_LENGTH))
    return data[:DATA_LENGTH]

  print('Extend data from %d points to %d' % (len(data), DATA_LENGTH))
  while len(data) < DATA_LENGTH:
    data.append(data[-1])
  return data

def main():
  """Main entry point."""
  data = pad(interpolate(POINTS))

  fy = fygen.FYGen(debug_level=1)
  fy.set((0, 1))
  fy.set_waveform(1, values=[x for x, _ in data])
  fy.set_waveform(2, values=[y for _, y in data])
  fy.set(0, freq_hz=10000, volts=6, wave='arb1', enable=True)
  fy.set(1, freq_hz=10000, volts=6, wave='arb2', enable=True)

  print('done')

if __name__ == '__main__':
  main()
