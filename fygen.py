"""Interface to FYXXXX signal generators.  Tested on an FY2300.

See help.py or use the command fygen.help() for more documentation.
"""
# pylint: disable=too-many-lines
# pylint: disable=too-many-public-methods

import sys
import time
import functools
import six
import serial
import fygen_help
import wavedef

# Version numbers.  The minor version number increments when bugs are fixed
# or trivial features are added.  The major version number increments if a
# large feature is added or any APIs change in a non-compatible way.

VERSION = 1.0

# Explicit channel numbers if you want the code a bit clearer.
CH1 = 0
CH2 = 1

# Modulation Modes
MODULATION_FSK = 0
MODULATION_ASK = 1
MODULATION_PSK = 2
MODULATION_BURST = 3
MODULATION_AM = 4
MODULATION_FM = 5
MODULATION_PM = 6

# Modulation Triggers
TRIGGER_CH2 = 0
TRIGGER_EXTERNAL_AC = 1  # FSK/ASK/PSK/BURST modes
TRIGGER_EXTERNAL_IN = 1  # AM/FM/PM modulation modes
TRIGGER_MANUAL = 2
TRIGGER_EXTERNAL_DC = 3

# Sweep modes
SWEEP_FREQUENCY = 0
SWEEP_AMPLITUDE = 1
SWEEP_OFFSET = 2
SWEEP_DUTY_CYCLE = 3

# Sweep sources
SWEEP_SOURCE_TIME = 0
SWEEP_SOURCE_VCO_IN = 1

# Measurement gate time
GATE_TIME_1S = 0
GATE_TIME_10S = 1
GATE_TIME_100S = 2

# Measurement coupling
COUPLING_AC = 0
COUPLING_DC = 1

# Synchronization modes
SYNC_MODES = {
    'wave': 0,
    'freq': 1,
    'volts': 2,
    'offset_volts': 3,
    'duty_cycle': 4,
}

# Maximum read size
MAX_READ_SIZE = 256

# Initialization state
SET_INIT_STATE = {
    'channel': (0, 1),
    'duty_cycle': 0.5,
    'enable': False,
    'freq_hz': 10000,
    'offset_volts': 0,
    'phase_degrees': 0,
    'volts': 5,
    'wave': 'sin',
}

class Error(Exception):
  """Base error class."""

class ChannelActiveError(Error):
  """Tried to define a waveform that is currently being generated"""

class CommandNotAcknowledgedError(Error):
  """The signal generator did not produce the expected response."""

class CommandTooShortError(Error):
  """Command is too short."""

class HelpError(Error):
  """Calling the fygen_help module produced an error."""

class InvalidBurstCycleCountError(Error):
  """Tried to pass an illegal burst cycle count."""

class InvalidChannelError(Error):
  """Tried to pass an invalid channel number."""

class InvalidCouplingError(Error):
  """Tried to pass an invalid coupling mode."""

class InvalidDutyCycleError(Error):
  """Tried to pass an invalid duty cycle."""

class InvalidGateTimeError(Error):
  """Tried to pass an invalid gate time."""

class InvalidModeError(Error):
  """Tried to pass parameters in the wrong mode."""

class InvalidModulationModeError(Error):
  """Tried to pass an invalid modulation mode."""

class InvalidAMAttenuationError(Error):
  """Tried to pass an invalid modulation rate."""

class InvalidSweepModeError(Error):
  """Tried to pass an invalid sweep mode."""

class InvalidSweepSourceError(Error):
  """Tried to pass an invalid sweep source."""

class InvalidSweepTimeError(Error):
  """Tried to pass an invalid time."""

class InvalidSynchronizationMode(Error):
  """Tried to pass an invalid synchronization mode."""

class InvalidVoltageError(Error):
  """Tried to pass an invalid voltage."""

class InvalidVoltageOffsetError(Error):
  """Tried to pass an invalid voltage offset."""

class InvalidFrequencyError(Error):
  """Tried to pass an invalid frequency."""

class InvalidHelpSectionError(Error):
  """Tried to pass an invalid help section number."""

class InvalidTriggerCycleCount(Error):
  """Tried to pass an invalid trigger cycle count."""

class InvalidTriggerModeError(Error):
  """Tried to pass an invalid trigger mode."""

class PossibleFirmwareBugError(Error):
  """Ran into a suspected firmware bug that could not be worked-around."""

class RawValueConflictError(Error):
  """Tried to pass both values and raw_values."""

class UnknownParameterError(Error):
  """Asked for an unknown parameter."""

class UnknownWaveformError(Error):
  """Specified an unknown waveform."""

class ValueCountError(Error):
  """Passed values or raw_values with an unexpected array size."""


# pylint: disable=redefined-builtin
def help(section=0, device='fy2300', fout=sys.stdout):
  """Used to read documentation in an interactive session."""
  try:
    fygen_help.help(section, device, fout)
  except fygen_help.Error as e:
    raise HelpError(e)
# pylint: enable=redefined-builtin

def get_version():
  return VERSION

