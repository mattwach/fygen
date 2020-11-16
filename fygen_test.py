"""Unit tests for fygen module."""

import unittest
import six

import fygen
import fygen_help
from wavedef import SUPPORTED_DEVICES

# pylint: disable=too-many-public-methods
# pylint: disable=invalid-name
# pylint: disable=too-many-lines

class FakeSerial(object):
  """Fake serial object for when more interaction is required."""
  def __init__(self, read_lines):
    self.read_lines = read_lines
    self.write_lines = []

  def getvalue(self):
    return ''.join(self.write_lines)

  def write(self, line):
    self.write_lines.append(line.decode('utf8'))

  # pylint: disable=unused-argument
  # pylint: disable=no-self-use
  def flush(self):
    pass

  def read(self, unused_length):
    return '\n'

  def reset_input_buffer(self):
    pass

  def reset_output_buffer(self):
    pass

  def read_until(self, terminator='\n', size=0):
    """fake read_until method."""
    r = self.read_lines[0]
    del self.read_lines[0]
    return r
  # pylint: enable=unused-argument
  # pylint: enable=no-self-use


class TestFYGen(unittest.TestCase):
  """Test harness for FYGen."""
  def setUp(self):
    self.output = six.StringIO()
    self.fy = fygen.FYGen(
        port=self.output,
        init_state=False,
        device_name='fy2300',
    )

  def tearDown(self):
    self.fy.close()

  def test_help(self):
    """Asserts that all help sections render."""
    for section in range(len(fygen_help.SECTIONS)):
      fygen.help(section, fout=self.output)
      self.assertIn('Other Help Sections', self.output.getvalue())

  def test_help_device(self):
    """Tests calling help with a device name."""
    for section in range(len(fygen_help.SECTIONS)):
      fygen.help(section, 'fy2300', self.output)
      self.assertIn('Other Help Sections', self.output.getvalue())

  def test_help_invalid_section(self):
    """Provides an invalid help section number."""
    with self.assertRaises(fygen.HelpError):
      fygen.help(len(fygen_help.SECTIONS))

  def test_get_version(self):
    """Tests the version command."""
    self.assertEqual(1.0, fygen.get_version())

  def test_autoset(self):
    """Tests autoset functionality."""
    fy = fygen.FYGen(port=self.output)
    fy.set((0, 1))
    val = self.output.getvalue()
    self.assertIn('WMN0\n', val)
    self.assertIn('WFN0\n', val)

  def test_autoset_with_args(self):
    """Tests autoset with additional arguments provided."""
    fy = fygen.FYGen(port=self.output)
    fy.set(wave='square', volts=0.1)
    val = self.output.getvalue()
    self.assertIn('WMW01\n', val)
    self.assertIn('WMA0.10\n', val)

  def test_send(self):
    """Tests the low-level send."""
    fs = FakeSerial([b'foo\n', b'bar\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True
    self.assertEqual('foo', fy.send('foocmd'))
    self.assertEqual('bar', fy.send('barcmd'))
    self.assertEqual('foocmd\nbarcmd\n', fs.getvalue())

  def test_send_too_short(self):
    """Provides a command that is too short."""
    with self.assertRaises(fygen.CommandTooShortError):
      self.fy.send('FO')

  def test_set_enable(self):
    """Enables generator on both channels."""
    self.fy.set(channel=(0, 1), volts=3, enable=True)
    self.assertEqual(
        'WMA3.00\n'
        'WMN1\n'
        'WFA3.00\n'
        'WFN1\n',
        self.output.getvalue())

  def test_already_enabled(self):
    """Tests WMN1 is not sent if the channel is already enabled."""
    fs = FakeSerial([b'1\n'])
    fy = fygen.FYGen(port=fs, init_state=False)
    fy.is_serial = True
    fy.read_before_write = True

    fy.set(0, enable=True)
    self.assertEqual('RMN\n', fs.getvalue())

  def test_set_disable(self):
    """Tests disable function on both channels."""
    fy = fygen.FYGen(port=self.output, default_channel=(0, 1), init_state=False)
    fy.set(volts=3, enable=False)
    self.assertEqual(
        'WMN0\n'
        'WMA3.00\n'
        'WFN0\n'
        'WFA3.00\n',
        self.output.getvalue())

  def test_already_disabled(self):
    """Tests that WMN0 is not sent if the channel is already disabled."""
    fs = FakeSerial([b'0\n'])
    fy = fygen.FYGen(port=fs, init_state=False)
    fy.is_serial = True
    fy.read_before_write = True

    fy.set(0, enable=False)
    self.assertEqual('RMN\n', fs.getvalue())

  def test_invalid_channel(self):
    """Passes an invalid channel."""
    with self.assertRaises(fygen.InvalidChannelError):
      self.fy.set(channel=2)

  def test_set_wave1(self):
    """Sets current wave by name."""
    self.fy.set(wave='sin')
    self.fy.set(channel=1, wave='square')
    self.assertEqual(
        'WMW00\n'
        'WFW01\n',
        self.output.getvalue())

  def test_set_wave2(self):
    """Sets current wave by number."""
    self.fy.set(wave=46)
    self.assertEqual('WMW46\n', self.output.getvalue())

  def test_wave_already_set(self):
    """Asserts a wave that is already square is not reset to square."""
    fs = FakeSerial([b'1\n'])
    fy = fygen.FYGen(port=fs, init_state=False)
    fy.is_serial = True
    fy.read_before_write = True

    fy.set(0, wave='square')
    self.assertEqual('RMW\n', fs.getvalue())

  def test_unknown_wave(self):
    """Passes an unknown waveform name."""
    with self.assertRaises(fygen.UnknownWaveformError):
      self.fy.set(wave='foo')

  def test_invalid_wave_index(self):
    """Passes an invalid waveform index."""
    with self.assertRaises(fygen.UnknownWaveformError):
      self.fy.set(wave=-1)

  def test_set_freq1(self):
    """Sets a frequency using freq_hz."""
    self.fy.set(freq_hz=5000)
    self.fy.set(channel=1, freq_hz=1e6)
    self.assertEqual(
        'WMF00005000000000\n'
        'WFF01000000000000\n',
        self.output.getvalue())

  def test_set_freq2(self):
    """Sets a frequency using freq_uhz."""
    self.fy.set(freq_uhz=5000)
    self.fy.set(channel=1, freq_uhz=1e6)
    self.assertEqual(
        'WMF00000000005000\n'
        'WFF00000001000000\n',
        self.output.getvalue())

  def test_freq_already_set1(self):
    """Tests that a frequency is not reset to the same thing."""
    fs = FakeSerial([b'12345\n'])
    fy = fygen.FYGen(port=fs, init_state=False)
    fy.is_serial = True
    fy.read_before_write = True

    fy.set(0, freq_hz=12345)
    self.assertEqual('RMF\n', fs.getvalue())

  def test_freq_already_set2(self):
    """Tests that a frequency is not reset to the same thing."""
    fs = FakeSerial([b'1234.5\n'])
    fy = fygen.FYGen(port=fs, init_state=False)
    fy.is_serial = True
    fy.read_before_write = True

    fy.set(0, freq_uhz=1234500000)
    self.assertEqual('RMF\n', fs.getvalue())

  def test_set_both_frequencies(self):
    """Tries passing both freq_hz and freq_uhz."""
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set(freq_hz=4000, freq_uhz=5000)

  def test_invalid_freq1(self):
    """Tries passing a negative frequency (freq_hz version)."""
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set(freq_hz=-1)

  def test_invalid_freq2(self):
    """Tries passing a negative frequency (freq_uhz version)."""
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set(freq_uhz=-1)

  def test_set_volts(self):
    """Sets voltage amplitude on both channels."""
    self.fy.set(volts=10)
    self.fy.set(channel=1, volts=0)
    self.assertEqual(
        'WMA10.00\n'
        'WFA0.00\n',
        self.output.getvalue())

  def test_volts_already_set(self):
    """Tries to set the voltage to an already set value."""
    fs = FakeSerial([b'56000\n'])
    fy = fygen.FYGen(port=fs, init_state=False)
    fy.is_serial = True
    fy.read_before_write = True

    fy.set(0, volts=5.6)
    self.assertEqual('RMA\n', fs.getvalue())

  def test_volts_too_low(self):
    """Tries to set the voltage to a negative value."""
    fy = fygen.FYGen(port=self.output)
    with self.assertRaises(fygen.InvalidVoltageError):
      fy.set(volts=-0.1)

  def test_volts_too_high(self):
    """Tries to set the voltage higher than the allowed maximum."""
    fy = fygen.FYGen(port=self.output, max_volts=1.5)
    with self.assertRaises(fygen.InvalidVoltageError):
      fy.set(volts=1.6)

  def test_duty_cycle(self):
    """Sets the duty cycle on both channels."""
    self.fy.set(duty_cycle=0.5)
    self.fy.set(channel=1, duty_cycle=0.9)
    self.assertEqual(
        'WMD50.0\n'
        'WFD90.0\n',
        self.output.getvalue())

  def test_duty_cycle_already_set(self):
    """Sets the duty cycle to an already-set value."""
    fs = FakeSerial([b'10500\n'])
    fy = fygen.FYGen(port=fs, init_state=False)
    fy.is_serial = True
    fy.read_before_write = True

    fy.set(0, duty_cycle=0.105)
    self.assertEqual('RMD\n', fs.getvalue())

  def test_duty_cycle_too_low(self):
    """Tries to set the duty cycle to zero."""
    with self.assertRaises(fygen.InvalidDutyCycleError):
      self.fy.set(duty_cycle=0)

  def test_duty_cycle_too_high(self):
    """Tries to set the duty cycle to one."""
    with self.assertRaises(fygen.InvalidDutyCycleError):
      self.fy.set(duty_cycle=1)

  def test_offset_volts(self):
    """Sets the offset voltage on both channels."""
    self.fy.set(offset_volts=1.5)
    self.fy.set(channel=1, offset_volts=-1.6)
    self.assertEqual(
        'WMO1.50\n'
        'WFO-1.60\n',
        self.output.getvalue())

  def test_offset_volts_already_set(self):
    """Tries to set the offset voltage to a value already set."""
    fs = FakeSerial([b'12340\n'])
    fy = fygen.FYGen(port=fs, init_state=False)
    fy.is_serial = True
    fy.read_before_write = True

    fy.set(0, offset_volts=12.34)
    self.assertEqual('RMO\n', fs.getvalue())

  def test_offset_volts_too_low(self):
    """Tries to set the offset voltage too low."""
    fy = fygen.FYGen(port=self.output, min_volts=-1.5, init_state=False)
    with self.assertRaises(fygen.InvalidVoltageOffsetError):
      fy.set(offset_volts=-1.6)

  def test_offset_volts_too_high(self):
    """Tries to set the offset voltage too high."""
    fy = fygen.FYGen(port=self.output, max_volts=1.5, init_state=False)
    with self.assertRaises(fygen.InvalidVoltageOffsetError):
      fy.set(offset_volts=1.6)

  def test_phase(self):
    """Sets the phase on both channels."""
    self.fy.set(phase_degrees=10)
    self.fy.set(channel=1, phase_degrees=380.3)
    self.assertEqual(
        'WMP10.000\n'
        'WFP20.300\n',
        self.output.getvalue())

  def test_phase_already_set(self):
    """Tries to set the phase to an already-set value."""
    fs = FakeSerial([b'189300\n'])
    fy = fygen.FYGen(port=fs, init_state=False)
    fy.is_serial = True
    fy.read_before_write = True

    fy.set(0, phase_degrees=189.3)
    self.assertEqual('RMP\n', fs.getvalue())

  def test_set_modulation(self):
    """Tries every known combination of modulatin and trigger."""
    self.fy.set_modulation(mode=fygen.MODULATION_FSK)
    self.fy.set_modulation(mode=fygen.MODULATION_ASK)
    self.fy.set_modulation(mode=fygen.MODULATION_PSK)
    self.fy.set_modulation(mode=fygen.MODULATION_BURST)
    self.fy.set_modulation(mode=fygen.MODULATION_AM)
    self.fy.set_modulation(mode=fygen.MODULATION_FM)
    self.fy.set_modulation(mode=fygen.MODULATION_PM)

    self.fy.set_modulation(trigger=fygen.TRIGGER_CH2)
    self.fy.set_modulation(trigger=fygen.TRIGGER_EXTERNAL_AC)
    self.fy.set_modulation(trigger=fygen.TRIGGER_EXTERNAL_IN)
    self.fy.set_modulation(trigger=fygen.TRIGGER_MANUAL)
    self.fy.set_modulation(trigger=fygen.TRIGGER_EXTERNAL_DC)

    self.fy.set_modulation(burst_count=76)

    self.fy.set_modulation(am_attenuation=0.121)

    self.fy.set_modulation(pm_bias_degrees=23.4)

    self.fy.set_modulation(hop_freq_hz=1234)
    self.fy.set_modulation(hop_freq_uhz=1234)

    self.fy.set_modulation(fm_bias_freq_hz=1234)
    self.fy.set_modulation(fm_bias_freq_uhz=1234)

    self.assertEqual(
        'WPF0\n'
        'WPF1\n'
        'WPF2\n'
        'WPF3\n'
        'WPF4\n'
        'WPF5\n'
        'WPF6\n'

        'WPM0\n'
        'WPM1\n'
        'WPM1\n'
        'WPM2\n'
        'WPM3\n'

        'WPN76\n'

        'WPR12.1\n'

        'WPP23.4\n'

        'WFK00001234000000\n'
        'WFK00000000001234\n'

        'WFM00001234000000\n'
        'WFM00000000001234\n',
        self.output.getvalue())

  def test_invalid_modulation_mode(self):
    """Tries to set invalid modulation modes."""
    with self.assertRaises(fygen.InvalidModulationModeError):
      self.fy.set_modulation(mode=-1)
    with self.assertRaises(fygen.InvalidModulationModeError):
      self.fy.set_modulation(mode=7)

  def test_invalid_burst_cycle_count(self):
    """Tries to set an invalid burst cycle count."""
    with self.assertRaises(fygen.InvalidBurstCycleCountError):
      self.fy.set_modulation(burst_count=0)

  def test_invalid_trigger_mode(self):
    """Tries to set invalid trigger modes."""
    with self.assertRaises(fygen.InvalidTriggerModeError):
      self.fy.set_modulation(trigger=-1)
    with self.assertRaises(fygen.InvalidTriggerModeError):
      self.fy.set_modulation(trigger=4)

  def test_invalid_am_attenuation(self):
    """Tries to set an invalid rate percentage."""
    with self.assertRaises(fygen.InvalidAMAttenuationError):
      self.fy.set_modulation(am_attenuation=-0.1)
    with self.assertRaises(fygen.InvalidAMAttenuationError):
      self.fy.set_modulation(am_attenuation=2.1)

  def test_invalid_hop_frequency(self):
    """Tries to set an invalid hop frequency."""
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set_modulation(hop_freq_hz=-0.1)
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set_modulation(hop_freq_uhz=-0.1)
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set_modulation(hop_freq_hz=1, hop_freq_uhz=1)

  def test_invalid_fm_bias_frequency(self):
    """Tries to set an invalid fm bias frequency."""
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set_modulation(fm_bias_freq_hz=-0.1)
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set_modulation(fm_bias_freq_uhz=-0.1)
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set_modulation(fm_bias_freq_hz=1, fm_bias_freq_uhz=1)

  def test_get_enable(self):
    """Gets the current enable status."""
    fs = FakeSerial([b'255\n', b'0\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual(True, fy.get(0, 'enable'))
    self.assertEqual(False, fy.get(1, 'enable'))
    self.assertEqual('RMN\nRFN\n', fs.getvalue())

  def test_get(self):
    """Calls get with no arguments."""
    fs = FakeSerial([
        b'50000\n',  # duty cycle
        b'255\n',  # enable
        b'12345.6789\n',  # freq hz
        b'12340\n',  # offset volts
        b'189300\n',  # phase degrees
        b'123400\n',  # volts
        b'4\n',  # wave
    ])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True
    self.assertEqual({
        'duty_cycle': 0.5,
        'enable': True,
        'freq_hz': 12345,
        'offset_volts': 12.34,
        'phase_degrees': 189.3,
        'volts': 12.34,
        'wave': 'dc',
    }, fy.get())
    self.assertEqual(
        'RMD\n'
        'RMN\n'
        'RMF\n'
        'RMO\n'
        'RMP\n'
        'RMA\n'
        'RMW\n'
        '',
        fs.getvalue())

  def test_get_wave(self):
    """Gets the current wave."""
    fs = FakeSerial([b'4\n', b'4\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True
    self.assertEqual('dc', fy.get(0, 'wave'))
    self.assertEqual({'wave': 'tri'}, fy.get(1, ('wave',)))
    self.assertEqual('RMW\nRFW\n', fs.getvalue())

  def test_get_invalid_channel(self):
    """Tries to pass an invalid channel."""
    with self.assertRaises(fygen.InvalidChannelError):
      self.fy.get(2, 'wave')

  def test_get_invalid_parameter(self):
    """Tries to pass an invalid parameter."""
    with self.assertRaises(fygen.UnknownParameterError):
      self.fy.get(0, 'foo')

  def test_get_invalid_waveform_index(self):
    """Unrecognized wave index is returned by the siggen."""
    fs = FakeSerial([b'100\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True
    with self.assertRaises(fygen.UnknownWaveformError):
      fy.get(0, 'wave')

  def test_get_freq1(self):
    """Gets the frequency in Hz."""
    fs = FakeSerial([b'12345.6789\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual(12345, fy.get(0, 'freq_hz'))
    self.assertEqual('RMF\n', fs.getvalue())

  def test_get_freq2(self):
    """Gets the frequency in uHz."""
    fs = FakeSerial([b'12345.6789\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual(12345678900, fy.get(1, 'freq_uhz'))
    self.assertEqual('RFF\n', fs.getvalue())

  def test_get_volts(self):
    """Gets the amplitude voltage."""
    fs = FakeSerial([b'123400\n', b'5000\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual(12.34, fy.get(0, 'volts'))
    self.assertEqual(0.5, fy.get(1, 'volts'))
    self.assertEqual('RMA\nRFA\n', fs.getvalue())

  def test_get_offset_volts(self):
    """Gets the offset voltage."""
    fs = FakeSerial([b'12340\n', b'4294962296\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual(12.34, fy.get(0, 'offset_volts'))
    self.assertEqual(-5, fy.get(1, 'offset_volts'))
    self.assertEqual('RMO\nRFO\n', fs.getvalue())

  def test_get_phase_degrees(self):
    """Gets the phase angle."""
    fs = FakeSerial([b'0\n', b'189300\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual(0, fy.get(0, 'phase_degrees'))
    self.assertEqual(189.3, fy.get(1, 'phase_degrees'))
    self.assertEqual('RMP\nRFP\n', fs.getvalue())

  def test_get_duty_cycle(self):
    """Gets the duty cycle."""
    fs = FakeSerial([b'50000\n', b'10500\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual(0.5, fy.get(0, 'duty_cycle'))
    self.assertEqual(0.105, fy.get(1, 'duty_cycle'))
    self.assertEqual('RMD\nRFD\n', fs.getvalue())

  def test_set_waveform(self):
    """Sets a custom waveform."""
    wave = [-1.0, 0.0, 1.0, 0.0] * 2048
    self.fy.set_waveform(5, values=wave)
    expected = 'DDS_WAVE5\n'
    expected += '00000020FF3F002000000020FF3F0020\n' * 1024
    self.assertEqual(expected, self.output.getvalue())

  def test_set_raw_waveform(self):
    """Sets a custom waveform using raw values."""
    wave = [1, 2, 3, 4] * 2048
    self.fy.set_waveform(6, raw_values=wave)
    expected = 'DDS_WAVE6\n'
    expected += '01000200030004000100020003000400\n' * 1024
    self.assertEqual(expected, self.output.getvalue())

  def test_bad_waveform_index(self):
    """Passes an invalid waveform index."""
    with self.assertRaises(fygen.UnknownWaveformError):
      self.fy.set_waveform(0, raw_values=[0]*8192)

  def test_raw_value_conflict_error(self):
    """Passes both values and raw_values."""
    with self.assertRaises(fygen.RawValueConflictError):
      self.fy.set_waveform(1, values=[0.0] * 8192, raw_values=[0]*8192)

  def test_value_count_error(self):
    """Passes the wrong array size."""
    with self.assertRaises(fygen.ValueCountError):
      self.fy.set_waveform(1, raw_values=[0]*8191)
    with self.assertRaises(fygen.ValueCountError):
      self.fy.set_waveform(1, values=[0.0]*8191)

  def test_cmd_noack_error(self):
    """Simulates the siggen not responsing to the DDR_WAVE request."""
    fs = FakeSerial([b'0\n', b'0\n', b'E\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True
    with self.assertRaises(fygen.CommandNotAcknowledgedError):
      fy.set_waveform(1, values=[0.0]*8192)

  def test_data_noack_error(self):
    """Simulates the siggen not responsing to data sent."""
    fs = FakeSerial([b'0\n', b'0\n', b'W\n', b'E\n'])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True
    with self.assertRaises(fygen.CommandNotAcknowledgedError):
      fy.set_waveform(1, values=[0.0]*8192)

  def test_set_sweep(self):
    """Tries every known sweep variable."""
    self.fy.set_sweep(enable=False, mode=fygen.SWEEP_FREQUENCY)

    self.fy.set_sweep(mode=fygen.SWEEP_AMPLITUDE)
    self.fy.set_sweep(mode=fygen.SWEEP_OFFSET)
    self.fy.set_sweep(mode=fygen.SWEEP_DUTY_CYCLE)

    self.fy.set_sweep(log_sweep=False)
    self.fy.set_sweep(log_sweep=True)

    self.fy.set_sweep(source=fygen.SWEEP_SOURCE_TIME)
    self.fy.set_sweep(source=fygen.SWEEP_SOURCE_VCO_IN)

    self.fy.set_sweep(time_seconds=10.1)

    self.fy.set_sweep(start_freq_hz=1234.56, end_freq_hz=1234.56)

    self.fy.set_sweep(start_volts=12.3456, end_volts=12.3456)

    self.fy.set_sweep(start_offset_volts=-12.3456, end_offset_volts=-12.3456)

    self.fy.set_sweep(start_duty_cycle=0.1, end_duty_cycle=0.9)

    self.assertEqual(
        'SBE0\n'
        'SOB0\n'

        'SBE0\n'
        'SOB1\n'
        'SBE0\n'
        'SOB2\n'
        'SBE0\n'
        'SOB3\n'

        'SBE0\n'
        'SMO0\n'
        'SBE0\n'
        'SMO1\n'

        'SBE0\n'
        'SXY0\n'
        'SBE0\n'
        'SXY1\n'

        'SBE0\n'
        'STI10.10\n'

        'SBE0\n'
        'SST1234.6\n'
        'SEN1234.6\n'

        'SBE0\n'
        'SST12.346\n'
        'SEN12.346\n'

        'SBE0\n'
        'SST-2.346\n'
        'SEN-2.346\n'

        'SBE0\n'
        'SST10.0\n'
        'SEN90.0\n'

        '',
        self.output.getvalue())

  def test_sweep_enable(self):
    """Tries to enable sweep mode."""
    with self.assertRaises(fygen.PossibleFirmwareBugError):
      self.fy.set_sweep(enable=True)

  def test_sweep_enable_forced(self):
    """Tries to enable sweep mode."""
    fy = fygen.FYGen(port=self.output)
    fy.force_sweep_enable = True
    fy.set_sweep(enable=True)
    self.assertEqual('SBE1\n', self.output.getvalue())

  def test_invalid_sweep_mode(self):
    """Sets an invalid sweep mode."""
    with self.assertRaises(fygen.InvalidSweepModeError):
      self.fy.set_sweep(mode=5)

  def test_invalid_sweep_source(self):
    """Sets an invalid sweep source."""
    with self.assertRaises(fygen.InvalidSweepSourceError):
      self.fy.set_sweep(source=2)

  def test_sweep_vco_with_time(self):
    """Sets a time with a VCO source."""
    with self.assertRaises(fygen.InvalidSweepSourceError):
      self.fy.set_sweep(source=fygen.SWEEP_SOURCE_VCO_IN, time_seconds=1)

  def test_invalid_sweep_time(self):
    """Sets an invalid sweep time."""
    with self.assertRaises(fygen.InvalidSweepTimeError):
      self.fy.set_sweep(time_seconds=0)

  def test_sweep_start_freq_in_invalid_mode(self):
    """Sets start_freq_hz in amplitude mode."""
    with self.assertRaises(fygen.InvalidModeError):
      self.fy.set_sweep(mode=fygen.SWEEP_AMPLITUDE, start_freq_hz=1000)

  def test_invalid_start_freq(self):
    """Sets start_freq_hz to zero."""
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set_sweep(start_freq_hz=0)

  def test_sweep_end_freq_in_invalid_mode(self):
    """Sets end_freq_hz in amplitude mode."""
    with self.assertRaises(fygen.InvalidModeError):
      self.fy.set_sweep(mode=fygen.SWEEP_AMPLITUDE, end_freq_hz=1000)

  def test_invalid_end_freq(self):
    """Sets end_freq_hz to zero."""
    with self.assertRaises(fygen.InvalidFrequencyError):
      self.fy.set_sweep(end_freq_hz=0)

  def test_sweep_start_volts_in_invalid_mode(self):
    """Sets start_volts in amplitude mode."""
    with self.assertRaises(fygen.InvalidModeError):
      self.fy.set_sweep(mode=fygen.SWEEP_FREQUENCY, start_volts=10)

  def test_invalid_start_volts(self):
    """Sets start_volts to zero and too high."""
    with self.assertRaises(fygen.InvalidVoltageError):
      self.fy.set_sweep(start_volts=0)
    with self.assertRaises(fygen.InvalidVoltageError):
      self.fy.set_sweep(start_volts=30)

  def test_sweep_end_volts_in_invalid_mode(self):
    """Sets end_volts in amplitude mode."""
    with self.assertRaises(fygen.InvalidModeError):
      self.fy.set_sweep(mode=fygen.SWEEP_FREQUENCY, end_volts=10)

  def test_invalid_end_volts(self):
    """Sets end_volts to zero and too high."""
    with self.assertRaises(fygen.InvalidVoltageError):
      self.fy.set_sweep(end_volts=0)
    with self.assertRaises(fygen.InvalidVoltageError):
      self.fy.set_sweep(end_volts=30)

  def test_sweep_start_offset_volts_in_invalid_mode(self):
    """Sets start_offset_volts in amplitude mode."""
    with self.assertRaises(fygen.InvalidModeError):
      self.fy.set_sweep(mode=fygen.SWEEP_FREQUENCY, start_offset_volts=10)

  def test_invalid_start_offset_volts(self):
    """Sets start_offset_volts too high."""
    with self.assertRaises(fygen.InvalidVoltageError):
      self.fy.set_sweep(start_offset_volts=30)

  def test_sweep_end_offset_volts_in_invalid_mode(self):
    """Sets end_offset_volts in amplitude mode."""
    with self.assertRaises(fygen.InvalidModeError):
      self.fy.set_sweep(mode=fygen.SWEEP_FREQUENCY, end_offset_volts=10)

  def test_invalid_end_offset_volts(self):
    """Sets end_offset_volts too high."""
    with self.assertRaises(fygen.InvalidVoltageError):
      self.fy.set_sweep(end_offset_volts=30)

  def test_sweep_start_duty_cycle_in_invalid_mode(self):
    """Sets start_duty_cycle in amplitude mode."""
    with self.assertRaises(fygen.InvalidModeError):
      self.fy.set_sweep(mode=fygen.SWEEP_FREQUENCY, start_duty_cycle=0.1)

  def test_invalid_start_duty_cycle(self):
    """Sets start_duty_cycle to zero and too high."""
    with self.assertRaises(fygen.InvalidDutyCycleError):
      self.fy.set_sweep(start_duty_cycle=0)
    with self.assertRaises(fygen.InvalidDutyCycleError):
      self.fy.set_sweep(start_duty_cycle=1)

  def test_sweep_end_duty_cycle_in_invalid_mode(self):
    """Sets end_duty_cycle in amplitude mode."""
    with self.assertRaises(fygen.InvalidModeError):
      self.fy.set_sweep(mode=fygen.SWEEP_FREQUENCY, end_duty_cycle=0.9)

  def test_invalid_end_duty_cycle(self):
    """Sets end_duty_cycle to zero and one."""
    with self.assertRaises(fygen.InvalidDutyCycleError):
      self.fy.set_sweep(end_duty_cycle=0)
    with self.assertRaises(fygen.InvalidDutyCycleError):
      self.fy.set_sweep(end_duty_cycle=1)

  def test_set_measurement(self):
    """Tests all combinations of set_measurement."""
    self.fy.set_measurement(reset_counter=True)

    self.fy.set_measurement(pause=False)
    self.fy.set_measurement(pause=True)

    self.fy.set_measurement(gate_time=fygen.GATE_TIME_1S)
    self.fy.set_measurement(gate_time=fygen.GATE_TIME_10S)
    self.fy.set_measurement(gate_time=fygen.GATE_TIME_100S)

    self.fy.set_measurement(coupling=fygen.COUPLING_DC)
    self.fy.set_measurement(coupling=fygen.COUPLING_AC)

    self.assertEqual(
        'WCZ0\n'

        'WCP1\n'
        'WCP0\n'

        'WCG0\n'
        'WCG1\n'
        'WCG2\n'

        'WCC1\n'
        'WCC0\n',
        self.output.getvalue())

  def test_set_measurement_invalid_gate_time(self):
    """Passes an invalid gate_time."""
    with self.assertRaises(fygen.InvalidGateTimeError):
      self.fy.set_measurement(gate_time=4)

  def test_set_measurement_invalid_coupling(self):
    """Passes an invalid coupling."""
    with self.assertRaises(fygen.InvalidCouplingError):
      self.fy.set_measurement(coupling=2)

  def test_get_measurement(self):
    """Gets all measurements."""
    fs = FakeSerial([
        b'0\n',  # gate mode = 1S
        b'0000000668\n',  # freq_hz
        b'0000060668\n',  # period_sec
        b'0000012345\n',  # positive_width_sec
        b'0000054321\n',  # negative_width_sec
        b'0000000541\n',  # duty cycle
    ])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True
    self.assertEqual(
        {
            'freq_hz': 668.0,
            'period_sec': 6.0668e-5,
            'positive_width_sec': 1.2345e-5,
            'negative_width_sec': 5.4321e-5,
            'duty_cycle': 0.541
        },
        fy.get_measurement())

  def test_get_measurement_counter(self):
    """Gets the counter measurement."""
    fs = FakeSerial([
        b'0000000669\n',  # counter
    ])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True
    self.assertEqual({'counter': 669}, fy.get_measurement({'counter'}))

  def test_get_measurement_frequency(self):
    """Gets frequencies."""
    fs = FakeSerial([
        b'0\n',  # gate mode = 1S
        b'0000000668\n',  # freq_hz
        b'1\n',  # gate mode = 10S
        b'0000000668\n',  # freq_hz
        b'2\n',  # gate mode = 100S
        b'0000000668\n',  # freq_hz
    ])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True
    self.assertEqual(668.0, fy.get_measurement('freq_hz'))
    self.assertEqual(66.8, fy.get_measurement('freq_hz'))
    self.assertEqual(6.68, fy.get_measurement('freq_hz'))

  def test_get_measurement_invalid_gate_time(self):
    """siggen returns an unexpected gate time mode."""
    fs = FakeSerial([
        b'x\n',  # gate mode = ???
        b'0000000668\n',  # freq_hz
    ])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True
    with self.assertRaises(fygen.InvalidGateTimeError):
      fy.get_measurement('freq_hz')

  def test_get_measurement_unknown_parameter(self):
    """requests an unknown parameter."""
    with self.assertRaises(fygen.UnknownParameterError):
      self.fy.get_measurement('foo')

  def test_save(self):
    """Saves parameters."""
    self.fy.save(2)
    self.assertEqual('USN02\n', self.output.getvalue())

  def test_load(self):
    """Loads parameters."""
    self.fy.load(3)
    self.assertEqual('ULN03\n', self.output.getvalue())

  def test_set_synchronization(self):
    """Sets all known sync modes."""
    self.fy.set_synchronization(wave=True)
    self.fy.set_synchronization(freq=True)
    self.fy.set_synchronization(volts=True)
    self.fy.set_synchronization(offset_volts=True)
    self.fy.set_synchronization(duty_cycle=True)

    self.assertEqual(
        'USA0\n'
        'USA1\n'
        'USA2\n'
        'USA3\n'
        'USA4\n'
        '',
        self.output.getvalue())

  def test_get_synchronization(self):
    """Gets all known sync modes."""
    fs = FakeSerial([
        b'0\n',  # duty cycle
        b'255\n',  # freq
        b'0\n',  # offset_volts
        b'255\n',  # volts
        b'0\n',  # wave
    ])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual({
        'duty_cycle': False,
        'freq': True,
        'offset_volts': False,
        'volts': True,
        'wave': False,
    }, fy.get_synchronization())
    self.assertEqual(
        'RSA4\n'
        'RSA1\n'
        'RSA3\n'
        'RSA2\n'
        'RSA0\n'
        '',
        fs.getvalue())

  def test_get_synchronization_dict(self):
    """Gets all known sync modes."""
    fs = FakeSerial([
        b'255\n',  # duty cycle
    ])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual(
        {'duty_cycle': True},
        fy.get_synchronization(('duty_cycle',)))
    self.assertEqual('RSA4\n', fs.getvalue())

  def test_get_synchronization_single(self):
    """Gets all known sync modes."""
    fs = FakeSerial([
        b'0\n',  # wave
    ])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual(False, fy.get_synchronization('wave'))
    self.assertEqual('RSA0\n', fs.getvalue())

  def test_get_invalid_sync_mode(self):
    """Gets an invalid sync mode."""
    with self.assertRaises(fygen.InvalidSynchronizationMode):
      self.fy.get_synchronization('foo')

  def test_set_buzzer(self):
    """Sets the buzzer."""
    self.fy.set_buzzer(False)
    self.fy.set_buzzer(True)
    self.assertEqual('UBZ0\nUBZ1\n', self.output.getvalue())

  def test_get_buzzer(self):
    """Gets buzzer state."""
    fs = FakeSerial([
        b'0\n',
        b'255\n',
    ])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertFalse(fy.get_buzzer())
    self.assertTrue(fy.get_buzzer())

    self.assertEqual('RBZ\nRBZ\n', fs.getvalue())

  def test_set_uplink(self):
    """Tries all setuplink combinations."""
    self.fy.set_uplink(is_master=True, enable=False)
    self.fy.set_uplink(is_master=False, enable=True)

    self.assertEqual(
        'UUL0\n'
        'UMS0\n'

        'UMS1\n'
        'UUL1\n'
        '',
        self.output.getvalue())

  def test_get_uplink(self):
    """Gets uplink settings."""
    fs = FakeSerial([
        b'0\n',
        b'255\n',
        b'255\n',
    ])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual({'enable': False, 'is_master': False}, fy.get_uplink())
    self.assertTrue(fy.get_uplink('enable'))

    self.assertEqual('RUL\nRMS\nRUL\n', fs.getvalue())

  def test_get_id(self):
    """Gets device id."""
    fs = FakeSerial([b'12345\n',])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual('12345', fy.get_id())
    self.assertEqual('UID\n', fs.getvalue())

  def test_get_model(self):
    """Gets device model."""
    fs = FakeSerial([b'fy2300\n',])
    fy = fygen.FYGen(port=fs)
    fy.is_serial = True

    self.assertEqual('fy2300', fy.get_model())
    self.assertEqual('UMO\n', fs.getvalue())

  def test_auto_detect_on_init(self):
    """Autodetects runs on FYGen init"""
    fs = FakeSerial([b'FY6900-60\n',])
    fy = fygen.FYGen(port=fs, _port_is_serial=True)

    self.assertEqual('fy6900', fy.device_name)
    self.assertEqual('UMO\n', fs.getvalue())

  def test_auto_detect(self):
    self.assertEqual(fygen.detect_device('FY6900-60M'), 'fy6900')
    self.assertEqual(fygen.detect_device('FY2350H'), 'fy2300')

  def test_autodetect_no_conflict(self):
    """
    Make sure no exact match maps to the wrong device.
    This is just to future proof in case two devices with
    leading 4-char prefix gets added that have different waveform id's
    """
    for device in SUPPORTED_DEVICES:
      self.assertEqual(fygen.detect_device(device), device)

if __name__ == '__main__':
  unittest.main()
