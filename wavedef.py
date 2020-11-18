"""Waveform mappings for various devices."""

import sys
import six

class Error(Exception):
  """Base error class."""

class InvalidChannelError(Error):
  """An invalid channel was passed."""

class InvalidMappingError(Error):
  """Internal error with mapping syntax."""

class InvalidNameError(Error):
  """Invalid name was used."""

class InvalidWaveformError(Error):
  """Invalid waveform was passed."""

class InvalidWaveformIdError(Error):
  """Invalid waveform Id was passed."""

class UnsupportedDeviceError(Error):
  """Unknown device was passed."""

# If your device is not in SUPPORTED_DEVICES you can pick one and it might
# mostly work anyway.
SUPPORTED_DEVICES = set((
    'fy2300',
    'fy6600',
    'fy6800',
    'fy6900',
))

# For consistency and better descriptions, all waveform names must be
# constructed from a combination of the following tokens, separated by dashes.
_REPLACE_CODES = {
    'adj': 'Adjustable',
    'am': 'AM',
    'chirp': 'Chirp',
    'cmos': 'CMOS',
    'dc': 'DC',
    'ecg': 'ECG',
    'exp': 'Exponential',
    'fall': 'Falling',
    'full': 'Full',
    'fm': 'FM',
    'gauss': 'Gauss White Noise',
    'half': 'Half',
    'impulse': 'Impulse',
    'log': 'Logarithm',
    'lorentz': 'Lorentz Pulse',
    'multitone': 'Multitone',
    'neg': 'Negative',
    'pulse': 'Pulse',
    'ramp': 'Ramp',
    'rand': 'Random',
    'rectangle': 'Rectangle',
    'stair': 'Stairstep',
    'sin': 'Sin',
    'sinc': 'Sinc Pulse',
    'square': 'Square',
    'trap': 'Trapezoidal Pulse',
    'tra': 'Trapezoid',
    'tri': 'Triangle',
    'wav': 'Wave',
}

# pylint: disable=too-few-public-methods
class WaveformDef(object):
  """Define a waveform."""
  def __init__(self, name, mappings):
    """Define a waveform.

    Waveform id mapping tend to vary by device and can even vary by
    device/channel combination Thus we need a mapping to describe things.

    The mapping is a dict of {id_str: id}

    id is an integer value
    id_str takes on one of the following forms.  These forms are tried in order
    and the first match is taken:
      - "device:channel", match device and channel,  Example: "fy2300:0"
      - "device:", match device,  Example "fy2300:"
      - ":channel", match channel for all devices,  Example ":0"
      - ":", match all devices and channels,  Example ""

    Args:
      name: Name that will be used in code.  Must consist of the replace_codes
        (defined below) separated by dashes
      description: An optional longer description
      mappings: Channel mappings, see above
    """
    self.name = name

    new_words = []
    for word in name.split('-'):
      if word.startswith('arb'):
        new_words.append('Arbitrary Waveform %s' % word[3:])
      elif word in _REPLACE_CODES:
        new_words.append(_REPLACE_CODES[word])
      else:
        raise InvalidNameError(
            'Waveform name ("%s") must consist of REPLACE_CODES '
            'separated by dashes' %
            name
        )

    self.description = ' '.join(new_words)

    # Do some validation of the mappings
    for map_name, val in six.iteritems(mappings):
      if map_name.count(':') != 1:
        raise InvalidMappingError(
            'mapping does not contain a single ":": %s' % map_name)

      device_name, channel = map_name.split(':')

      if channel not in ('', '0', '1'):
        raise InvalidMappingError(
            'mapping does not end with a valid channel: %s' % map_name)

      if device_name and device_name not in SUPPORTED_DEVICES:
        raise InvalidMappingError(
            'Device name not in SUPPORTED_DEVICES: %s' % map_name)

      if not isinstance(val, int):
        raise InvalidMappingError(
            'mapping value is not an int: %s -> %s' % (map_name, val))
      if val < 0:
        raise InvalidMappingError(
            'mapping value < 0: %s -> %s' % (map_name, val))
      if val > 99:
        raise InvalidMappingError(
            'mapping value > 99: %s -> %s' % (map_name, val))
    self.mappings = mappings
