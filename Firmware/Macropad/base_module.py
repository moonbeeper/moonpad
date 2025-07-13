from enum import Enum
from kmk.modules import Module
from twiman import TWIDevice, TWIManager


class ModuleType(Enum):
    KNOBS = (0x01,)  # i love ruff.
    SLIDERS = (0x02,)


class BaseModule(Module):
    """Base class for all modules in the moonpad"""

    # i hate this "type safety" stuff. Makes me confident tho.
    def __init__(self, twiman: TWIManager, target_type_id: ModuleType):
        self.twiman = twiman
        self.target_type_id = target_type_id.value[
            0  # I think this is right because is a tuple with one element
        ]
        self.devices = []
        self.keyboard = None

        twiman.add_device_callback(self.twiman_new_device_callback)
        twiman.add_removal_callback(self.twiman_removed_device_callback)

    def twiman_new_device_callback(self, device: TWIDevice):
        return

    def twiman_removed_device_callback(self, device: TWIDevice):
        return

    def mod_during_bootup(self, keyboard):
        """Called during the bootup process of the keyboard."""
        return

    def during_bootup(self, keyboard):
        self.keyboard = keyboard
        self.mod_during_bootup(keyboard)

    def before_matrix_scan(self, keyboard):
        return

    def after_matrix_scan(self, keyboard):
        return

    def process_key(self, keyboard, key, is_pressed, int_coord):
        return key

    def before_hid_send(self, keyboard):
        return

    def after_hid_send(self, keyboard):
        return

    def on_powersave_enable(self, keyboard):
        return

    def on_powersave_disable(self, keyboard):
        return

    def deinit(self, keyboard):
        pass  # alright
