"""
Conway's Game of Life, but new cells are given the average color of their parents

Press `r` to reset. Click to create new live cells with random colors.
"""
import asyncio

import numpy as np
from cv2 import filter2D, BORDER_CONSTANT

from nurses_2.app import run_widget_as_app
from nurses_2.colors import ABLACK
from nurses_2.io import MouseButton
from nurses_2.widgets.graphic_widget import GraphicWidget

KERNEL = np.array([
    [1, 1, 1],
    [1, 0, 1],
    [1, 1, 1],
])
UPDATE_SPEED = .1


class Life(GraphicWidget):
    def on_add(self):
        super().on_add()
        self._update_task = asyncio.create_task(self._update())

    def on_remove(self):
        super().on_remove()
        self._update_task.cancel()

    def on_size(self):
        super().on_size()
        self._reset()

    def _reset(self):
        h, w = self._size

        self.universe = np.random.randint(0, 2, (h * 2, w), dtype=bool)

        self.texture[..., :3] = np.random.randint(0, 256, (h * 2, w, 3))
        self.texture[..., 3] = 255
        self.texture[~self.universe, :3] = 0

    async def _update(self):
        while True:
            neighbors = filter2D(self.universe.astype(np.uint8), -1, KERNEL, borderType=BORDER_CONSTANT)
            still_alive = self.universe & (neighbors > 1) & (neighbors < 4)
            new_borns = ~self.universe & (neighbors == 3)
            self.universe = new_borns | still_alive

            rgb = self.texture[..., :3]
            new_colors = filter2D(rgb, -1, KERNEL / 3)
            rgb[~still_alive] = 0
            rgb[new_borns] = new_colors[new_borns]

            await asyncio.sleep(UPDATE_SPEED)

    def on_key_press(self, key_press_event):
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
            self.texture[h - 1: h + 3, w - 1: w + 2, :3] = np.random.randint(0, 256, 3)


run_widget_as_app(Life(size_hint=(1.0, 1.0)))
