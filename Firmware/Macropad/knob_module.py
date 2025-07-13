from sched import scheduler
import struct
from time import time
from base_module import BaseModule, ModuleType
from twiman import TWIDevice


class KnobDevice(TWIDevice):
    """An extension of TWIDevice for knob devices"""

    def __init__(self, addr, channel, serial_id):
        super().__init__(addr, channel, serial_id)
        self.num_encoders = 0
        self.rotation_delta = []
        self.button_pressed = []
        self.button_released = []


# Should even be more refreshed frequently to ensure extra "responsiveness"
class KnobModule(BaseModule):
    """The knob module for handling knobbing devices. duh"""

    def __init__(self, twiman):
        super().__init__(twiman, ModuleType.KNOBS)
        self.global_encoder_count = 0
        self.knob_lookup = {}  # super shitty way to do this
        self.update_interval = 50  # ms

        self.map = None

    def twiman_new_device_callback(self, device):
        if device.type_id == self.target_type_id:  # ?????
            friend_code = device.get_friend_code()
            knob_device = KnobDevice(device.addr, device.channel, device.raw_serial)
            encoder_count = self.get_encoder_count(knob_device)

            knob_device.num_encoders = encoder_count
            # set initial values to 0. I do not know if this can be in the constructor.
            knob_device.rotation_delta = [0] * encoder_count
            knob_device.button_pressed = [0] * encoder_count
            knob_device.button_released = [0] * encoder_count

            # key = (slider_device.addr, slider_device.channel, friend_code)
            self.knob_lookup[friend_code] = encoder_count
            self.global_encoder_count += encoder_count

            self.devices.append(knob_device)
            print(f"new knob device detected: {friend_code}")

    def twiman_removed_device_callback(self, device):
        if device in self.devices:
            friend_code = device.get_friend_code()
            # key = (device.addr, device.channel, friend_code)
            num_encoders = self.knob_lookup.pop(friend_code, None)

            if num_encoders is not None:
                self.global_encoder_count -= num_encoders
                print(f"knob device removed: {friend_code} ({num_encoders} encoders)")
            else:
                print(f"knob device removed: {friend_code} (unknown encoder count)")

            self.devices.remove(device)
            print(f"knob device removed: {device.get_friend_code()}")

    def get_encoder_count(self, device: KnobDevice):
        """Return the number of encoders in a device"""
        self.twiman.select_channel(device.channel)

        command = bytes([0x02, 0x03])
        buffer = bytearray(1)
        self.twiman.send_command(device.addr, command)
        time.sleep(0.005)  # 5 ms
        self.twiman.read_from_device(device.addr, buffer)

        return buffer[0]

    def get_encoder_values(
        self, device: KnobDevice
    ) -> tuple[list[int], list[int], list[int]]:
        """Get the slider values from a device"""
        self.twiman.select_channel(device.channel)
        num_encoders = device.num_encoders
        total_bytes = num_encoders * 3  # int8 + uint8 + uint8

        buf = bytearray(total_bytes)
        self.twiman.readfrom_into(device.addr, buf)

        # struct KnobChanges
        # {
        #   int8_t rotation_delta[NUM_ENCODERS];
        #   uint8_t button_pressed[NUM_ENCODERS];
        #   uint8_t button_released[NUM_ENCODERS];
        # };

        format = f"<{num_encoders}b{num_encoders}B{num_encoders}B"
        unpacked = struct.unpack(format, buf)
        rotation_delta = list(unpacked[:num_encoders])
        button_pressed = list(unpacked[num_encoders : 2 * num_encoders])
        button_released = list(unpacked[2 * num_encoders :])

        return (
            rotation_delta,
            button_pressed,
            button_released,  # ignored for now
        )

    def get_knob_index(self, device: KnobDevice, encoder_idx: int):
        """A stable index for our KNOBS. When a device is removed the index will change, otherwise it will not."""  # :)
        knob_index = 0
        for d in self.devices:
            if d == device:
                break
            knob_index += d.num_encoders
        return knob_index + encoder_idx

    def handle_encoder_rotation(self, device: KnobDevice, encoder_idx: int, delta: int):
        """Handle the rotation of the encoder"""
        if not self.map:
            return
        layer_id = self.keyboard.active_layer[0]

        encoder_index = self.get_knob_index(device, encoder_idx)

        encoder_mapping = self.map[layer_id][encoder_index]

        steps = abs(delta)
        direction_key = (
            encoder_mapping[0] if delta < 0 else encoder_mapping[1]  # CCW : CW
        )

        for _ in range(steps):
            self.keyboard.tap_key(direction_key)

        print(
            f"encoder {encoder_idx} ({device.get_friend_code()}) rotated: {delta} steps"
        )

    def handle_encoder_pressed(self, device: KnobDevice, encoder_idx: int):
        """Handle the button press of the encoder"""
        if not self.map:
            return
        layer_id = self.keyboard.active_layer[0]

        encoder_index = self.get_knob_index(device, encoder_idx)

        encoder_mapping = self.map[layer_id][encoder_index]
        button_key = encoder_mapping[2]  # button is index 2 (last one)
        self.keyboard.tap_key(button_key)

        print(f"encoder {encoder_idx} ({device.get_friend_code()}) pressed")

    def update_knobs(self):
        """Update all knobs"""
        for device in self.devices:
            rotation_delta, button_pressed, button_released = self.get_encoder_values(
                device
            )
            device.rotation_delta = rotation_delta
            device.button_pressed = button_pressed
            device.button_released = button_released

            print(f"knob values: {rotation_delta}")
            print(f"knob pressed: {button_pressed}")
            print(f"knob released: {button_released}")

            for idx in range(device.num_encoders):
                current_delta = device.rotation_delta[idx]
                if rotation_delta != 0:
                    self.handle_encoder_rotation(device, idx, current_delta)
                if device.button_pressed[idx]:
                    self.handle_encoder_pressed(device, idx)

    def schedule_tasks(self):
        """Schedule the knob update task"""
        scheduler.create_task(self.update_knobs, period_ms=self.update_interval)

    def mod_during_bootup(self, keyboard):
        self.schedule_tasks()
