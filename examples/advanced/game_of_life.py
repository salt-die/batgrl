"""
Conway's Game of Life, but new cells are given the average color of their parents

Press `r` to reset. Click to create new live cells with random colors.
"""
import asyncio

import numpy as np
from scipy.ndimage import convolve

from nurses_2.app import run_widget_as_app
from nurses_2.colors import ABLACK
from nurses_2.io import MouseButton
from nurses_2.widgets.graphic_widget import GraphicWidget

KERNEL = np.array([
    [1, 1, 1],
    [1, 0, 1],
    [1, 1, 1],
])
UPDATE_SPEED = .012

class Life(GraphicWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_task = asyncio.create_task(self._update())

    def on_size(self):
        super().on_size()
        self._reset()

    def _reset(self):
        h, w = self._size
        self.universe = np.random.randint(0, 2, (h * 2, w))
        self.RGB = [np.random.randint(0, 256, (h * 2, w)) for _ in range(3)]

    async def _update(self):
        while True:
            neighbors = convolve(self.universe, KERNEL, mode="constant")
            still_alive = self.universe & (neighbors > 1) & (neighbors < 4)
            new_borns = ~self.universe & (neighbors == 3)
            self.universe = still_alive + new_borns

            old_colors = [np.where(still_alive, color, 0) for color in self.RGB]
            new_colors = [
                np.where(new_borns, convolve(color, KERNEL, mode="constant") / 3, 0)
                for color in self.RGB
            ]

            self.RGB = [sum(color) for color in zip(old_colors, new_colors)]

            self.texture[..., :3] = np.dstack(self.RGB)

            await asyncio.sleep(UPDATE_SPEED)

    def on_keypress(self, key_press_event):
        match key_press_event.key:
            case "r":
                self._reset()
                return True

    def on_mouse(self, mouse_event):
        if (
            mouse_event.button is not MouseButton.NO_BUTTON
            and self.collides_point(mouse_event.position)
        ):
            h, w = self.to_local(mouse_event.position)
            h *= 2

            self.universe[h - 1: h + 3, w - 1: w + 2] = 1
            for color in self.RGB:
                color[h - 1: h + 3, w - 1: w + 2] = np.random.randint(0, 256)


run_widget_as_app(Life, size_hint=(1.0, 1.0), default_color=ABLACK)
