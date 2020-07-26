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
    '',
    'fy2300',
    'fy6800',
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
    'stair': 'Stairstep',
    'sin': 'Sin',
    'sinc': 'Sinc Pulse',
    'square': 'Square',
    'trap': 'Trapezoidal Pulse',
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
            'Waveform name must consist of REPLACE_CODES separated by dashes')

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

      if device_name not in SUPPORTED_DEVICES:
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

# format
_WAVEFORM_DEFS = [
    WaveformDef('sin', {':': 0}),
    WaveformDef('square', {':': 1}),
    WaveformDef('cmos', {':': 2}),
    WaveformDef('adj-pulse', {':0': 3}),
    WaveformDef('dc', {':0': 4, ':1': 3}),
    WaveformDef('tri', {':0': 5, ':1': 4}),
    WaveformDef('ramp', {':0': 6, ':1': 5}),
    WaveformDef('neg-ramp', {':0': 7, ':1': 6}),
    WaveformDef('stair-tri', {':0': 8, ':1': 7}),
    WaveformDef('stair', {':0': 9, ':1': 8}),
    WaveformDef('neg-stair', {':0': 10, ':1': 9}),
    WaveformDef('exp', {':0': 11, ':1': 10}),
    WaveformDef('neg-exp', {':0': 12, ':1': 11}),
    WaveformDef('fall-exp', {':0': 13, ':1': 12}),
    WaveformDef('neg-fall-exp', {':0': 14, ':1': 13}),
    WaveformDef('log', {':0': 15, ':1': 14}),
    WaveformDef('neg-log', {':0': 16, ':1': 15}),
    WaveformDef('fall-log', {':0': 17, ':1': 16}),
    WaveformDef('neg-fall-log', {':0': 18, ':1': 17}),
    WaveformDef('full-wav', {':0': 19, ':1': 18}),
    WaveformDef('neg-full-wav', {':0': 20, ':1': 19}),
    WaveformDef('half-wav', {':0': 21, ':1': 20}),
    WaveformDef('neg-half-wav', {':0': 22, ':1': 21}),
    WaveformDef('lorentz', {':0': 23, ':1': 22}),
    WaveformDef('multitone', {':0': 24, ':1': 23}),
    WaveformDef('rand', {':0': 25, ':1': 24}),
    WaveformDef('ecg', {':0': 26, ':1': 25}),
    WaveformDef('trap', {':0': 27, ':1': 26}),
    WaveformDef('sinc', {':0': 28, ':1': 27}),
    WaveformDef('impulse', {':0': 29, ':1': 28}),
    WaveformDef('gauss', {':0': 30, ':1': 29}),
    WaveformDef('am', {':0': 31, ':1': 30}),
    WaveformDef('fm', {':0': 32, ':1': 31}),
    WaveformDef('chirp', {':0': 33, ':1': 32}),
]

def _make_arb(count, start_dict):
  for arb_index in range(1, count + 1):
    _WAVEFORM_DEFS.append(WaveformDef('arb%u' % arb_index, start_dict))
    # create a new dictionary will all indexes incremented by one
    start_dict = dict((k, v+1) for k, v in six.iteritems(start_dict))

# Add arb1, arb2 ... arb64
_make_arb(64, {':0': 34, ':1': 33})

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

  _check_is_supported(device_name)

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

  _check_is_supported(device_name)

  if channel not in (0, 1):
    raise InvalidChannelError(
        'Invalid channel %d.  Please use a 0 or 1' % channel)

  raise InvalidWaveformIdError(
      'Invalid waveform id %d for device %s, channel %d.' %
      (wave_id, device_name, channel))

def _check_is_supported(device_name):
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

  _check_is_supported(device_name)

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
def help(device_name='', fout=sys.stdout, use_markdown=False):
  """Dumps a table of waveform names, along with supported devices and channels.

  Example output:

  Name       Description       Channels
  ----------------------------------------------------
  sin        Sin               all
  adj-pulse  Adjustable Pulse  0
  ...
  """
  _check_is_supported(device_name)

  def dump_row(name, description, channel):
    fout.write('|%-15s|%-40s|%8s|\n' % (name, description, channel))

  def get_channels(waveform):
    """Returns channels for a given waveform."""
    channel_set = set()
    for mapping in waveform.mappings:
      if mapping.startswith(':') or mapping.startswith('%s:' % device_name):
        channel = mapping.split(':')[1]
        if not channel:
          return '0, 1'
        channel_set.add(channel)

    if not channel_set:
      return None

    return ', '.join(sorted(channel_set))

  def describe_waveform(waveform):
    """Dumps a waveform description line."""
    channels = get_channels(waveform)
    name = '`%s`' % waveform.name if use_markdown else waveform.name
    if channels:
      dump_row(name, waveform.description, channels)

  dump_row('Name', 'Description', 'Channels')
  fout.write(
      '|---------------|----------------------------------------|--------|\n')
  for waveform in _WAVEFORM_DEFS:
    describe_waveform(waveform)
# pylint: enable=redefined-builtin