# pylint: enable=too-few-public-methods

_WAVEFORMS = {
    'sin': {':': 0},
    'square': {':': 1},
    'cmos': {':': 2, 'fy6900:': 4},
    'adj-pulse': {':0': 3, 'fy6900:0': 5},
    'dc': {':0': 4, ':1': 3, 'fy6900:0': 6, 'fy6900:1': 5},
    'tri': {':0': 5, ':1': 4, 'fy6900:0': 7, 'fy6900:1': 6},
    'ramp': {':0': 6, ':1': 5, 'fy6900:0': 8, 'fy6900:1': 7},
    'neg-ramp': {':0': 7, ':1': 6, 'fy6900:0': 9, 'fy6900:1': 8},
    'stair-tri': {':0': 8, ':1': 7, 'fy6900:0': 10, 'fy6900:1': 9},
    'stair': {':0': 9, ':1': 8, 'fy6900:0': 11, 'fy6900:1': 10},
    'neg-stair': {':0': 10, ':1': 9, 'fy6900:0': 12, 'fy6900:1': 11},
    'exp': {':0': 11, ':1': 10, 'fy6900:0': 13, 'fy6900:1': 12},
    'neg-exp': {':0': 12, ':1': 11, 'fy6900:0': 14, 'fy6900:1': 13},
    'fall-exp': {':0': 13, ':1': 12, 'fy6900:0': 15, 'fy6900:1': 14},
    'neg-fall-exp': {':0': 14, ':1': 13, 'fy6900:0': 16, 'fy6900:1': 15},
    'log': {':0': 15, ':1': 14, 'fy6900:0': 17, 'fy6900:1': 16},
    'neg-log': {':0': 16, ':1': 15, 'fy6900:0': 18, 'fy6900:1': 17},
    'fall-log': {':0': 17, ':1': 16, 'fy6900:0': 19, 'fy6900:1': 18},
    'neg-fall-log': {':0': 18, ':1': 17, 'fy6900:0': 20, 'fy6900:1': 19},
    'full-wav': {':0': 19, ':1': 18, 'fy6900:0': 21, 'fy6900:1': 20},
    'neg-full-wav': {':0': 20, ':1': 19, 'fy6900:0': 22, 'fy6900:1': 21},
    'half-wav': {':0': 21, ':1': 20, 'fy6900:0': 23, 'fy6900:1': 22},
    'neg-half-wav': {':0': 22, ':1': 21, 'fy6900:0': 24, 'fy6900:1': 23},
    'lorentz': {':0': 23, ':1': 22, 'fy6900:0': 25, 'fy6900:1': 24},
    'multitone': {':0': 24, ':1': 23, 'fy6900:0': 26, 'fy6900:1': 25},
    'rand': {':0': 25, ':1': 24, 'fy6900:0': 27, 'fy6900:1': 26},
    'ecg': {':0': 26, ':1': 25, 'fy6900:0': 28, 'fy6900:1': 27},
    'trap': {':0': 27, ':1': 26, 'fy6900:0': 29, 'fy6900:1': 28},
    'sinc': {':0': 28, ':1': 27, 'fy6900:0': 30, 'fy6900:1': 29},
    'impulse': {':0': 29, ':1': 28, 'fy6900:0': 31, 'fy6900:1': 30},
    'gauss': {':0': 30, ':1': 29, 'fy6900:0': 32, 'fy6900:1': 31},
    'am': {':0': 31, ':1': 30, 'fy6900:0': 33, 'fy6900:1': 32},
    'fm': {':0': 32, ':1': 31, 'fy6900:0': 34, 'fy6900:1': 33},
    'chirp': {':0': 33, ':1': 32, 'fy6900:0': 35, 'fy6900:1': 34},
    'rectangle': {'fy6900:': 2},
    'tra': {'fy6900:': 3},
}