def detect_device(model):
  """
  Tries to determine the best-matching device for the given model
  """
  model = model.lower()

  # Try matching based on prefix, this is helpful to map e.g.
  # FY2350H to FY2300
  for device in wavedef.SUPPORTED_DEVICES:
    if device[:4] == model[:4]:
      return device

  raise wavedef.UnsupportedDeviceError(
      "Unable to autodetect device '%s'. "
      "Use FYGen(device_name='fy2300') with one of the supported devices, "
      "beware that the waveforms might not match up."
      "Supported devices: %s"
      % (
          model,
          ', '.join(wavedef.SUPPORTED_DEVICES)
      )
  )

class FYGen(object):
  """Initialize a connection object with the signal generator.

  One can also simply point this to sys.stdout to see low-level details without
  talking with a real device.
  """
  def __init__(
      self,
      serial_path='/dev/ttyUSB0',
      port=None,
      device_name=None,
      default_channel=0,
      read_before_write=True,
      init_state=True,
      debug_level=0,
      timeout=5,
      max_volts=20.0,
      min_volts=-20.0,
      _port_is_serial=False,
  ):
    """Initializes connection to device.

    Args:
      serial_path: Path to usb serial device.  The format of this will vary by
        OS and will vary if you have multiple USB serial devices connected.
      port: If not None, specifies an output port.  In this case, path is
        ignored.  One usecase is to set port=sys.stdout to see the commands
        that will be sent.
      device_name: Specific device name, such as 'fy2300', 'fy6800'.  Some
        functions may not be available or may be incorrectly mapped if this
        value is incorrect.
        If left empty the device will be autodetected
      default_channel: The channel(s) used when the parameter is omitted.
      read_before_write: If True, then setting a parameter will first get it.
        If the parameter is already set to the desired value, the value is not
        sent.  This is useful because the signal generator responds to get
        operations much more quickly than set ones.
      init_state: If true, then the first set command will set all unspecified
        set parameters to a known state.
      debug_level: If 0, run silently.  If 1, print send and receive commands.
        If 2, print send and receive commands and wait for confirmation on
        send commands.
      timeout: How long to block reads and writes
      max_volts: Maximum volts/offset to allow
      min_volts: Minimum voltage offset to allow
    """
    if port:
      self.port = port
      self.is_serial = _port_is_serial

      # We cannot autodetect here
      if not self.is_serial and device_name is None:
        device_name = 'fy2300'

    else:
      self.port = serial.Serial(
          port=serial_path,
          baudrate=115200,
          bytesize=serial.EIGHTBITS,
          parity=serial.PARITY_NONE,
          stopbits=serial.STOPBITS_ONE,
          rtscts=False,
          dsrdtr=False,
          xonxoff=False,
          timeout=timeout)

      self.is_serial = True
      self.port.reset_output_buffer()
      self.port.reset_input_buffer()

    self.init_state = init_state
    self.read_before_write = read_before_write and self.is_serial
    self.debug_level = debug_level
    self.init_called_for_channel = set()
    self.device_name = device_name
    self.default_channel = default_channel
    self.max_volts = max_volts
    self.min_volts = min_volts
    # Set to force sweep enable
    self.force_sweep_enable = False

    # Detect model
    if self.device_name is None:
      model = self.get_model()
      self.device_name = detect_device(model)

  def close(self):
    """Closes serial port.  Call this at program exit for a clean shutdown."""
    self.port.close()
    self.port = None

  def send(self, command, retry_count=5):
    """Sends command, then waits for a response.  Returns the response."""
    if len(command) < 3:
      raise CommandTooShortError('Command too short: %s' % command)

    if self.debug_level == 2:
      six.moves.input('%s (Press Enter to Send)' % command)

    data = command + '\n'
    if self.is_serial:
      data = data.encode()
      self.port.reset_output_buffer()
      self.port.reset_input_buffer()

    self.port.write(data)
    self.port.flush()

    response = self._recv(command)

    if self.is_serial and not response and retry_count > 0:
      # sometime the siggen answers queries with nothing.  Wait a bit and try
      # again
      time.sleep(0.1)
      return self.send(command, retry_count - 1)

    return response.strip()

  # Note: unused-argument is disabled because we are capturing locals()
  # into a local variable and accessing these variables using that method
  #
  # pylint counts arguments as local variables:
  #pylint: disable=too-many-locals
  def set(
      self,
      channel=None,
      enable=None,         #pylint: disable=unused-argument
      wave=None,           #pylint: disable=unused-argument
      freq_hz=None,        #pylint: disable=unused-argument
      freq_uhz=None,       #pylint: disable=unused-argument
      volts=None,          #pylint: disable=unused-argument
      offset_volts=None,   #pylint: disable=unused-argument
      phase_degrees=None,  #pylint: disable=unused-argument
      duty_cycle=None,     #pylint: disable=unused-argument
      retry_count=3):
    """Change device settings.

    All parameters are optional and should be specified using named
    parameters (e.g. do not depend on parameter ordering.)

    Note there are two parameters for frequency: freq_hz and freq_uhz.  This is
    to avoid floating point rounding issues.  You can pass either freq_hz or
    freq_uhz but not both.

    Essential Args:
      channel: Can be a single number or a list of numbers.
      wave: Can be a string or an integer < 100.  If it's a string, wavedef
        is used as a lookup table.  If it's an integer, the number is used
        directly.
      freq_hz: An integer that specifies the frequency in hertz.
      freq_uhz: An integer that specifies the frequency in micro hertz.
      volts: A float that specifies the amplitude in volts.  This is rounded to
        the nearest hundredth of a volt.
      offset_volts: A float that specifies the voltage offset from zero
      duty_cycle: A float value from 0-1 that specifies the duty cycle.  Note
        that most waveforms ignore this setting.
      phase_degrees: An float value that specifies the phase offset in degrees
      retry_count: If > 0 and read_before_write is True the set results will
        be verified and resent if verification fails.
    """

    # Convert local arguments into a dictionary
    args_dict = dict(locals())

    if freq_hz is not None and freq_uhz is not None:
      raise InvalidFrequencyError(
          'Please, provide freq_hz or freq_uhz, not both.')

    if channel is None:
      channel = self.default_channel

    if not isinstance(channel, (tuple, list)):
      channel = (channel,)

    for c in channel:
      chan_dict = dict(args_dict)
      for _ in range(retry_count):
        if not self._set_for_channel(c, chan_dict):
          break  # nothing was sent
        if not self.read_before_write:
          break  # Since there is no get, we don't know if a retry is needed.
