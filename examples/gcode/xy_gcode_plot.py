#!/usr/bin/env python3
"""Can read a simple form of GCode and create an XY plot.

See the gcode/ subdir for example files.

Example usage:

  ./xy_gcode_plot.py cat.gcd
"""

import argparse
import math
import sys
import six

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen

PARSER = argparse.ArgumentParser(
    description='Create an XY plot from a gcode file.')

PARSER.add_argument(
    'filename',
    help='Pathname to gcode file.')

PARSER.add_argument(
    '--dry_run',
    help='Print commands to stdout instead of a real device',
    action='store_true')

PARSER.add_argument(
    '--debug_level',
    help='Debug Level (0, 1, 2)',
    type=int,
    default=1)

PARSER.add_argument(
    '--freq_hz',
    help='XY frequency',
    type=int,
    default=1000)

PARSER.add_argument(
    '--xarb',
    help='Arb index for X data',
    type=int,
    default=1)

PARSER.add_argument(
    '--yarb',
    help='Arb index for Y data',
    type=int,
    default=2)

PARSER.add_argument(
    '--xchannel',
    help='Channel to use for X data (0 or 1).  Y channel will use the other '
         'channel',
    type=int,
    default=0)

PARSER.add_argument(
    '--volts',
    help='Max voltage to set.',
    type=float,
    default=6.0)

PARSER.add_argument(
    '--data_length',
    help='Data length to send to siggen.',
    type=int,
    default=8192)


ARGS = PARSER.parse_args()

def parse_gcode_line(line):
  """Convert a line of gcode into a dict."""

  if ';' in line:
    line = line.split(';')[0]  # remove comment

  d = {}
  for token in line.split():
    if len(token) < 2:
      continue
    token = token.upper()
    d[token[0]] = float(token[1:])

  return d

def read_gcode(fin):
  """Reads a gcode file and extracts points.

  Input is a file object.  Output is a list of (x, y, pen_down) coordinates
  """

  # current state.  A GCode line does not have to specify X Y and Z,
  # non-specified parameters are considered "unchanged"
  x = 0
  y = 0
  pen_down = True
  new_pen_down = False
  data = []

  # no strict parsing here.  Just do what we can
  for line in fin:
    d = parse_gcode_line(line)

    if 'G' not in d:
      continue

    # Only support G01 commands.  Ignore everything else.
    if int(d['G']) != 1:
      continue

    if 'Z' in d:
      new_pen_down = int(d['Z']) == 0

    if 'X' in d:
      x = d['X']

    if 'Y' in d:
      y = d['Y']

    # The "if" here to avoid multiple pen up movements in a sequence.  It also
    # keeps pen up movements at the start and end of the file off the list
    if new_pen_down or pen_down:
      data.append((x, y, new_pen_down))

    pen_down = new_pen_down

  # remove pen_up events at the end
  while not data[-1][2]:
    del data[-1]

  return data

def bound_coordinates(data):
  """Determines bondaries from a list of (x,y,pen_down) coordinates."""

  xmin = None
  ymin = None
  xmax = None
  ymax = None

  for p in data:
    x, y, _ = p

    if xmin is None or x < xmin:
      xmin = x

    if xmax is None or x > xmax:
      xmax = x

    if ymin is None or y < ymin:
      ymin = y

    if ymax is None or y > ymax:
      ymax = y

  return xmin, ymin, xmax, ymax


def interpolate(data):
  """Adds extra points between longer gaps.

  Without interpolation, longer lines will not get their fair share of presense
  in the waveform and thus will appear as faint jumps on the final XY plot.

  With interpolation, it possible we may end up with > DATA_LENGTH (8192)
  points.  This function does not take on that concern and happily creates
  > DATA_LENGTH points if a lot of data is given.

  THhs function does concern itself with too few lines though and will always
  create at least DATA_LENGTH points, even if only a single line segment was
  provided.
  """

  length = calc_length(data)
  segment_size = length / ARGS.data_length

  print('length=%s  segment_size=%s' % (length, segment_size))

  datai = (p for p in data)
  x1, y1, pen_down = six.next(datai)
  new_data = [(x1, y1, pen_down)]

  for p in datai:
    x2, y2, pen_down = p
    if pen_down:
      new_data.extend(interpolate_segment(x1, y1, x2, y2, segment_size))
    else:
      # always add this point
      new_data.append((x2, y2, False))
    x1 = x2
    y1 = y2

  return new_data

def interpolate_segment(x1, y1, x2, y2, segment_size):
  """If the length of the segment is less than segment_size, returns [(x2, y2)].

  Otherwise, generates interpolated points from x1, y1 to x2, y2."""
  dx = x2 - x1
  dy = y2 - y1
  length = math.sqrt(dx * dx + dy * dy)

  if length > 0:
    x_step = dx / length * segment_size
    y_step = dy / length * segment_size

  data = []
  while length >= segment_size:
    x1 += x_step
    y1 += y_step
    data.append((x1, y1, True))
    length -= segment_size

  data.append((x2, y2, True))
  return data

