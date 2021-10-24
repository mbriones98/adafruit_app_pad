"""
KeyApp is a basic framework for apps with functionality bound to each key.
"""

import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label

from apps.base import BaseApp
from constants import DISPLAY_HEIGHT, DISPLAY_WIDTH


def init_display_group_macro_app(display_width, display_height):
    """Set up displayio group with all the labels."""
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
                    (display_width - 1) * x / 2,
                    display_height - 1 - (4 - y) * 12,
                ),
                anchor_point=(x / 2, 1.0),
            )
        )
    group.append(Rect(0, display_height - 11, display_width, 12, fill=0xFFFFFF))
    group.append(
        label.Label(
            terminalio.FONT,
            text="",
            color=0x000000,
            anchored_position=(display_width // 2, display_height),
            anchor_point=(0.5, 1.0),
        )
    )

    return group


class KeyApp(BaseApp):
    name = "Key App"

    display_group = init_display_group_macro_app(DISPLAY_WIDTH, DISPLAY_HEIGHT)

    # First row
    key_0 = None
    key_1 = None
    key_2 = None

    # Second row
    key_3 = None
    key_4 = None
    key_5 = None

    # Third row
    key_6 = None
    key_7 = None
    key_8 = None

    # Fourth row
    key_9 = None
    key_10 = None
    key_11 = None

    def __init__(self, app_pad):
        self.keys = []
        for index in range(12):
            key = getattr(self, "key_%s" % index)

            try:
                bound_key = key.bind(self, index)
            except AttributeError:
                bound_key = None

            self.keys.append(bound_key)

        super().__init__(app_pad)

    def __getitem__(self, index):
        try:
            return self.keys[index]
        except IndexError as err:
            if 0 <= index <= 11:
                return None
            raise err

    def __iter__(self):
        return iter(self.keys)

    def __len__(self):
        return len(self.keys)

    def display_on_focus(self):
        self.display_group[13].text = self.name

        for i, key in enumerate(self.keys):
            try:
                key.label = key.text()
            except AttributeError:
                self.display_group[i].text = ""

    def pixels_on_focus(self):
        for i, key in enumerate(self.keys):
            try:
                key.pixel = key.color()
            except AttributeError:
                self.macropad.pixels[i] = 0

    def key_event(self, event):
        key = self[event.number]

        if key is None:
            return

        if event.pressed:
            key.press()
        else:
            key.release()


class Key:
    class BoundKey:
        def __init__(self, key, app, key_number):
            self.key = key
            self.app = app
            self.key_number = key_number

        @property
        def pixel(self):
            return self.app.macropad.pixels[self.key_number]

        @pixel.setter
        def pixel(self, color):
            self.app.macropad.pixels[self.key_number] = color

        @property
        def label(self):
            self.app.display_group[self.key_number].text

        @label.setter
        def label(self, text):
            self.app.display_group[self.key_number].text = text

        def text(self):
            return self.key.text(self.app)

        def color(self):
            return self.key.color(self.app)

        def press(self):
            self.key.press(self.app)

        def release(self):
            self.key.release(self.app)

        def __str__(self) -> str:
            return f"{self.__class__.__name__}({self.key_number} - {self.key})"

    def __init__(self, text="", color=0, command=None):
        self.command = command
        self._color = color
        self._text = text

    def text(self, app):
        return self._text

    def color(self, app):
        return self._color

    def press(self, app):
        if self.command:
            self.command.execute(app)

    def release(self, app):
        if self.command:
            self.command.undo(app)

    def bind(self, app, key_number):
        return self.BoundKey(self, app, key_number)