#pylint: enable=too-many-locals


  def _set_for_channel(self, channel, args_dict):
    """Implements set as above, but for a single channel.

    Args:
      channel: Channel to set (0 or 1)
      args_dict: Key-pairs.  e.g. {'volts': 5.5}.  NOTE: this function does
        modify args_dict by *removing* arguments that are already confirmed
        as set from the dictionary.  This is done to avoid redundant reads
        on retries.
    """
    if channel not in (0, 1):
      raise InvalidChannelError('Invalid channel: %s' % channel)

    # Implements init_state functionality.
    if self.init_state and channel not in self.init_called_for_channel:
      # This is the first call to set for this channel.  Fill in non-specified
      # arguments from SET_INIT_STATE
      self.init_called_for_channel.add(channel)
      for k, v in six.iteritems(SET_INIT_STATE):
        if args_dict[k] is None:
          args_dict[k] = v

    # convert args from a dict to a list so we can order enable=True/False
    # properly and remove null values
    args = list((k, v) for k, v in six.iteritems(args_dict) if v is not None)

    enable = args_dict.get('enable', None)

    # enable=False should to be moved to the beginning of the args list to
    # minimize transient states being generated to connected equipment.
    if enable is not None and not enable:
      del args[args.index(('enable', enable))]
      args.insert(0, ('enable', enable))

    # enable=true needs to be moved to the end of the list, again to minimize
    # transient states being generated.
    if enable is not None and enable:
      del args[args.index(('enable', enable))]
      args.append(('enable', enable))

    def should_set(chan, parm_name, expected_value):
      """Returns true if the write to the siggen should proceed."""
      if not self.read_before_write:
        return True

      if self.get(chan, parm_name) == expected_value:
        # No need to set as the value is already where it needs to be.
        # Also, delete the argument from future retries
        del args_dict[parm_name]
        return False

      return True

    # Map various parameter names to function that check arguments
    # and generate the correct low-level string.
    make_command = {
        'duty_cycle': functools.partial(_make_duty_cycle_command, channel),
        'enable': functools.partial(_make_enable_command, channel),
        'freq_hz': functools.partial(_make_freq_hz_command, channel),
        'freq_uhz': functools.partial(_make_freq_uhz_command, channel),
        'offset_volts': functools.partial(
            _make_offset_volts_command,
            channel,
            self.min_volts,
            self.max_volts),
        'phase_degrees': functools.partial(_make_phase_command, channel),
        'volts': functools.partial(
            _make_volts_command, channel, self.max_volts),
        'wave': functools.partial(
            _make_wave_command, channel, self.device_name),
    }

    command_list = []
    for name, value in (a for a in args if a[0] in make_command):
      if not should_set(channel, name, value):
        continue
      command = make_command[name](value)
      if command:
        command_list.append(command)

    for command in command_list:
      self.send(command)

    return len(command_list)


  def get(self, channel=None, params=None):
    """Get one or more parameters from the Signal generator.

    get() supports three styles.

    1) You can provide a string and get will get that one parameter and return
      its value. The parameter names are the same as the set() command.
    2) You can provide any iterable (list, tuple, set, dictionary) and get()
      will read the names within and returns dictionary of name/value pairs.
      This dictionary can later be used with set.  e.g.  s = fy.get()
      fy.set(**s)
    3) You can provide no parameters and get will return a dictionary of every
      parameter it knows about.

    Args:
      channel: A single channel.  If a list is provided, index 0 of the list is
        used.
      params: See above
    """

    if channel is None:
      channel = self.default_channel

    if isinstance(channel, (list, tuple)):
      channel = channel[0]

    if channel not in (0, 1):
      raise InvalidChannelError('Invalid channel: %s' % channel)

    if params is None:
      p = sorted(SET_INIT_STATE)
      del p[p.index('channel')]
    elif isinstance(params, str):
      p = (params,)
    else:
      p = params

    if 'freq_hz' in p and 'freq_uhz' in p:
      raise InvalidFrequencyError(
          'Please, provide freq_hz or freq_uhz, not both.')

    prefix = 'RF' if channel == 1 else 'RM'

    def send(code):
      """self.send shortcut."""
      return self.send(prefix + code)

    def get_waveform_name():
      """Gets the waveform name from the signal generator."""
      try:
        return wavedef.get_name(self.device_name, int(send('W')), channel)
      except wavedef.Error:
        raise UnknownWaveformError('Unknown waveform index returned')

    def get_offset_volts():
      """Gets offset volts, correcting for an "unsigned" bug in the fygen."""
      offset_unsigned = int(send('O'))
      if offset_unsigned > 0x80000000:
        offset_unsigned = -(0x100000000 - offset_unsigned)
      return float(offset_unsigned) / 1000

    data = {}

    # mapping of parameters to conversion functions.
    conversions = {
        'duty_cycle': lambda: float(send('D')) / 100000.0,
        'enable': lambda: bool(int(send('N'))),
        'freq_hz': lambda: int(send('F').split('.')[0]),
        'freq_uhz': lambda: int(float(send('F')) * 1000000.0),
        'offset_volts': get_offset_volts,
        'phase_degrees': lambda: float(send('P')) / 1000.0,
        'volts': lambda: float(send('A')) / 10000.0,
        'wave': get_waveform_name,
    }

    for name in p:
      if name not in conversions:
        raise UnknownParameterError('Unknown get parameter: %s' % name)
      data[name] = conversions[name]()

    if isinstance(params, str):
      return data[params]

    return data

  def set_waveform(
      self,
      waveform_index,
      raw_values=None,
      values=None,
      min_value=-1.0,
      max_value=1.0,
      value_count=8192):
    """Program an arbitrary waveform.

    Typical use would be to use the values parameter and let set_waveform
    convert to raw_values for you.  Here is a sin wave:

        wave = (math.sin(t * math.pi / 2048.0) for t in range(4096))
        fy.set_waveform(0, values=wave)
        fy.set(0, wave='arb1')

    If you want to pass raw integer values, you can use raw_values instead, an
    example sawtooth

        wave = (t * 4 for t in range(4096))
        fy.set_waveform(0, raw_values=wave)
        fy.set(0, wave='arb1')

    Note: You can not reliably update a waveform while it is selected for a
    channel. The set_waveform command checks both channels and throws an error
    if either is set to the desired waveform.

    Args:
      waveform_index: Which waveform index to program.  Typically 0-63, but it
        depends on your hardware.
      raw_values: Use this if you want to define raw 14-bit values to send to
        the generator with no manipulation.
      values: Use this if you want to provide floats and have set_waveform
        convert to raw_values for you.
      min_value: This is used when converting values.  When using raw_values,
        this parameter is not used.
      max_value: This is used when converting values.  When using raw_values,
        this parameter is not used.
      value_count: The number of values to provide.  Do not change this unless
        your signal generator requires it.
    """
    if waveform_index < 1:
      raise UnknownWaveformError('waveform_index < 1')

    if raw_values:
      if values is not None:
        raise RawValueConflictError(
            'Please do not provide both values and raw_values')
    else:
      raw_values = list(_convert_values_to_raw_values(
          values, min_value, max_value))

    if len(raw_values) != value_count:
      raise ValueCountError(
          'Unexpected value array length.  expected %d, got %d' %
          (value_count, len(raw_values)))

    for c in (0, 1):
      if self.is_serial and self.get(c, 'wave') == 'arb%u' % waveform_index:
        raise ChannelActiveError(
            'Can not update arb%u because it is active on channel %u' %
            (waveform_index, c))

    data = []
    for v in raw_values:
      data.append(v & 255)  # lower 8 bits
      data.append((v >> 8) & 63)  # upper 6 bits

    response = self.send('DDS_WAVE%u' % waveform_index)
    if self.is_serial and response != 'W':
      raise CommandNotAcknowledgedError('DDS_WAVE command was not acknowledged')

    if self.is_serial:
      self.port.write(bytearray(data))
    else:
      for i in range(0, len(data), 16):
        self.port.write(''.join('%02X' % d for d in data[i:i+16]))
        self.port.write('\n')
    response = self._recv('(Wave Data)').strip()
    if self.is_serial and response != 'HN':
      raise CommandNotAcknowledgedError('DDS_WAVE data was not accepted')

  def set_modulation(
      self,
      mode=None,
      trigger=None,
      burst_count=None,
      am_attenuation=None,
      pm_bias_degrees=None,
      hop_freq_hz=None,
      hop_freq_uhz=None,
      fm_bias_freq_hz=None,
      fm_bias_freq_uhz=None):
    """Setup a modulation mode

    Defined modes are: MODULATION_FSK, MODULATION_ASK, MODULATION_PSK
      MODULATION_BURST, MODULATION_AM, MODULATION_FM,
      MODULATION_PM

    Defined sources are: TRIGGER_CH2, TRIGGER_EXTERNAL_AC, TRIGGER_MANUAL,
      TRIGGER_EXTERNAL_DC

    Example:
      # trigger 10 primary pulses on every auxiliary channel pulse
      fy = fygen.FYGen()
      fy.set(channel=0, wave='sin', freq_hz=1000000, enable=True)
      fy.set(channel=1, wave='square', freq_hz=1)
      fy.set_modulation(fygen.MODULATION_BURST, fygen.TRIGGER_CH2, 10)

    Args:
      mode: Modulation mode.  See above.
      trigger: Trigger source. See above
      burst_count: Number of times to cycle on a trigger
      am_attenuation: Used with MODULATION_AM (0.0-1.0)
      pm_bias_degrees: Used with MODULATION_PM
      hop_freq_hz: FSK hop frequency in Hz
      hop_freq_uhz: FSK hop frequency in uHz
      fm_bias_freq_hz: FM bias freq in Hz
      fm_bias_freq_uhz: FM bias freq in uHz
    """
    commands = []

    def maybe_add_frequency(code, freq_hz, freq_uhz):
      """Adds frequency of the given code."""
      if freq_hz is not None and freq_uhz is not None:
        raise InvalidFrequencyError(
            'Please, provide hz or uhz, not both.')

      if freq_hz is not None:
        freq_uhz = freq_hz * 1000000

      if freq_uhz is not None:
        if freq_uhz < 0:
          raise InvalidFrequencyError('frequency < 0')
        commands.append('WF%s%014u' % (code, freq_uhz))

    maybe_add_frequency('K', hop_freq_hz, hop_freq_uhz)
    maybe_add_frequency('M', fm_bias_freq_hz, fm_bias_freq_uhz)

    if mode is not None:
      if mode < 0:
        raise InvalidModulationModeError('Modulation mode < 0')
      if mode > MODULATION_PM:
        raise InvalidModulationModeError('Modulation mode > 3')
      commands.append('WPF%u' % mode)

    if burst_count is not None:
      if burst_count < 1:
        raise InvalidBurstCycleCountError('Trigger burst count < 1')
      commands.append('WPN%u' % burst_count)

    if trigger is not None:
      if trigger < 0:
        raise InvalidTriggerModeError('Trigger mode < 0')
      if trigger > TRIGGER_EXTERNAL_DC:
        raise InvalidTriggerModeError('Trigger mode > 3')
      commands.append('WPM%u' % trigger)

    if am_attenuation is not None:
      if am_attenuation < 0.0:
        raise InvalidAMAttenuationError('AM Ratio < 0')
      if am_attenuation > 2.0:
        raise InvalidAMAttenuationError('AM Ratio > 1')
      commands.append('WPR%.1f' % (am_attenuation * 100.0))

    if pm_bias_degrees is not None:
      commands.append('WPP%.1f' % (pm_bias_degrees % 360.0))

    for command in commands:
      self.send(command)

  # pylint: disable=too-many-locals
  # pylint: disable=too-many-statements
  def set_sweep(
      self,
      enable=None,
      mode=None,
      log_sweep=None,
      source=None,
      time_seconds=None,
      start_freq_hz=None,
      end_freq_hz=None,
      start_volts=None,
      end_volts=None,
      start_offset_volts=None,
      end_offset_volts=None,
      start_duty_cycle=None,
      end_duty_cycle=None):
    """Setup a parameter sweep.

    The Signal generator can sweep frequency, amplitude, offset,
    or duty cycle.  Only one parameter can be swept at a time.

    Defined modes are: SWEEP_FREQUENCY, SWEEP_AMPLITUDE, SWEEP_OFFSET,
      SWEEP_DUTY_CYCLE

    Defined sources are: SWEEP_SOURCE_TIME and SWEEP_SOURCE_VCO_IN

    Example:
      # Sweep from 1000Hz to 10000Hz over 10 seconds
      fy = fygen.FYGen()
      fy.set_sweep(
          mode=fygen.SWEEP_FREQUENCY,
          time_seconds=10,
          start_freq_hz=1000,
          end_freq_hz=10000,
          enable=True)

    Args:
      enable: Used to enable/disable the sweep
      mode: Modulation mode.  See above.
      log_sweep: If true, the sweep is logarythmic, otherwise it is linear.
      source: Sweep source, see above
      time_seconds: If the source is SWEEP_SOURCE_TIME, this defines the sweep
        time.
      start_freq_hz: If the mode is SWEEP_FREQUENCY, this float defines the
        starting frequency
      end_freq_hz: If the mode is SWEEP_FREQUENCY, this float defines the
        ending frequency
      start_volts: If the mode is SWEEP_AMPLITUDE, this float defines the
        starting voltage
      end_volts: If the mode is SWEEP_AMPLITUDE, this float defines the ending
        voltage
      start_offset_volts: If the mode is SWEEP_OFFSET, this float defines the
        starting voltage offset
      end_offset_volts: If the mode is SWEEP_OFFSET, this float defines the
        ending voltage offset
      start_duty_cycle: If the mode is SWEEP_DUTY_CYCLE, this float (0-1)
        defines the starting duty cycle (for supported wave types)
      end_duty_cycle: If the mode is SWEEP_DUTY_CYCLE, this float (0-1) defines
        the ending duty cycle (for supported wave types)
    """
    commands = []

    if mode is not None:
      if mode < 0 or mode > SWEEP_DUTY_CYCLE:
        raise InvalidSweepModeError('Invalid Sweep Mode: %s' % mode)
      commands.append('SOB%u' % mode)
    elif start_freq_hz is not None or end_freq_hz is not None:
      mode = SWEEP_FREQUENCY
    elif start_volts is not None or end_volts is not None:
      mode = SWEEP_AMPLITUDE
    elif start_offset_volts is not None or end_offset_volts is not None:
      mode = SWEEP_OFFSET
    elif start_duty_cycle is not None or end_duty_cycle is not None:
      mode = SWEEP_DUTY_CYCLE

    if log_sweep is not None:
      commands.append('SMO%u' % (1 if log_sweep else 0))

    if source is not None:
      if source == SWEEP_SOURCE_TIME:
        commands.append('SXY0')
      elif source == SWEEP_SOURCE_VCO_IN:
        commands.append('SXY1')
      else:
        raise InvalidSweepSourceError('Invalid sweep source')

    if time_seconds is not None:
      if source == SWEEP_SOURCE_VCO_IN:
        raise InvalidSweepSourceError(
            'provided time_seconds with source == SWEEP_SOURCE_VCO_IN')
      if time_seconds <= 0:
        raise InvalidSweepTimeError('time_seconds <= 0')
      commands.append('STI%.2f' % time_seconds)

    if start_freq_hz is not None:
      if mode != SWEEP_FREQUENCY:
        raise InvalidModeError(
            'using start_freq_hz when not in SWEEP_FREQUENCY mode.')
      if start_freq_hz <= 0:
        raise InvalidFrequencyError('start_freq_hz <= 0')
      commands.append('SST%.1f' % start_freq_hz)

    if end_freq_hz is not None:
      if mode != SWEEP_FREQUENCY:
        raise InvalidModeError(
            'using end_freq_hz when not in SWEEP_FREQUENCY mode.')
      if end_freq_hz <= 0:
        raise InvalidFrequencyError('end_freq_hz <= 0')
      commands.append('SEN%.1f' % end_freq_hz)

    if start_volts is not None:
      if mode != SWEEP_AMPLITUDE:
        raise InvalidModeError(
            'using start_volts when not in SWEEP_AMPLITUDE mode.')
      if start_volts <= 0:
        raise InvalidVoltageError('start_volts <= 0')
      if start_volts > self.max_volts:
        raise InvalidVoltageError('start_volts > %g' % self.max_volts)
      commands.append('SST%.3f' % start_volts)

    if end_volts is not None:
      if mode != SWEEP_AMPLITUDE:
        raise InvalidModeError(
            'using end_volts when not in SWEEP_AMPLITUDE mode.')
      if end_volts <= 0:
        raise InvalidVoltageError('end_volts <= 0')
      if end_volts > self.max_volts:
        raise InvalidVoltageError('end_volts > %g' % self.max_volts)
      commands.append('SEN%.3f' % end_volts)

    if start_offset_volts is not None:
      if mode != SWEEP_OFFSET:
        raise InvalidModeError(
            'using start_offset_volts when not in SWEEP_OFFSET mode.')
      if start_offset_volts > self.max_volts:
        raise InvalidVoltageError('start_offset_volts > %g' % self.max_volts)
      # Bug: The offset volts parameter needs an additional offset added
      commands.append('SST%.3f' % (start_offset_volts + 10.0))

    if end_offset_volts is not None:
      if mode != SWEEP_OFFSET:
        raise InvalidModeError(
            'using end_offset_volts when not in SWEEP_OFFSET mode.')
      if end_offset_volts > self.max_volts:
        raise InvalidVoltageError('end_offset_volts > %g' % self.max_volts)
      # Bug: The offset volts parameter needs an additional offset added
      commands.append('SEN%.3f' % (end_offset_volts + 10.0))

    if start_duty_cycle is not None:
      if mode != SWEEP_DUTY_CYCLE:
        raise InvalidModeError(
            'using start_duty_cycle when not in SWEEP_DUTY_CYCLE mode.')
      if start_duty_cycle <= 0:
        raise InvalidDutyCycleError('start_duty_cycle <= 0')
      if start_duty_cycle >= 1:
        raise InvalidDutyCycleError('start_duty_cycle >= 1')
      commands.append('SST%.1f' % (start_duty_cycle * 100.0))

    if end_duty_cycle is not None:
      if mode != SWEEP_DUTY_CYCLE:
        raise InvalidModeError(
            'using end_duty_cycle when not in SWEEP_DUTY_CYCLE mode.')
      if end_duty_cycle <= 0:
        raise InvalidDutyCycleError('end_duty_cycle <= 0')
      if end_duty_cycle >= 1:
        raise InvalidDutyCycleError('end_duty_cycle >= 1')
      commands.append('SEN%.1f' % (end_duty_cycle * 100.0))

    if (enable is not None and not enable) or commands:
      # disable the sweep when changing any parameters
      self.send('SBE0')


    for command in commands:
      self.send(command)

    # -- This should come last ---
    if enable is not None and enable:
      if not self.force_sweep_enable:
        raise PossibleFirmwareBugError(
            'Sweep enable did not work properly on the test device '
            '(FY2300 V2.3).  If possible, press the knob button on the '
            'device to enable the sweep.  To force the setting, set '
            'fy.force_sweep_enable=True (assuming your object is called fy). '
            'The bug is that set sweep parameters are ignored so be careful '
            'what you connect the generator to if you force enable sweep.')
      self.send('SBE1')
  # pylint: enable=too-many-statements
  # pylint: enable=too-many-locals

  def set_measurement(
      self,
      reset_counter=None,
      pause=None,
      gate_time=None,
      coupling=None):
    """Used to control aspects of the measurement function.

    All parameters are optional.  Pass only those you wish to change.

    Args:
      reset_counter: If True, the counter will be reset
      pause: Set to True or False to pause and unpause the measurement.
      gate_time: Set to GATE_TIME_1S, GATE_TIME_10S or GATE_TIME_100S.
      coupling: Set to COUPLING_DC or COUPLING_AC
    """
    commands = []

    if pause is not None:
      commands.append('WCP%u' % (0 if pause else 1))

    if gate_time is not None:
      if gate_time < 0 or gate_time > GATE_TIME_100S:
        raise InvalidGateTimeError(
            'Invalid gate time, please choose GATE_TIME_1S, GATE_TIME_10S or '
            'GATE_TIME_100S')
      commands.append('WCG%u' % gate_time)

    if coupling is not None:
      if coupling == COUPLING_DC:
        commands.append('WCC1')
      elif coupling == COUPLING_AC:
        commands.append('WCC0')
      else:
        raise InvalidCouplingError(
            'Invalid coupling.  please choose COUPLING_DC or COUPLING_AC')

    if reset_counter:
      commands.append('WCZ0')

    for command in commands:
      self.send(command)

  def get_measurement(self, params=None):
    """Gets one or more measurement parameters.

    params is special in that it can take one of three forms.

    If passed an iterable (list, set) or strings, it will return a dictionary
    of values for the requested parameters.

    If passed a single string, it will return only the value of that parameter.

    If passed a None, it will return a dictionary of all known parameters,
    except for the counter.  The reason is that reading the frequency resets
    the counter to zero, thus they can't effectively be read at the same time.

    Parameters include:
      freq_hz: Returns the frequency as a floating point value.
      counter: Returns the current counter value.
      period_sec: Returns the wave period as a float in seconds.
      positive_width_sec: Returns the "high value" pulse width as a float in
        seconds.
      negative_width_sec: Returns the "low value" pulse width as a float in
        seconds.
      duty_cycle: Returns the duty cycle as a float from 0.0-1.0.
    """

    extract_param = None
    if params is None:
      params = (
          'freq_hz',
          'period_sec',
          'positive_width_sec',
          'negative_width_sec',
          'duty_cycle')
    elif isinstance(params, str):
      extract_param = params
      params = (params,)

    def read_frequency():
      """Reads the current measurement frequency."""
      try:
        gate_time = int(self.send('RCG'))
      except ValueError:
        raise InvalidGateTimeError('RCG returned an unrecognized gate time.')
      return float(self.send('RCF')) / (10.0 ** gate_time)

    getters = {
        'freq_hz': read_frequency,
        'counter': lambda: int(self.send('RCC')),
        'period_sec': lambda: float(self.send('RCT')) / 1000000000.0,
        'positive_width_sec': lambda: float(
            self.send('RC+')) / 1000000000.0,
        'negative_width_sec': lambda: float(
            self.send('RC-')) / 1000000000.0,
        'duty_cycle': lambda: float(self.send('RCD')) / 1000.0,
    }

    results = {}

    for param in params:
      if param not in getters:
        raise UnknownParameterError(
            'Unknown parameter: %s.  Valid parameters are %s' %
            (param, ', '.join(sorted(getters))))
      results[param] = getters[param]()

    if extract_param:
      return results[extract_param]

    return results

  def save(self, index):
    """Saves current device state to the given index (internal to the device).

    Note that index 1 is documented as the startup settings."""
    self.send('USN%02u' % index)

  def load(self, index):
    """Restore device state from a given index.

    This index is expected to have been saved earlier in time.  Note that the
    state is internal to the device.  The client side (python) does not know how
    the device state changed without further queries."""
    self.send('ULN%02u' % index)

  # pylint: disable=unused-argument
  def set_synchronization(
      self,
      wave=None,
      freq=None,
      volts=None,
      offset_volts=None,
      duty_cycle=None):
    """Configures parameter synchronization.

    Values set to True enable synchronization.  False disables synchronization,
    the default of None does not change synchronization.
    """
    for arg, val in six.iteritems(locals()):
      if arg in SYNC_MODES and val is not None:
        if val:
          self.send('USA%u' % SYNC_MODES[arg])
        else:
          self.send('USD%u' % SYNC_MODES[arg])
  # pylint: enable=unused-argument

  def get_synchronization(self, params=None):
    """Returns the current state of sync modes.

    Available parameters include wave, freq, volts, offset, and duty_cycle

    If params is a string, the function returns True or False for that parameter

    If params is an iterable (list, dict, set, etc), a dictionary of parameter
    is returned.

    If params is None, a dictionary of all known parameters is returned.
    """
    if params is None:
      p_list = sorted(SYNC_MODES)
    elif isinstance(params, str):
      p_list = (params,)
    else:
      p_list = params

    data = {}
    for p in p_list:
      if p not in SYNC_MODES:
        raise InvalidSynchronizationMode(
            'Invalid synchronization mode: %s' % p)
      data[p] = bool(int(self.send('RSA%u' % SYNC_MODES[p])))

    if isinstance(params, str):
      return data[params]

    return data

  def set_buzzer(self, enable):
    """Enables/disables the buzzer."""
    self.send('UBZ%d' % (1 if enable else 0))

  def get_buzzer(self):
    """Returns True if the buzzer is enabled."""
    return bool(int(self.send('RBZ')))

  def set_uplink(self, is_master=None, enable=None):
    """Sets uplink mode as master or slave.

    All parameters are optional.
    """
    if enable is not None and not enable:
      self.send('UUL0')

    if is_master is not None:
      self.send('UMS%d' % (0 if is_master else 1))

    if enable is not None and enable:
      self.send('UUL1')

  def get_uplink(self, params=None):
    """Sets uplinks settings.

    params can be a string, a dict or None.

    If a string, it will return the requested parameter.

    If a dict, it will return the requested parametes as a dict.

    If none, it will return all parameters as a dict.

    Valid parameters include is_master and enable
    """
    extract_parm = None
    if isinstance(params, str):
      extract_parm = params
      params = (params,)
    elif params is None:
      params = ('enable', 'is_master')

    results = {}
    for parm in params:
      if parm == 'enable':
        results[parm] = bool(int(self.send('RUL')))
      elif parm == 'is_master':
        results[parm] = not bool(int(self.send('RMS')))
      else:
        raise UnknownParameterError('Unknown uplink parameter: %s' % parm)

    if extract_parm:
      return results[extract_parm]

    return results

  def get_id(self):
    """Returns the device id."""
    return self.send('UID')

  def get_model(self):
    """Returns the device model."""
    return self.send('UMO')

  def _recv(self, command):
    """Waits for device."""
    if not self.is_serial:
      return ''
    response = self.port.read_until(size=MAX_READ_SIZE).decode('utf8')
    if self.debug_level:
      sys.stdout.write('%s -> %s\n' % (command.strip(), response.strip()))
    return response