def _make_arb(count, start_dict):
  for arb_index in range(1, count + 1):
    _WAVEFORMS['arb%u' % arb_index] = start_dict
    # create a new dictionary will all indexes incremented by one
    start_dict = dict((k, v+1) for k, v in six.iteritems(start_dict))

# Add arb1, arb2 ... arb64
_make_arb(64, {':0': 34, ':1': 33, 'fy6900:0': 36, 'fy6900:1': 35})

def _make_waveform_defs():
  return [
      WaveformDef(name, mapping)
      for name, mapping in _WAVEFORMS.items()
  ]

_WAVEFORM_DEFS = _make_waveform_defs()


def _generate_waveform_id_dict():
  """Maps _WAVEFORM_DEFS -> _WAVEFORM_IDS.

  _WAVEFORM_IDS is a sparse map of the following keys:
    "name:device:channel" -> id
    "name:device:" -> id
    "name::channel" -> id
    "name:" -> id
  """

  data = {}

  for waveform in _WAVEFORM_DEFS:
    for key, wave_id in six.iteritems(waveform.mappings):
      data['%s:%s' % (waveform.name, key)] = wave_id

  return data

_WAVEFORM_IDS = _generate_waveform_id_dict()

def _generate_waveform_name_dict():
  """Maps _WAVEFORM_DEFS -> _WAVEFORM_NAMES.

  _WAVEFORM_NAMES is a sparse map of the following keys:
    "id:device:channel" -> name
    "id:device:" -> name
    "id::channel" -> name
    "id:" -> name
  """

  data = {}

  for waveform in _WAVEFORM_DEFS:
    for key, wave_id in six.iteritems(waveform.mappings):
      data['%s:%s' % (wave_id, key)] = waveform.name

  return data

_WAVEFORM_NAMES = _generate_waveform_name_dict()

def _generate_waveforms_by_name():
  """Maps _WAVEFORM_DEFS -> _WAVEFORMS_BY_NAME"""
  return dict((wf.name, wf) for wf in _WAVEFORM_DEFS)

_WAVEFORMS_BY_NAME = _generate_waveforms_by_name()


def get_id(device_name, name, channel):
  """Looks up a wave id.

  Args:
    device_name: A single string that indicates a device or a list of
      strings that indicate a priority list of devices.
    name: waveform name.  e.g. 'sin'
    channel: channel number
  """

  # start with the most specific, work to the most generic
  lookups = (
      '%s:%s:%d' % (name, device_name, channel),
      '%s:%s:' % (name, device_name),
      '%s::%s' % (name, channel),
      '%s::' % name,
  )

  for lookup in lookups:
    if lookup in _WAVEFORM_IDS:
      return _WAVEFORM_IDS[lookup]

  check_is_supported(device_name)

  if channel not in (0, 1):
    raise InvalidChannelError(
        'Invalid channel %d.  Please use a 0 or 1' % channel)

  raise InvalidWaveformError(
      'Invalid waveform %s for device %s, channel %d.  Available waveforms '
      'include %s' %
      (name, device_name, channel, get_valid_list(device_name, channel)))

def get_name(device_name, wave_id, channel):
  """Looks up a wave name.

  Args:
    device_name: A single string that indicates a device or a list of
      strings that indicate a priority list of devices.
    wave_id: waveform id.  e.g. 0
    channel: channel number
  """

  # start with the most specific, work to the most generic
  lookups = (
      '%s:%s:%d' % (wave_id, device_name, channel),
      '%s:%s:' % (wave_id, device_name),
      '%s::%s' % (wave_id, channel),
      '%s::' % wave_id,
  )

  for lookup in lookups:
    if lookup in _WAVEFORM_NAMES:
      return _WAVEFORM_NAMES[lookup]

  check_is_supported(device_name)

  if channel not in (0, 1):
    raise InvalidChannelError(
        'Invalid channel %d.  Please use a 0 or 1' % channel)

  raise InvalidWaveformIdError(
      'Invalid waveform id %d for device %s, channel %d.' %
      (wave_id, device_name, channel))

