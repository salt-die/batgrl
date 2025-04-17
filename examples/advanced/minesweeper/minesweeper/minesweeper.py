import asyncio

import cv2
import numpy as np
from batgrl.gadgets.behaviors.button_behavior import ButtonBehavior
from batgrl.gadgets.gadget import Gadget, Point
from batgrl.gadgets.pane import Pane
from batgrl.gadgets.text import Text, new_cell

from .colors import COUNT_SQUARE, FLAG_COLOR, HIDDEN_SQUARE
from .count import Count
from .grid import Grid
from .minefield import Minefield
from .unicode_chars import (
    BAD_FLAG,
    BOMB,
    COOL,
    EXPLODED,
    FLAG,
    HAPPY,
    KNOCKED_OUT,
    SURPRISED,
)

SIZE = 16, 30
NMINES = 99

KERNEL = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.uint8)
RNG = np.random.default_rng()

V_SPACING = Grid.V_SPACING
H_SPACING = Grid.H_SPACING


class ResetButton(ButtonBehavior, Text):
    def update_normal(self):
        self.add_str(HAPPY)

    def update_down(self):
        self.add_str(SURPRISED)

    def on_release(self):
        self.parent.reset()


class MineSweeper(Gadget):
    def __init__(self, pos=Point(0, 0), **kwargs):
        h, w = SIZE
        default_cell = new_cell(fg_color=HIDDEN_SQUARE, bg_color=COUNT_SQUARE)
        super().__init__(pos=pos, size=(V_SPACING * h + 2, H_SPACING * w + 1), **kwargs)

        self.timer = Text(
            size=(1, 20),
            pos_hint={"x_hint": 0.95, "anchor": "top-right"},
            default_cell=default_cell,
        )
        self.timer.add_str("Time Elapsed:")
        self._elapsed_time = 0

        self.bg = Pane(
            size_hint={"height_hint": 1.0, "width_hint": 1.0}, bg_color=COUNT_SQUARE
        )

        self.mines_left = Text(
            size=(1, 10),
            pos_hint={"x_hint": 0.05},
            default_cell=default_cell,
        )
        self.mines_left.add_str("Mines:")

        self.reset_button = ResetButton(
            size=(1, 2), default_cell=default_cell, pos_hint={"x_hint": 0.5}
        )

        self.add_gadgets(self.bg, self.mines_left, self.timer, self.reset_button)

    def on_add(self):
        super().on_add()
        self._timer_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self.reset()

    def on_remove(self):
        super().on_remove()
        self._timer_task.cancel()

    @property
    def mines(self):
        return self._mines

    @mines.setter
    def mines(self, mines):
        self._mines = mines
        self.mines_left.add_str(str(mines).zfill(3), pos=(0, -3))

    def reset(self):
        if len(self.children) == 5:
            del self.children[-2:]

        self._timer_task.cancel()
        self._elapsed_time = 0
        self.reset_button.update_normal()
        self.mines = NMINES

        minefield = self.create_minefield()
        count = cv2.filter2D(minefield, -1, KERNEL, borderType=cv2.BORDER_CONSTANT)

        self.add_gadgets(Count(count, minefield), Minefield(count, minefield))

        self._timer_task = asyncio.create_task(self._time())

    async def _time(self):
        while True:
            self.timer.add_str(str(self._elapsed_time).zfill(6), pos=(0, -6))
            await asyncio.sleep(1)
            self._elapsed_time += 1

    def game_over(self, win: bool):
        self._timer_task.cancel()

        count, minefield = self.children[-2:]

        if not win:
            self.reset_button.add_str(KNOCKED_OUT)
            count.chars[(count.chars == BOMB) & (minefield.chars != FLAG)] = EXPLODED

            bad_flags = (count.chars != BOMB) & (minefield.chars == FLAG)
            count.chars[bad_flags] = BAD_FLAG
            count.canvas["fg_color"][bad_flags] = FLAG_COLOR
        else:
            self.reset_button.add_str(COOL)

    def create_minefield(self):
        minefield = np.zeros(SIZE, dtype=np.uint8)
        h, w = SIZE

        for _ in range(NMINES):
            while True:
                location = RNG.integers(h), RNG.integers(w)
                if minefield[location] == 0:
                    minefield[location] = 1
                    break

        return minefield
