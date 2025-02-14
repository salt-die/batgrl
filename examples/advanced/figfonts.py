import asyncio
from pathlib import Path
from random import random, randrange

import numpy as np
from batgrl.app import App
from batgrl.colors import BLACK, RED, WHITE, gradient, lerp_colors
from batgrl.figfont import FIGFont
from batgrl.gadgets.behaviors.button_behavior import ButtonBehavior
from batgrl.gadgets.text import Text

ASSETS = Path(__file__).parent.parent / "assets"
BIG_FONT = FIGFont.from_path(ASSETS / "delta_corps_priest_1.flf")
LITTLE_FONT = FIGFont.from_path(ASSETS / "rustofat.tlf")
TRANSITIONS = np.array([0.07, 0.004, 1e-5])


class Bleed(Text):
    def __init__(self, banner, button, **kwargs):
        super().__init__(**kwargs)
        self.banner = banner
        self.button = button
        self.add_gadgets(banner, button)
        self._start_locs = np.argwhere(self.banner.canvas["char"] != " ")
        self._drops = []

    def on_add(self):
        super().on_add()
        self._drip_task = asyncio.create_task(self._bleed())

    def on_remove(self):
        self._drip_task.cancel()
        for task in self._drops:
            task.cancel()

        super().on_remove()

    async def _bleed(self):
        while True:
            self._drops = [drip for drip in self._drops if not drip.done()]
            if len(self._drops) < 20:
                self._drops.append(asyncio.create_task(self._drip()))
            await asyncio.sleep(0.03)

    async def _drip(self):
        drop = Text(is_transparent=True)
        drop.pos = self._start_locs[randrange(len(self._start_locs))]
        drop.size = self.height - drop.y, 1
        drop.canvas["fg_color"] = RED

        weights = weights = np.array([0.0, 0.89, 0.1])
        amounts = np.zeros(drop.height, float)
        amounts[0] = 1

        self.add_gadget(drop)
        if round(random()):
            self.children.remove(drop)
            self.children.insert(0, drop)
        self.button.pull_to_front()

        chars = drop.canvas["char"]
        while (char := amounts > TRANSITIONS[:, None])[2].any():
            chars[:] = " "
            chars[char[2]] = "░"
            chars[char[1]] = "▒"
            chars[char[0]] = "▓"
            amounts = np.convolve(amounts, weights, mode="same")

            await asyncio.sleep(0)

        self.remove_gadget(drop)


class TextButton(ButtonBehavior, Text):
    def __init__(self, **kwargs):
        self._color_task = None
        self._grad = gradient(WHITE, RED, n=20)
        self._dark_red = lerp_colors(RED, BLACK, 0.35)
        self._i = 0
        super().__init__(**kwargs)

    def on_add(self):
        self._color_task = asyncio.create_task(self._to_white())
        super().on_add()

    def on_remove(self):
        if self._color_task is not None:
            self._color_task.cancel()
        super().on_remove()

    async def _to_red(self):
        self.canvas["fg_color"] = self._grad[self._i]
        while self._i < len(self._grad) - 1:
            self._i += 1
            if self.button_state != "down":
                self.canvas["fg_color"] = self._grad[self._i]
            await asyncio.sleep(0.01)

    async def _to_white(self):
        self.canvas["fg_color"] = self._grad[self._i]
        while self._i > 0:
            self._i -= 1
            self.canvas["fg_color"] = self._grad[self._i]
            await asyncio.sleep(0.01)

    def update_hover(self):
        if self._color_task is not None:
            self._color_task.cancel()
        self._color_task = asyncio.create_task(self._to_red())
        self.canvas["fg_color"] = self._grad[self._i]

    def update_normal(self):
        if self._color_task is not None:
            self._color_task.cancel()
        self._color_task = asyncio.create_task(self._to_white())
        self.canvas["fg_color"] = self._grad[self._i]

    def update_down(self):
        self.canvas["fg_color"] = self._dark_red


class DripApp(App):
    async def on_start(self):
        button_canvas = LITTLE_FONT.render_array(" PLAY\nAGAIN?")
        banner_canvas = BIG_FONT.render_array("YOU DIED")

        button = TextButton(
            size=button_canvas.shape,
            pos=(10, 0),
            pos_hint={"x_hint": 0.5},
            is_transparent=True,
        )
        button.canvas["char"] = button_canvas

        h, w = banner_canvas.shape
        banner = Text(size=(h, w), is_transparent=True)
        banner.canvas["char"] = banner_canvas

        bleed = Bleed(
            banner, button, size=(h + 9, w), pos_hint={"y_hint": 0.5, "x_hint": 0.5}
        )

        self.add_gadget(bleed)


if __name__ == "__main__":
    DripApp().run()
