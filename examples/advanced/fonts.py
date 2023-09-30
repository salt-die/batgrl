import asyncio
from pathlib import Path
from random import random, randrange

import numpy as np

from nurses_2.app import App
from nurses_2.colors import BLACK, RED, ColorPair, gradient, lerp_colors
from nurses_2.fonts import FIGFont
from nurses_2.widgets.behaviors.button_behavior import ButtonBehavior, ButtonState
from nurses_2.widgets.text_widget import TextWidget

ASSETS = Path(__file__).parent.parent / "assets"
BIG_FONT = FIGFont.from_path(ASSETS / "delta_corps_priest_1.flf")
LITTLE_FONT = FIGFont.from_path(ASSETS / "rustofat.tlf")
RED_ON_BLACK = ColorPair.from_colors(RED, BLACK)
TRANSITIONS = np.array([0.07, 0.004, 1e-5])


class Bleed(TextWidget):
    def __init__(
        self, banner, button, blood_color_pair: ColorPair = RED_ON_BLACK, **kwargs
    ):
        super().__init__(**kwargs)
        self.banner = banner
        self.button = button
        self.add_widgets(banner, button)
        self.blood_color_pair = blood_color_pair
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
            self._drops.append(asyncio.create_task(self._drip()))
            await asyncio.sleep(0.03)

    async def _drip(self):
        drop = TextWidget(default_color_pair=self.blood_color_pair, is_transparent=True)
        drop.pos = self._start_locs[randrange(len(self._start_locs))]
        drop.size = self.height - drop.y, 1

        overlap = drop.colors[: self.banner.height - drop.y, :, 3:]
        overlap[self.banner.canvas[drop.y :, drop.x]["char"] != " "] = 255

        weights = weights = np.array([0.0, 0.89, 0.1])
        amounts = np.zeros(drop.height, float)
        amounts[0] = 1

        canvas = drop.canvas["char"][:, 0]

        self.add_widget(drop)
        if round(random()):
            self.children.remove(drop)
            self.children.insert(0, drop)
        self.button.pull_to_front()

        while (char := amounts > TRANSITIONS[:, None])[2].any():
            canvas[:] = " "
            canvas[char[2]] = "░"
            canvas[char[1]] = "▒"
            canvas[char[0]] = "▓"
            amounts = np.convolve(amounts, weights, mode="same")

            await asyncio.sleep(0)

        self.remove_widget(drop)


class TextButton(ButtonBehavior, TextWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dark_red = lerp_colors(RED, BLACK, 0.35)
        self._grad = gradient(self.default_fg_color, RED, 20)
        self._i = 0

    def on_add(self):
        self._color_task = asyncio.create_task(self._to_white())
        super().on_add()

    def on_remove(self):
        self._color_task.cancel()
        super().on_remove()

    async def _to_red(self):
        self.colors[..., :3] = self._grad[self._i]
        while self._i < len(self._grad) - 1:
            self._i += 1
            if self.state is not ButtonState.DOWN:
                self.colors[..., :3] = self._grad[self._i]
            await asyncio.sleep(0.01)

    async def _to_white(self):
        self.colors[..., :3] = self._grad[self._i]
        while self._i > 0:
            self._i -= 1
            self.colors[..., :3] = self._grad[self._i]
            await asyncio.sleep(0.01)

    def update_hover(self):
        self._color_task.cancel()
        self._color_task = asyncio.create_task(self._to_red())
        self.colors[..., :3] = self._grad[self._i]

    def update_normal(self):
        self._color_task.cancel()
        self._color_task = asyncio.create_task(self._to_white())
        self.colors[..., :3] = self._grad[self._i]

    def update_down(self):
        self.colors[..., :3] = self._dark_red


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
        banner = TextWidget(size=(h, w), is_transparent=True)
        banner.canvas["char"] = banner_canvas

        bleed = Bleed(
            banner, button, size=(h + 9, w), pos_hint={"y_hint": 0.5, "x_hint": 0.5}
        )

        self.add_widget(bleed)


if __name__ == "__main__":
    DripApp().run()
