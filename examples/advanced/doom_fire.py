"""
Recreating the fire effect from Doom.
"""
import asyncio

import numpy as np

from nurses_2.clamp import clamp
from nurses_2.app import App
from nurses_2.widgets.button import Button
from nurses_2.widgets.graphic_widget import GraphicWidget
from nurses_2.widgets.text_widget import TextWidget, Anchor
from nurses_2.widgets.widget import Widget

FIRE_PALETTE = np.array([
    [  0,   0,   0,   0],
    [  7,   7,   7, 255],
    [ 31,   7,   7, 255],
    [ 47,  15,   7, 255],
    [ 71,  15,   7, 255],
    [ 87,  23,   7, 255],
    [103,  31,   7, 255],
    [119,  31,   7, 255],
    [143,  39,   7, 255],
    [159,  47,   7, 255],
    [175,  63,   7, 255],
    [191,  71,   7, 255],
    [199,  71,   7, 255],
    [223,  79,   7, 255],
    [223,  87,   7, 255],
    [223,  87,   7, 255],
    [215,  95,   7, 255],
    [215,  95,   7, 255],
    [215, 103,  15, 255],
    [207, 111,  15, 255],
    [207, 119,  15, 255],
    [207, 127,  15, 255],
    [207, 135,  23, 255],
    [199, 135,  23, 255],
    [199, 143,  23, 255],
    [199, 151,  31, 255],
    [191, 159,  31, 255],
    [191, 159,  31, 255],
    [191, 167,  39, 255],
    [191, 167,  39, 255],
    [191, 175,  47, 255],
    [183, 175,  47, 255],
    [183, 183,  47, 255],
    [183, 183,  55, 255],
    [207, 207, 111, 255],
    [223, 223, 159, 255],
    [239, 239, 199, 255],
    [255, 255, 255, 255],
])

MAX_STRENGTH = len(FIRE_PALETTE) - 1


class DoomFire(GraphicWidget):
    def __init__(self, fire_strength=MAX_STRENGTH, **kwargs):
        super().__init__(**kwargs)

        h, w = self.size
        self._fire_values = np.zeros((2 * h, w), dtype=int)
        self.fire_strength = fire_strength

        asyncio.create_task(self._step_forever())

    @property
    def fire_strength(self):
        return self._fire_strength

    @fire_strength.setter
    def fire_strength(self, fire_strength):
        self._fire_strength = clamp(fire_strength, 0, MAX_STRENGTH)

        np.clip(
            self._fire_strength + np.random.randint(-3, 4, self.width),
            0,
            MAX_STRENGTH,
            out=self._fire_values[-1],
        )

    def on_size(self):
        h, w = self._size
        self._fire_values = np.zeros((2 * h, w), dtype=int)
        self.fire_strength = self.fire_strength  # Trigger `fire_strength.setter`
        self.texture = FIRE_PALETTE[self._fire_values]

    def _step_fire(self):
        roll_up = np.roll(self._fire_values, -1, 0)
        roll_up_left = np.clip(np.roll(roll_up, -1, 1) - 1, 0, None)
        roll_up_left_left = np.clip(np.roll(roll_up, -2, 1) - 2, 0, None)

        decay = np.random.randint(0, 4, self._fire_values.shape)

        decay_2_else_no_change = np.where(decay == 2, roll_up_left_left, self._fire_values)
        decay_1_else_above = np.where(decay == 1, roll_up_left, decay_2_else_no_change)
        self._fire_values = np.where(decay == 0, roll_up, decay_1_else_above)

        self.fire_strength = self.fire_strength

        self.texture[:] = FIRE_PALETTE[self._fire_values]

    async def _step_forever(self):
        while True:
            self._step_fire()

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return


class DoomFireApp(App):
    async def on_start(self):
        doomfire = DoomFire(size_hint=(1.0, 1.0))

        button_container = Widget(size=(1, 28), pos_hint=(1.0, .5), anchor=Anchor.BOTTOM_CENTER)

        strength_label = TextWidget(pos=(0, 3), size=(1, 22))
        strength_label.add_text(f"Current Strength:", column=1)

        def update_label():
            strength_label.add_text(f"{doomfire.fire_strength:2d}", column=19)

        update_label()

        def decrease_callback():
            doomfire.fire_strength -= 1
            update_label()

        decrease_button = Button(
            size=(1, 3),
            label="-",
            callback=decrease_callback,
        )

        def increase_callback():
            doomfire.fire_strength += 1
            update_label()

        increase_button = Button(
            size=(1, 3),
            pos=(0, 25),
            label="+",
            callback=increase_callback,
        )

        button_container.add_widgets(increase_button, strength_label, decrease_button)
        self.add_widgets(doomfire, button_container)


DoomFireApp(title="Doom Fire Example").run()
