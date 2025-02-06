"""
Conway's Game of Life, but new cells are given the average color of their parents.

Press `r` to reset. Click to create new live cells with random colors.
"""

import asyncio

import numpy as np
from batgrl.app import run_gadget_as_app
from batgrl.gadgets.graphics import Graphics, scale_geometry
from cv2 import BORDER_CONSTANT, filter2D

KERNEL = np.array(
    [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ]
)
UPDATE_SPEED = 1 / 60


class Life(Graphics):
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
        h, w = scale_geometry(self._blitter, self._size)
        self.universe = np.random.randint(0, 2, (h, w), dtype=bool)
        self.texture[..., :3] = np.random.randint(0, 256, (h, w, 3))
        self.texture[~self.universe] = 0

    async def _update(self):
        while True:
            neighbors = filter2D(
                self.universe.astype(np.uint8), -1, KERNEL, borderType=BORDER_CONSTANT
            )
            still_alive = self.universe & np.isin(neighbors, (2, 3))
            new_borns = ~self.universe & (neighbors == 3)
            self.universe = new_borns | still_alive

            rgb = self.texture[..., :3]
            new_colors = filter2D(rgb, -1, KERNEL / 3)
            rgb[~still_alive] = 0
            rgb[new_borns] = new_colors[new_borns]
            self.texture[..., 3] = 0
            self.texture[..., 3][self.universe] = 255

            await asyncio.sleep(UPDATE_SPEED)

    def on_key(self, key_event):
        if key_event.key == "r":
            self._reset()
            return True

    def on_mouse(self, mouse_event):
        if mouse_event.button != "no_button" and self.collides_point(mouse_event.pos):
            h, w = scale_geometry(self._blitter, mouse_event.pos)
            self.universe[h - 1 : h + 3, w - 1 : w + 2] = 1
            self.texture[h - 1 : h + 3, w - 1 : w + 2, :3] = np.random.randint(
                0, 256, 3
            )


if __name__ == "__main__":
    run_gadget_as_app(
        Life(size_hint={"height_hint": 1.0, "width_hint": 1.0}, blitter="braille"),
        title="Game of Life",
    )