def check_is_supported(device_name):
  if device_name not in SUPPORTED_DEVICES:
    raise UnsupportedDeviceError(
        'Device %s is not supported.  Supported devices include %s' %
        (device_name, SUPPORTED_DEVICES))

def get_valid_list(device_name=None, channel=None):
  """Returns a list of all valid waves for a given device_name and channel.

  If device and channel are None, returns a list of all defined waveforms.
  """

  if device_name is None and channel is None:
    return sorted(_WAVEFORMS_BY_NAME)

  check_is_supported(device_name)

  def is_valid(waveform):
    """Returns true if a waveform is valid."""
    lookups = (
        '%s:%d' % (device_name, channel),
        ':%d' % channel,
        '%s:' % device_name,
        ':',
    )
    for lookup in lookups:
      if lookup in waveform.mappings:
        return True
    return False

  return sorted(wf.name for wf in _WAVEFORM_DEFS if is_valid(wf))

def get_description(waveform_name):
  """Returns a long description for a waveform name."""
  if waveform_name not in _WAVEFORMS_BY_NAME:
    raise InvalidWaveformError(
        'No such waveform: %s.  Try get_valid_list()' % waveform_name)

  return _WAVEFORMS_BY_NAME[waveform_name].description

# pylint: disable=redefined-builtin
def help(device_name=None, fout=sys.stdout, use_markdown=False):
  """Dumps a table of waveform names, along with supported devices and channels.

  Example output:

  Name       Description       Channels   Devices
  ----------------------------------------------------
  sin        Sin               all        all
  adj-pulse  Adjustable Pulse  0          fy2300, fy6800
  ...
  """
  if device_name is not None:
    check_is_supported(device_name)

  def dump_row(name, description, channel, device):
    fout.write('|%-15s|%-30s|%8s|%8s|\n' % (name, description, channel, device))

  def get_compatible(waveform):
    """
    Returns compatible devices and channels for a given waveform.
    At the moment the output would be a bit confusing if two devices
    support the same waveform but only on different channels.
    Luckily there aren't any waveforms like that yet
    """
    channel_set = set()
    device_set = set()
    for mapping in waveform.mappings:
      is_included = (
          mapping.startswith(':') or
          mapping.startswith('%s:' % device_name) or
          device_name is None
      )
      if is_included:
        device, channel = mapping.split(':')
        if not device:
          device_set = SUPPORTED_DEVICES
        else:
          device_set.add(device)

        if not channel:
          channel_set.add('0')
          channel_set.add('1')
        else:
          channel_set.add(channel)

    if not channel_set:
      return None, None

    if device_set == SUPPORTED_DEVICES:
      device_text = 'all'
    else:
      device_text = ','.join(sorted(device_set))

    channel_text = ', '.join(sorted(channel_set))
    return (device_text, channel_text)

  def describe_waveform(waveform):
    """Dumps a waveform description line."""
    devices, channels = get_compatible(waveform)
    name = '`%s`' % waveform.name if use_markdown else waveform.name
    if channels:
      dump_row(name, waveform.description, channels, devices)

  dump_row('Name', 'Description', 'Channels', 'Devices')
  fout.write(
      '|---------------|------------------------------|--------|--------|\n')

  waveforms_arbs_last = sorted(
      _WAVEFORM_DEFS,
      key=lambda x: x.name.startswith('arb'),
  )
  for waveform in waveforms_arbs_last:
    describe_waveform(waveform)
# pylint: enable=redefined-builtin
