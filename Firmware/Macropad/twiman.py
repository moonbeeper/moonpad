try:
    from typing import Callable, Literal, List  # comes from kmk code
    from circuitpython_typing import (  # type: ignore
        ReadableBuffer,
        WriteableBuffer,
    )  # isn't needed in the bundle at runtime :·)
except ImportError:
    pass

from binascii import hexlify
import time
import board
import busio
from kmk import scheduler


class TWIDevice:
    """I2C device metadata class."""

    def __init__(self, addr, channel, raw_friend_code):
        self.addr = addr
        self.channel = channel
        self.raw_friend_code = raw_friend_code

        self.type_id = raw_friend_code[0]
        self.raw_serial = raw_friend_code[1:]
        self.serial = hexlify(self.raw_serial).decode("ascii")

    def get_friend_code(self):
        """Get the friend code as a string."""
        return f"{self.type_id:02X}{self.serial}"

    # This is so a class that inherits can compare itself to a TWIDevice. This lets us be able to delete and... compare.
    def __eq__(self, other):
        return (
            isinstance(other, TWIDevice)
            and self.addr == other.addr
            and self.channel == other.channel
        )

    def __hash__(self):
        return hash((self.addr, self.channel))


class TWIManager:
    """hello am twiman. I manage I2C devices on a multiplexer."""

    def __init__(
        self,
        sda_pin=board.D4,
        scl_pin=board.D5,
        mux_addr=0x70,
        mux_channels=1,
        default_addr=0x03,
    ):
        self.i2c = busio.I2C(sda=sda_pin, scl=scl_pin, frequency=400000)
        self.mux_addr = mux_addr
        self.mux_channels = mux_channels
        self.default_addr = default_addr

        self.max_addr = 0x77
        self.channels = range(self.mux_channels)
        self.active_addresses = {channel: set() for channel in self.channels}
        self.next_addr = {channel: 0x04 for channel in self.channels}
        self.freed_addresses = {channel: [] for channel in self.channels}

        self.registered_devices: list[TWIDevice] = []

        self.new_device_callbacks: list[Callable[[TWIDevice], None]] = []
        self.removed_device_callbacks: list[Callable[[TWIDevice], None]] = []

        # ! seconds !
        # self.last_health_check = 0
        self.health_check_interval = 2
        # self.last_discovery = 0
        self.discovery_interval = 5
        # self.batch_delay = 2.5 :(

    def send_command(self, device: TWIDevice, command: bytes):
        """Send command to a device"""
        try:
            while not self.i2c.try_lock():
                time.sleep(0.001)  # 1ms
                pass

            self.i2c.writeto(device.addr, command)

            return True
        except Exception as e:
            print(f"failed to send command to device: {e}")
            return False
        finally:
            self.i2c.unlock()

    def read_from_device(self, device: TWIDevice, num_bytes: int):
        """Read bytes from a device"""
        try:
            while not self.i2c.try_lock():
                time.sleep(0.001)  # 1ms
                pass

            buffer = bytearray(num_bytes)
            self.i2c.readfrom_into(device.addr, buffer)

            return buffer
        except Exception as e:
            print(f"failed to read from device: {e}")
            return None
        finally:
            self.i2c.unlock()

    def add_device_callback(
        self, callback: Callable[[TWIDevice], None]
    ):  # makes me feel confident.
        """Add a callback for new devices"""
        self.new_device_callbacks.append(callback)

    def add_removal_callback(self, callback: Callable[[TWIDevice], None]):
        """Add a callback for removed devices"""
        self.removed_device_callbacks.append(callback)

    def get_next_address_for_channel(self, channel: int):
        """Get next available address for channel"""  # i hate this way of commenting methods.
        if self.freed_addresses[channel]:  # free addresses are used first.
            addr = self.freed_addresses[channel].pop()
            print(f"CH{channel}: reusing 0x{addr:02X}")
            return addr
        while self.next_addr[channel] <= self.max_addr:
            addr = self.next_addr[channel]
            self.next_addr[channel] += 1

            if addr in self.active_addresses[channel] or addr == self.mux_addr:
                continue

            print(f"CH{channel}: new addr 0x{addr:02X}")
            return addr

        raise Exception(f"somehow we ran out of addresses for channel {channel}")

    def free_address(self, channel: int, addr):
        """Free an address in a specific channel for reuse"""
        if addr in self.active_addresses[channel]:
            self.active_addresses[channel].remove(addr)
            self.freed_addresses[channel].append(addr)

            print(f"CH{channel}: freed address 0x{addr:02X}")

    def select_channel(self, channel: int):
        """Select a multiplexer channel"""
        try:
            while not self.i2c.try_lock():  # spinning. woo
                time.sleep(0.001)  # 1ms
                pass

            channel_byte = 1 << channel
            self.i2c.writeto(self.mux_addr, bytes([channel_byte]))
            time.sleep(0.005)
        except Exception as e:
            print(f"failed to select channel: {channel}: {e}")
        finally:
            self.i2c.unlock()

    def unselect_channel(self, channel: int):
        """Select a multiplexer channel"""
        try:
            while not self.i2c.try_lock():  # spinning. woo
                time.sleep(0.001)  # 1ms
                pass

            self.i2c.writeto(self.mux_addr, bytes([0x00]))
            time.sleep(0.005)
        except Exception as e:
            print(f"failed to select channel: {channel}: {e}")
        finally:
            self.i2c.unlock()

    def ping_slave(self, addr):
        """Quick ping to check if a slave responds with an ACK"""
        try:
            while not self.i2c.try_lock():
                time.sleep(0.001)  # 1ms
                pass

            self.i2c.writeto(addr, bytes([]))
            return True
        except Exception:
            return False
        finally:
            self.i2c.unlock()

    def send_address_change_command(self, old_addr, new_addr):
        """Send the address change command to a slave"""
        try:
            while not self.i2c.try_lock():
                time.sleep(0.001)  # 1ms
                pass

            command = bytes([0x00, 0x02, new_addr])
            self.i2c.writeto(old_addr, command)
            time.sleep(0.05)  # 50 ms

            return True
        except Exception as e:
            print(f"address change failed: 0x{old_addr:02X} -> 0x{new_addr:02X}: {e}")
            # TODO: Might want to restart the whole TWI bus or reset the actual mcu.
            return False
        finally:
            self.i2c.unlock()

    def get_friend_code_command(self, addr):
        """Send the address change command to a slave"""
        try:
            while not self.i2c.try_lock():
                time.sleep(0.001)  # 1ms
                pass

            command = bytes([0x00, 0x01])
            self.i2c.writeto(addr, command)
            time.sleep(0.005)  # 5 ms
            buffer = bytearray(11)  # 1 typeid + 10 serial bytes
            self.i2c.readfrom_into(addr, buffer)

            return buffer
        except Exception as e:
            print(f"failed to get friend code: {e}")
            return None
        finally:
            self.i2c.unlock()

    def discover_new_device_on_channel(self, channel: int):
        """Discovers a new fresh slave using the default address on a specific channel"""
        self.select_channel(channel)
        if not self.ping_slave(
            self.default_addr
        ):  # only check the default address. we don't care about the rest lol
            return False
        print(f"CH{channel}: found new device at 0x{self.default_addr:02X}")

        try:
            new_addr = self.get_next_address_for_channel(channel)
        except Exception as e:
            print(f"CH{channel}: {e}")
            return False

        if not self.send_address_change_command(self.default_addr, new_addr):
            self.freed_addresses[channel].append(new_addr)  # put it back into the pool
            return False

        time.sleep(0.02)  # 20 ms. smooth tea time
        if not self.ping_slave(new_addr):
            print(f"CH{channel}: slave failed to ACK at new address 0x{new_addr:02X}")
            self.freed_addresses[channel].append(new_addr)
            return False

        device = TWIDevice(new_addr, channel, self.get_friend_code_command(new_addr))
        self.registered_devices.append(device)
        self.active_addresses[channel].add(new_addr)

        for callback in (
            self.new_device_callbacks
        ):  # i hate this so much but it might actually work.
            try:
                callback(device)
            except Exception as e:
                print(f"HOW. failed to call new callback: {e}")

        print(f"CH{channel}: slave successfully changed address to 0x{new_addr:02X}")
        return True

    def health_check_all_active_devices(self):
        """Health check all active devices across all channels"""
        # current_time = time.monotonic()

        # if current_time - self.last_health_check < self.health_check_interval:
        #     return

        dead_devices = []
        total_checked = (
            0  # track how many devices we checked. useful for debugging i guess.
        )

        for channel in self.channels:
            if not self.active_addresses[channel]:
                continue

            self.select_channel(channel)
            time.sleep(0.001)

            for addr in self.active_addresses[channel]:
                total_checked += 1

                if self.ping_slave(addr):
                    continue
                else:
                    dead_devices.append((channel, addr))

        for channel, addr in dead_devices:
            print(
                f"CH{channel}: slave 0x{addr:02X} stopped responding. Its going to be removed."
            )
            self.free_address(channel, addr)
            for i in range(
                len(self.registered_devices) - 1, -1, -1
            ):  # in reverse because we might remove A LOT of beep boops.
                device = self.registered_devices[i]
                if device.channel == channel and device.addr == addr:
                    self.registered_devices.pop(i)
                    for (
                        callback
                    ) in self.removed_device_callbacks:  # this is sooo wrong holy shit.
                        try:
                            callback(device)  # Batch callback
                        except Exception as e:
                            print(f"how. failed to call removed callback: {e}")

                    break

        # self.last_health_check = current_time

        if total_checked > 0:
            print(
                f"health check: {total_checked} devices ACKed, {len(dead_devices)} removed"
            )

    def discovery_scan_all_channels(self):
        """Scans all channels for new devices (slaves) :)"""
        # current_time = time.monotonic()

        # if current_time - self.last_discovery < self.discovery_interval:
        #     return

        new_devices = 0  # debug debug debug yay. i hope this works.

        for channel in self.channels:
            if self.discover_new_device_on_channel(channel):
                new_devices += 1

        # self.last_discovery = current_time

        if new_devices > 0:
            print(f"discovery: added {new_devices} new devices")

    def initial_discovery(self):
        """Initial discovery."""
        print("starting initial module discovery...")

        total_found = 0
        for channel in self.channels:
            found_on_channel = 0

            # keep discovering until no more devices at default address. might be inefficient but it works
            while self.discover_new_device_on_channel(channel):
                found_on_channel += 1
                total_found += 1

                # small delay between discoveries to let devices initialize
                time.sleep(
                    0.55
                )  # devices wait 0.5 seconds right now. I might want to change that pretty soon. meh

            if found_on_channel > 0:
                print(f"CH{channel}: inital discovery found {found_on_channel} devices")

        print(f"initial discovery completed: {total_found} total devices")

    def schedule_tasks(self):
        """Schedule periodic tasks for health checks and discovery scans"""
        scheduler.create_task(
            self.health_check_all_active_devices,
            period_ms=self.health_check_interval * 1000,
        )
        scheduler.create_task(
            self.discovery_scan_all_channels,
            period_ms=self.maintenance_interval * 1000,
        )

    # compatiblity with direct use as a I2C bus without any multiplexer in the middle (for the oled screen lol)
    # https://github.com/adafruit/Adafruit_CircuitPython_TCA9548A/blob/main/adafruit_tca9548a.py
    def __len__(self) -> Literal[4]:
        return 4

    def __getitem__(
        self, key: Literal[0, 1, 2, 3]
    ) -> "TWIChannel":  # hardcoded as hell
        if not 0 <= key <= 3:
            raise IndexError("Channel must be an integer in the range: 0-3.")
        if self.channels[key] is None:
            self.channels[key] = TWIChannel(self, key)
        return self.channels[key]


