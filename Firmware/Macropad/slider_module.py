import struct
from time import time
from base_module import BaseModule, ModuleType
from kmk import scheduler
from lib.Adafruit_CircuitPython_MIDI.adafruit_midi import MIDI
from lib.Adafruit_CircuitPython_MIDI.adafruit_midi.control_change import ControlChange
import usb_midi
from twiman import TWIDevice
from utils import map_value


class SliderDevice(TWIDevice):
    """An extension of TWIDevice for slider devices"""

    def __init__(self, addr, channel, serial_id):
        super().__init__(addr, channel, serial_id)
        self.num_sliders = 0
        self.slider_values = []
        self.old_slider_values = []
        self.slider_changed = []


# Should be refreshed frequently to ensure "responsiveness"
class SliderModule(BaseModule):
    """The slider module for handling slider devices. duh"""

    def __init__(self, twiman):
        super().__init__(twiman, ModuleType.SLIDERS)
        self.global_slider_count = 0
        self.slider_lookup = {}  # super shitty way to do this
        self.slider_deadzone = 5  # TODO: DOUBLE DEADZONE IN PYTHON AND CPP!!!!!!!
        self.update_interval = 100  # ms

        self.midi = MIDI(midi_out=usb_midi.ports[1], out_channel=0)

    def twiman_new_device_callback(self, device):
        if device.type_id == self.target_type_id:  # ?????
            friend_code = device.get_friend_code()
            slider_device = SliderDevice(device.addr, device.channel, device.raw_serial)
            slider_count = self.get_slider_count(slider_device)

            slider_device.num_sliders = slider_count
            # set initial values to 0. I do not know if this can be in the constructor.
            slider_device.slider_values = [0] * slider_count
            slider_device.old_slider_values = [0] * slider_count

            # key = (slider_device.addr, slider_device.channel, friend_code)
            self.slider_lookup[friend_code] = slider_count
            self.global_slider_count += slider_count

            self.devices.append(slider_device)
            print(f"new slider device detected: {friend_code}")

    def twiman_removed_device_callback(self, device):
        if device in self.devices:
            friend_code = device.get_friend_code()
            # key = (device.addr, device.channel, friend_code)
            num_sliders = self.slider_lookup.pop(friend_code, None)

            if num_sliders is not None:
                self.global_slider_count -= num_sliders
                print(f"slider device removed: {friend_code} ({num_sliders} sliders)")
            else:
                print(f"slider device removed: {friend_code} (unknown slider count)")

            self.devices.remove(device)
            print(f"slider device removed: {device.get_friend_code()}")

    def get_slider_count(self, device: SliderDevice):
        """Return the number of sliders in a device"""
        self.twiman.select_channel(device.channel)

        command = bytes([0x02, 0x03])
        buffer = bytearray(1)
        self.twiman.send_command(device.addr, command)
        time.sleep(0.005)  # 5 ms
        self.twiman.read_from_device(device.addr, buffer)

        return buffer[0]

    def get_slider_values(self, device: SliderDevice) -> tuple[list[int], list[int]]:
        """Get the slider values from a device"""
        self.twiman.select_channel(device.channel)
        num_sliders = device.num_sliders
        total_bytes = num_sliders * 2 + num_sliders * 1  # uint16 + uint8

        buf = bytearray(total_bytes)
        self.twiman.readfrom_into(device.addr, buf)

        # struct SliderChanges
        # {
        #   uint16_t slider_value[NUM_SLIDERS];
        #   uint8_t slider_changed[NUM_SLIDERS];
        # };

        format = f"<{num_sliders}H{num_sliders}B"
        unpacked = struct.unpack(format, buf)
        slider_values = list(unpacked[:num_sliders])  # first part is unint16
        slider_changed = list(unpacked[num_sliders:])  # second part is uint8

        return slider_values, slider_changed  # will ignore the "slider_changed" for now

    def update_sliders(self):
        """Update all sliders"""
        for device in self.devices:
            slider_values, slider_changed = self.get_slider_values(device)
            device.slider_values = slider_values
            device.slider_changed = slider_changed

            print(f"slider values: {slider_values}")
            print(f"slider changed: {slider_changed}")

            for idx in range(device.num_sliders):
                current_value = slider_values[idx]
                if (  # holy format ruff
                    abs(device.old_slider_values[idx] - current_value)
                    > self.slider_deadzone
                ):
                    device.old_slider_values[idx] = current_value
                    self.update_midi(device, idx, current_value)

    def get_midi_index(self, device: SliderDevice, slider_idx: int):
        """A stable index for our MIDI messages. When a device is removed the index will change, otherwise it will not."""
        midi_index = 0
        for d in self.devices:
            if d == device:
                break
            midi_index += d.num_sliders
        return midi_index + slider_idx

    def update_midi(self, device: SliderDevice, slider_idx: int, value: int):
        """Send a MIDI Control Change message for a slider value"""
        midi_index = self.get_midi_index(device, slider_idx)
        mapped_value = int(map_value(value, 0, 1023, 0, 127))

        self.midi.send(ControlChange(midi_index, mapped_value))
        print(
            f"slider {slider_idx} on device {device.get_friend_code()} updated to {mapped_value}"
        )

    def schedule_tasks(self):
        """Schedule the slider update task"""
        scheduler.create_task(self.update_sliders, period_ms=self.update_interval)

    def mod_during_bootup(self, keyboard):
        self.schedule_tasks()
