"""Moire patterns in foreground colors. Click to change patterns."""

import asyncio
from math import cos, sin
from time import monotonic
from typing import Literal

import numpy as np
from batgrl.app import App
from batgrl.colors import BLACK, WHITE, gradient
from batgrl.gadgets.text import Text

PALETTE = np.array(gradient(BLACK, WHITE, n=100))


def map_into(v, ina, inb, outa, outb):
    return outa + (outb - outa) * ((v - ina) / (inb - ina))


class Moire(Text):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mode: Literal[0, 1, 2] = 0

    def on_size(self):
        super().on_size()
        for y in range(self.height):
            for x in range(self.width):
                self.chars[y, x] = "batgrl "[(y + x) % 7]

    def on_mouse(self, mouse_event) -> bool | None:
        if mouse_event.event_type == "mouse_down":
            self.mode = (self.mode + 1) % 3

    def update(self):
        t = monotonic() * 0.2
        m = min(self.height, self.width)
        aspect = self.height / self.width
        ys, xs = np.indices(self.size)
        sty = 2 * (ys - self.height / 2) / m
        stx = 2 * (xs - self.width / 2) / m * aspect
        center_ay = 0.5 * sin(7 * t)
        center_ax = 0.5 * cos(3 * t)
        center_by = 0.5 * sin(4 * t)
        center_bx = 0.5 * cos(3 * t)

        A = (
            np.arctan2(center_ay - sty, center_ax - stx)
            if self.mode % 2 == 0
            else ((center_ay - sty) ** 2 + (center_ax - stx) ** 2) ** 0.5
        )

        B = (
            np.arctan2(center_by - sty, center_bx - stx)
            if self.mode == 0
            else ((center_by - sty) ** 2 + (center_bx - stx) ** 2) ** 0.5
        )

        A_mod = map_into(cos(2.12 * t), -1, 1, 6, 60)
        B_mod = map_into(cos(3.33 * t), -1, 1, 6, 60)

        a = np.cos(A * A_mod)
        b = np.cos(B * B_mod)
        i = (a * b + 1) / 2
        idx = (i * len(PALETTE)).astype(int)
        self.canvas["fg_color"] = PALETTE[idx]


class MoireApp(App):
    async def on_start(self):
        moire = Moire(size_hint={"height_hint": 1.0, "width_hint": 1.0})
        self.add_gadget(moire)

        while True:
            moire.update()
            await asyncio.sleep(0)


if __name__ == "__main__":
    MoireApp(title="Moire Example").run()