class TWIChannel:
    """This class needs to behave like an I2CDevice. shall the TWIManager do manager things."""

    def __init__(self, twiman: TWIManager, channel: int) -> None:
        self.twiman = twiman
        self.channel = channel

    def try_lock(self) -> bool:
        """Pass through for try_lock."""
        self.twiman.select_channel(self.channel)

        return True

    def unlock(self) -> bool:
        """Pass through for unlock."""
        self.twiman.unselect_channel(self.channel)

        return None

    def readfrom_into(self, address: int, buffer: ReadableBuffer, **kwargs):
        """Pass through for readfrom_into."""
        if address == self.twiman.mux_addr:
            raise ValueError("Device address must be different than the MUX address.")
        return self.twiman.i2c.readfrom_into(address, buffer, **kwargs)

    def writeto(self, address: int, buffer: WriteableBuffer, **kwargs):
        """Pass through for writeto."""
        if address == self.twiman.mux_addr:
            raise ValueError("Device address must be different than the MUX address.")
        return self.twiman.i2c.writeto(address, buffer, **kwargs)

    def writeto_then_readfrom(
        self,
        address: int,
        buffer_out: WriteableBuffer,
        buffer_in: ReadableBuffer,
        **kwargs,
    ):
        """Pass through for writeto_then_readfrom."""
        # In linux, at least, this is a special kernel function call
        if address == self.twiman.address:
            raise ValueError("Device address must be different than TCA9548A address.")
        return self.twiman.i2c.writeto_then_readfrom(
            address, buffer_out, buffer_in, **kwargs
        )

    def scan(self) -> List[int]:
        """Perform an I2C Device Scan"""
        return self.twiman.i2c.scan()

    def probe(self, address: int) -> bool:
        """Check if an I2C device is at the specified address on the hub."""
        # backwards compatibility for circuitpython <9.2
        if hasattr(self.twiman.i2c, "probe"):
            return self.twiman.i2c.probe(address)
        return address in self.scan()