def calc_length(data):
  """Determines the line length of the entire drawing."""
  length = 0.0

  datai = (p for p in data)
  x1, y1, _ = six.next(datai)

  for p in datai:
    x2, y2, pen_down = p
    if pen_down:
      dx = x2 - x1
      dy = y2 - y1
      length += math.sqrt(dx * dx + dy * dy)
    x1 = x2
    y1 = y2

  return length

def reduce(data, points_to_remove):
  """Remove points_to_remove segments.

  The segments removed were the shortest found in the original data.  removal
  feedback is not accounted for so removing a large number of points can lead
  to non-optimal selection."""
  print('Reducing %d points down to %d points' %
        (len(data), len(data) - points_to_remove))
  # create a list to qualifying indexes of the form (length, index)
  lengths = []

  # iteration 1, calc points that are bookended by pen down points
  # eg, if we have the points P1F, P2T, P3T, P4T, P5T, P6F  where T/F are
  # pen_down, P3 and P4 are added for consideration.  P1, P2, P5 and P6 are not
  # because they are edge boundaries.

  for idx in range(1, len(data) - 1):
    if not data[idx - 1][2] or not data[idx][2] or not data[idx + 1][2]:
      # pen is up before, on or after this point, so don't consider it
      continue
    x1, y1, _ = data[idx - 1]
    x2, y2, _ = data[idx]
    x3, y3, _ = data[idx + 1]

    length = min(line_length(x1, y1, x2, y2), line_length(x2, y2, x3, y3))
    lengths.append((length, idx))

  # iteration 2, find patterns of the form
  # P1F, P2T, P3T, P4F, then add the P2->P3 length and P2, P3 for
  # consideration
  pen_down_sequence_len = 0
  # pylint: disable=consider-using-enumerate
  for idx in range(len(data)):
    if data[idx][2]:
      pen_down_sequence_len += 1  # tracking the number of pen_down events
    else:
      if pen_down_sequence_len == 2:  # only trigger if there were two
        x1, y1, _ = data[idx - 2]  # 1 and two back are the pen_down events
        x2, y2, _ = data[idx - 1]
        # Add this pen up event, along with the previous pen down events
        # All three need to be removed or we will end up with back to back
        # pen up events.  Also note the reverse order which is needed
        # for clean removal.
        lengths.append((line_length(x1, y1, x2, y2), idx, idx - 1, idx - 2))

      pen_down_sequence_len = 0
  # pylint: enable=consider-using-enumerate

  # sort by length and cull
  lengths.sort()
  lengths = lengths[:points_to_remove]
  # now reverse sort by index so that we can remove points without invalidating
  # indexes
  lengths.sort(key=lambda p: -p[1])

  # start deleting points
  for sequence in lengths:
    for idx in sequence[1:]:
      del data[idx]

def line_length(x1, y1, x2, y2):
  """Calculates the length of a line."""
  dx = x2 - x1
  dy = y2 - y1
  return math.sqrt(dx * dx + dy * dy)

def main():
  """Program entry point."""
  with open(ARGS.filename) as fin:
    data = read_gcode(fin)

  # add points along longer lines
  data = interpolate(data)

  # reduce size until its correct.
  # This is a non-trivial problem.  To keep detail, we remove the
  # points that are closest to one another.  But removing a point affects the
  # distance calculation on the point before and after it.  Thus we have
  # options:
  #
  # Remove one point at a time.  This will be slow O(n*n) but is simple
  #
  # Create a data structure that can quickly recalculate and reprioritize
  # the lengths of points that neighbor a removed one.  This is complex and
  # likely to be buggy.
  #
  # Remove n points at a time.  One of these n points might be a bad choice
  # but the closer the point is to the shortest, the less likely it would have
  # survived the final culling anyway.
  #
  # We go for the last option, removing 1/10 of the needed points each iteration
  while len(data) > ARGS.data_length:
    points_to_remove = int((len(data) - ARGS.data_length) / 10)
    if points_to_remove < 1:
      points_to_remove = 1
    reduce(data, points_to_remove)

  # It's also poosible that data is a bit too short, usually just a single point
  # The "solution" is to duplicate the final point
  if len(data) < ARGS.data_length:
    print('Extending data from %d -> %d points' % (len(data), ARGS.data_length))
  while len(data) < ARGS.data_length:
    data.append(data[-1])

  xmin, ymin, xmax, ymax = bound_coordinates(data)

  print('len(data)=%u, xmin=%s  xmax=%s  ymin=%s  ymax=%s' %
        (len(data), xmin, xmax, ymin, ymax))

  if ARGS.dry_run:
    fy = fygen.FYGen(port=sys.stdout, debug_level=ARGS.debug_level)
  else:
    fy = fygen.FYGen(debug_level=ARGS.debug_level)

  fy.set((0, 1), volts=ARGS.volts, freq_hz=ARGS.freq_hz)
  fy.set_waveform(
      ARGS.xarb, values=[x for x, _, _ in data], min_value=xmin, max_value=xmax)
  fy.set_waveform(
      ARGS.yarb, values=[y for _, y, _ in data], min_value=ymin, max_value=ymax)
  fy.set(
      0,
      wave='arb%d' % ARGS.xarb,
      enable=True)
  fy.set(
      1 - ARGS.xchannel,
      wave='arb%d' % ARGS.yarb,
      enable=True)

  print('done')

if __name__ == '__main__':
  main()
