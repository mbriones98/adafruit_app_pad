"""
A macro/hotkey program for Adafruit MACROPAD. Macro setups are stored in the
/macros folder (configurable below), load up just the ones you're likely to
use. Plug into computer's USB port, use dial to select an application macro
set, press MACROPAD keys to send key sequences and other USB protocols.
"""

# pylint: disable=import-error, unused-import, too-few-public-methods

import os
import time
import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label
from adafruit_macropad import MacroPad

import app

print(app.CONSTANT)


# CONFIGURABLES ------------------------

MACRO_FOLDER = "/macros"


# CLASSES AND FUNCTIONS ----------------


class App:
    """Class representing a host-side application, for which we have a set
    of macro sequences. Project code was originally more complex and
    this was helpful, but maybe it's excessive now?"""

    def __init__(self, appdata):
        self.name = appdata["name"]
        self.macros = appdata["macros"]


class HotkeyPad:
    def __init__(self, apps):
        self.apps = apps
        self.macropad = self._init_macropad()
        self.display_group = self._init_display_group()
        self.macropad.display.show(self.display_group)

        self.last_encoder_position = self.encoder_position
        self.last_encoder_switch = self.encoder_switch

        self.app_index = 0
        try:
            self.current_app = self.apps[self.app_index]
        except IndexError:
            self.current_app = None

    @classmethod
    def _init_macropad(cls):
        macropad = MacroPad()
        macropad.display.auto_refresh = False
        macropad.pixels.auto_write = False

        return macropad

    def _init_display_group(self):
        # Set up displayio group with all the labels
        group = displayio.Group()
        for key_index in range(12):
            x = key_index % 3
            y = key_index // 3
            group.append(
                label.Label(
                    terminalio.FONT,
                    text="",
                    color=0xFFFFFF,
                    anchored_position=(
                        (self.macropad.display.width - 1) * x / 2,
                        self.macropad.display.height - 1 - (3 - y) * 12,
                    ),
                    anchor_point=(x / 2, 1.0),
                )
            )
        group.append(Rect(0, 0, self.macropad.display.width, 12, fill=0xFFFFFF))
        group.append(
            label.Label(
                terminalio.FONT,
                text="",
                color=0x000000,
                anchored_position=(self.macropad.display.width // 2, -2),
                anchor_point=(0.5, 0.0),
            )
        )

        return group

    @property
    def encoder_position(self):
        return self.macropad.encoder

    @property
    def encoder_switch(self):
        self.macropad.encoder_switch_debounced.update()
        return self.macropad.encoder_switch_debounced.pressed

    @property
    def current_app(self):
        return self._current_app

    @current_app.setter
    def current_app(self, new_app):
        self._current_app = new_app
        if new_app is None:
            self.display_group[13].text = "NO MACRO FILES FOUND"
        else:
            self.display_group[13].text = self._current_app.name
            for i in range(12):
                if i < len(
                    self._current_app.macros
                ):  # Key in use, set label + LED color
                    self.macropad.pixels[i] = self._current_app.macros[i][0]
                    self.display_group[i].text = self._current_app.macros[i][1]
                else:  # Key not in use, no label or LED
                    self.macropad.pixels[i] = 0
                    self.display_group[i].text = ""

        self.macropad.keyboard.release_all()
        self.macropad.consumer_control.release()
        self.macropad.mouse.release_all()
        self.macropad.stop_tone()
        self.macropad.pixels.show()
        self.macropad.display.refresh()

    def run(self):
        if not self.apps:
            while True:
                continue
        else:
            self.main_loop()

    def main_loop(self):
        while True:
            # Read encoder position. If it's changed, switch apps.
            position = self.encoder_position
            if position != self.last_encoder_position:
                self.last_encoder_position = position
                self.app_index = position % len(self.apps)
                self.current_app = self.apps[self.app_index]

            # Handle encoder button. If state has changed, and if there's a
            # corresponding macro, set up variables to act on this just like
            # the keypad keys, as if it were a 13th key/macro.
            encoder_switch = self.encoder_switch
            if encoder_switch != self.last_encoder_switch:
                self.last_encoder_switch = encoder_switch
                if len(self.current_app.macros) < 13:
                    continue  # No 13th macro, just resume main loop
                key_number = 12  # else process below as 13th macro
                pressed = encoder_switch
            else:
                event = self.macropad.keys.events.get()
                if not event or event.key_number >= len(self.current_app.macros):
                    continue  # No key events, or no corresponding macro, resume loop
                key_number = event.key_number
                pressed = event.pressed

            # If code reaches here, a key or the encoder button WAS pressed/released
            # and there IS a corresponding macro available for it...other situations
            # are avoided by 'continue' statements above which resume the loop.

            sequence = self.current_app.macros[key_number][2]
            if pressed:
                # 'sequence' is an arbitrary-length list, each item is one of:
                # Positive integer (e.g. Keycode.KEYPAD_MINUS): key pressed
                # Negative integer: (absolute value) key released
                # Float (e.g. 0.25): delay in seconds
                # String (e.g. "Foo"): corresponding keys pressed & released
                # List []: one or more Consumer Control codes (can also do float delay)
                # Dict {}: mouse buttons/motion (might extend in future)
                if key_number < 12:  # No pixel for encoder button
                    self.macropad.pixels[key_number] = 0xFFFFFF
                    self.macropad.pixels.show()
                for item in sequence:
                    if isinstance(item, int):
                        if item >= 0:
                            self.macropad.keyboard.press(item)
                        else:
                            self.macropad.keyboard.release(-item)
                    elif isinstance(item, float):
                        time.sleep(item)
                    elif isinstance(item, str):
                        self.macropad.keyboard_layout.write(item)
                    elif isinstance(item, list):
                        for code in item:
                            if isinstance(code, int):
                                self.macropad.consumer_control.release()
                                self.macropad.consumer_control.press(code)
                            if isinstance(code, float):
                                time.sleep(code)
                    elif isinstance(item, dict):
                        if "buttons" in item:
                            if item["buttons"] >= 0:
                                self.macropad.mouse.press(item["buttons"])
                            else:
                                self.macropad.mouse.release(-item["buttons"])
                        self.macropad.mouse.move(
                            item["x"] if "x" in item else 0,
                            item["y"] if "y" in item else 0,
                            item["wheel"] if "wheel" in item else 0,
                        )
                        if "tone" in item:
                            if item["tone"] > 0:
                                self.macropad.stop_tone()
                                self.macropad.start_tone(item["tone"])
                            else:
                                self.macropad.stop_tone()
                        elif "play" in item:
                            self.macropad.play_file(item["play"])
            else:
                # Release any still-pressed keys, consumer codes, mouse buttons
                # Keys and mouse buttons are individually released this way (rather
                # than release_all()) because pad supports multi-key rollover, e.g.
                # could have a meta key or right-mouse held down by one macro and
                # press/release keys/buttons with others. Navigate popups, etc.
                for item in sequence:
                    if isinstance(item, int):
                        if item >= 0:
                            self.macropad.keyboard.release(item)
                    elif isinstance(item, dict):
                        if "buttons" in item:
                            if item["buttons"] >= 0:
                                self.macropad.mouse.release(item["buttons"])
                        elif "tone" in item:
                            self.macropad.stop_tone()
                self.macropad.consumer_control.release()
                if key_number < 12:  # No pixel for encoder button
                    self.macropad.pixels[key_number] = self.current_app.macros[
                        key_number
                    ][0]
                    self.macropad.pixels.show()


def load_apps(directory):
    # Load all the macro key setups from .py files in MACRO_FOLDER
    apps = []
    files = os.listdir(directory)
    files.sort()
    for filename in files:
        if filename.endswith(".py"):
            try:
                module = __import__(MACRO_FOLDER + "/" + filename[:-3])
                apps.append(App(module.app))
                print("Loaded %s" % module.app["name"])
            except (
                SyntaxError,
                ImportError,
                AttributeError,
                KeyError,
                NameError,
                IndexError,
                TypeError,
            ) as err:
                pass

    return apps


apps = load_apps(MACRO_FOLDER)
macropad = HotkeyPad(apps)
macropad.run()
