#!/usr/bin/env python

"""Cycles though all avaliable waves."""

import argparse
import sys

import six

sys.path.append('../..')

# pylint: disable=wrong-import-position
import fygen
import wavedef

PARSER = argparse.ArgumentParser(
    description='Cycle through all available waves for a given device')

PARSER.add_argument(
    '--port',
    help='Select connection port',
    type=str,
)

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
    '--include_arbitrary',
    help='Include arbitrary functions',
    action='store_true')

PARSER.add_argument(
    '--device',
    help='Select signal generator type',
    type=str,
)

PARSER.add_argument(
    '--test_mode',
    help='No delays or prompts',
    action='store_true')

ARGS = PARSER.parse_args()


def show_waves(fy, c):
  """Show waves for a given channel."""
  fy.set(channel=1-c, wave='sin')
  waves = wavedef.get_valid_list(fy.device_name, c)

  if not ARGS.include_arbitrary:
    waves = list(w for w in waves if not w.startswith('arb'))

  for n, wave in enumerate(waves):
    fy.set(channel=c, wave=wave)
    if not ARGS.test_mode:
      six.moves.input('%d/%d  Channel %d, %s (Press Enter To Continue)' %
                      (n, len(waves), c, wavedef.get_description(wave)))

def main():
  """Main function."""
  # Sanitize arguments and inject arguments defined in the environment.
  if ARGS.port is None:
    ARGS.port = os.environ.get("FYPORT")
  if ARGS.device is None:
    ARGS.device = os.environ.get("FYDEVICE")
  if ARGS.device is not None:
    ARGS.device = ARGS.device.lower()
  # Open FYGen.
  if ARGS.dry_run:
    fy = fygen.FYGen(port=sys.stdout, device_name=ARGS.device)
  else:
    fy = fygen.FYGen(serial_path=ARGS.port,
      debug_level=ARGS.debug_level, device_name=ARGS.device)
  # Run.
  fy.set(0, freq_hz=10000, volts=2, offset_volts=2, enable=True)
  fy.set(1, freq_hz=10000, volts=2, offset_volts=-2, enable=True)
  show_waves(fy, 0)
  show_waves(fy, 1)
  fy.set(channel=(0, 1), enable=False)
  print("Done!")

if __name__ == '__main__':
  main()