def _make_command(channel, suffix):
  """Creates a generic command.

  Args:
    channel: 0 or 1
    suffix: The suffix of the command.  e.g. W00 would be for sin waveform.

  Raises:
    InvalidChannelError: if any channel other than 0 or 1 is given.
  """
  if channel == 0:
    return 'WM' + suffix

  if channel == 1:
    return 'WF' + suffix

  raise InvalidChannelError(
      'Invalid channel: %s.  Only 0 or 1 is supported' % channel)

def _make_wave_command(channel, device_name, wave):
  """Creates a wave command string.

  Args:
    channel: Channel number
    wave: A string or an integer.  If a string, then wavedef is used as a
      lookup table

  Raises:
    UnknownWaveformError: If a string is passed for wave and it's not found
      in wavedef
    UnknownWaveformError: If the waveform index is too high or too low
  """
  if isinstance(wave, str):
    try:
      wave = wavedef.get_id(device_name, wave, channel)
    except wavedef.Error as e:
      raise UnknownWaveformError(e)

  if wave < 0:
    raise UnknownWaveformError(
        'Invalid waveform index %d.  Index must be >= 0' % wave)

  return _make_command(channel, 'W%02u' % wave)


def _make_freq_uhz_command(channel, freq_uhz):
  """Create a frequency command string.

  freq_hz and freq_uhz are summed for the final result.

  Args:
    channel: Channel number
    freq_uhz: Integer frequency in uhz.  None is acceptable.

  Raises:
    InvalidFrequencyError: If a negative frequency is passed.
  """
  if freq_uhz < 0:
    raise InvalidFrequencyError('Invalid freq_uhz: %d' % freq_uhz)

  return _make_command(channel, 'F%014u' % freq_uhz)

