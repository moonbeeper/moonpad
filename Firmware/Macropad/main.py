import board
import digitalio

from kmk.extensions.display import Display, TextEntry, ssd1306
from kmk.extensions.media_keys import MediaKeys
from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation
from knob_module import KnobModule
from slider_module import SliderModule
from twiman import TWIManager

mux_reset = digitalio.DigitalInOut(board.D10)  # unused
mux_reset.direction = digitalio.Direction.OUTPUT
mux_reset.value = True  # required or else the mux will be stuck in reset.

keyboard = KMKKeyboard()  # keyboard updates first
twiman = TWIManager(
    mux_channels=4 - 1
)  # There's 4 channels. One is used for the display, so we have 3 left for devices.

twiman.initial_discovery()
twiman.schedule_tasks()

driver = ssd1306.SSD1306(
    i2c=twiman[3],  # peace of bananas. I hate now using a mux for the display
)

display = Display(
    # Mandatory:
    display=driver,
    # Optional:
    width=128,  # screen size
    height=32,  # screen size
    flip=True,  # flips your display content
    flip_left=False,  # flips your display content on left side split
    flip_right=False,  # flips your display content on right side split
    brightness=0.8,  # initial screen brightness level
    brightness_step=0.1,  # used for brightness increase/decrease keycodes
    dim_time=20,  # time in seconds to reduce screen brightness
    dim_target=0.1,  # set level for brightness decrease
    off_time=60,  # time in seconds to turn off screen
    powersave_dim_time=10,  # time in seconds to reduce screen brightness
    powersave_dim_target=0.1,  # set level for brightness decrease
    powersave_off_time=30,  # time in seconds to turn off screen
)

display.entries = [
    TextEntry(text="tahnks yours kmk", x=0, y=0),
    TextEntry(text="beep beep pad", x=0, y=12),
    TextEntry(text="Hey there!", x=0, y=24),
]
keyboard.extensions.append(display)

keyboard.col_pins = (
    board.D6,
    board.D8,
    board.D7,
)
keyboard.row_pins = (
    board.D1,
    board.D3,
    board.D9,
)
keyboard.diode_orientation = DiodeOrientation.COL2ROW
media_keys = MediaKeys()
keyboard.extensions.append(media_keys)
keyboard.extensions.append(SliderModule(twiman))

knob_module = KnobModule(twiman)
keyboard.extensions.append(knob_module)

keyboard.keymap = [
    [
        KC.F13,
        KC.F14,
        KC.F15,
        KC.F16,
        KC.F17,
        KC.F18,
        KC.F19,
        KC.F20,
    ]
]

knob_module.map = [
    [KC.BRIGHTNESS_UP, KC.BRIGHTNESS_DOWN, KC.BRIGHTNESS_DOWN],
    [KC.AUDIO_VOL_UP, KC.AUDIO_VOL_DOWN, KC.AUDIO_MUTE],
    [KC.LCTRL(KC.EQUAL), KC.LCTRL(KC.MINUS), KC.NO],
]

if __name__ == "__main__":
    keyboard.go()
