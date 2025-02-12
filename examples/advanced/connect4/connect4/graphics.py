import asyncio
from itertools import cycle

import cv2
from batgrl.colors import AWHITE, TRANSPARENT, AColor, gradient
from batgrl.gadgets.graphics import Graphics, Size
from batgrl.gadgets.grid_layout import GridLayout

BOARD_COLOR = AColor.from_hex("4bade5")
SELECTED_COLOR = AColor(*(2 * (i // 3) + (255 // 3) for i in BOARD_COLOR))
CHECKER_SIZE = Size(6, 13)


def x_to_column(x):
    """Convert x coordinate of mouse position to Connect4 column."""
    for i in range(1, 8):
        if x < i * CHECKER_SIZE.width:
            return i - 1


class BoardPiece(Graphics):
    """A single square of a Connect4 board."""

    def __init__(self):
        super().__init__(size=CHECKER_SIZE, default_color=BOARD_COLOR)
        h, w = self._size
        center = h, w // 2
        radius = w // 3
        cv2.circle(self.texture, center, radius, TRANSPARENT, -1)

    def select(self):
        texture = self.texture
        texture[(texture != TRANSPARENT).all(axis=2)] = SELECTED_COLOR

    def unselect(self):
        texture = self.texture
        texture[(texture != TRANSPARENT).all(axis=2)] = BOARD_COLOR


class Checker(Graphics):
    def __init__(self, color):
        super().__init__(size=CHECKER_SIZE)
        h, w = self._size
        center = h, w // 2
        radius = w // 3
        cv2.circle(self.texture, center, radius, color, -1)
        self._color = color

    def on_add(self):
        super().on_add()
        self._flash_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

    def flash(self):
        self._flash_task = asyncio.create_task(self._flash())

    def stop_flash(self):
        self._flash_task.cancel()

    async def _flash(self):
        flash_gradient = cycle(
            gradient(self._color, AWHITE, n=20) + gradient(AWHITE, self._color, n=10)
        )
        for self.texture[:] in flash_gradient:
            await asyncio.sleep(0.05)

    async def fall(self, target, on_complete):
        velocity = 0
        gravity = 1 / 36
        y = self.y

        while self.y != target:
            velocity += gravity
            y += velocity
            self.y = min(target, int(y))

            await asyncio.sleep(0)

        on_complete()


class Board(GridLayout):
    def __init__(self):
        super().__init__(grid_rows=6, grid_columns=7, pos=(2, 0), is_transparent=True)
        self.add_gadgets(BoardPiece() for _ in range(42))
        self.size = self.min_grid_size
        self._last_col = -1

    def on_mouse(self, mouse_event):
        if not self.collides_point(mouse_event.pos):
            for i in range(6):
                self.children[self.index_at(i, self._last_col)].unselect()
            self._last_col = -1
            return False

        col = x_to_column(self.to_local(mouse_event.pos).x)
        if col != self._last_col:
            for i in range(6):
                if self._last_col != -1:
                    self.children[self.index_at(i, self._last_col)].unselect()
                self.children[self.index_at(i, col)].select()
            self._last_col = col