def _make_freq_hz_command(channel, freq_hz):
  return _make_freq_uhz_command(channel, freq_hz * 1000000)


def _make_volts_command(channel, max_volts, volts):
  """Creates a waveform amplitude string."""
  if volts < 0:
    raise InvalidVoltageError('volts is too low: %g < 0' % volts)

  if volts > max_volts:
    raise InvalidVoltageError('volts is too high: %g > %g' % (volts, max_volts))

  return _make_command(channel, 'A%.2f' % volts)


def _make_duty_cycle_command(channel, duty_cycle):
  """Creates a waveform duty cycle string."""
  if duty_cycle <= 0.0:
    raise InvalidDutyCycleError('duty_cycle <= 0: %g' % duty_cycle)

  if duty_cycle >= 1.0:
    raise InvalidDutyCycleError('duty_cycle >= 1: %g' % duty_cycle)

  return _make_command(channel, 'D%.1f' % (duty_cycle * 100.0))


def _make_offset_volts_command(channel, min_volts, max_volts, volts):
  """Create a voltage offset string."""
  if volts < min_volts:
    raise InvalidVoltageOffsetError(
        'offset_volts is too low: %g < %g' % (volts, min_volts))

  if volts > max_volts:
    raise InvalidVoltageOffsetError(
        'offset_volts is too high: %g > %g' % (volts, max_volts))

  return _make_command(channel, 'O%.2f' % volts)


def _make_phase_command(channel, phase_degrees):
  """Creates a phase string."""
  return _make_command(channel, 'P%.3f' % (phase_degrees % 360))


def _make_enable_command(channel, enable):
  """Enable/Disable a channel.

  Args:
    channel: 0 or 1
    enable: True/False
  """
  return _make_command(channel, 'N' + ('1' if enable else '0'))

def _convert_values_to_raw_values(values, min_value, max_value):
  """Converts an array of values to an array of raw_values."""
  max_raw_value = 16384  # 14-bit
  for v in values:
    raw_v = int((v - min_value) * max_raw_value / (max_value - min_value))
    if raw_v < 0:
      raw_v = 0
    if raw_v >= max_raw_value:
      raw_v = max_raw_value - 1
    yield raw_v
