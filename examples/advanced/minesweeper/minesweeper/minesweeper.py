import asyncio

import numpy as np
import cv2

from nurses_2.widgets.widget import Widget
from nurses_2.widgets.text_widget import TextWidget, Anchor, Point
from nurses_2.widgets.behaviors.button_behavior import ButtonBehavior

from .colors import FLAG_COLOR, DATA_BAR
from .count import Count
from .grid import Grid
from .minefield import Minefield
from .unicode_chars import *

SIZE = 16, 30
NMINES = 99

KERNEL = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.uint8)
RNG = np.random.default_rng()

V_SPACING = Grid.V_SPACING
H_SPACING = Grid.H_SPACING


class ResetButton(ButtonBehavior, TextWidget):
    def update_normal(self):
        self.add_text(HAPPY)

    def update_down(self):
        self.add_text(SURPRISED)

    def on_release(self):
        self.parent.reset()


class MineSweeper(Widget):
    def __init__(self, pos=Point(0, 0), **kwargs):
        h, w = SIZE

        super().__init__(
            pos=pos,
            size=(V_SPACING * h + 2, H_SPACING * w + 1),
            background_color_pair=DATA_BAR,
            **kwargs
        )

        self.timer = TextWidget(
            size=(1, 20),
            anchor=Anchor.TOP_RIGHT,
            pos_hint=(None, .95),
            default_color_pair=DATA_BAR,
        )
        self.timer.add_text("Time Elapsed:")
        self._elapsed_time = 0

        self.mines_left = TextWidget(
            size=(1, 10),
            pos_hint=(None, .05),
            default_color_pair=DATA_BAR,
        )
        self.mines_left.add_text("Mines:")

        self.reset_button = ResetButton(
            size=(1, 2),
            default_color_pair=DATA_BAR,
            anchor=Anchor.CENTER,
            pos_hint=(None, .5),
        )

        self.add_widgets(self.mines_left, self.timer, self.reset_button)

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
        self.mines_left.add_text(str(mines).zfill(3), column=-3)

    def reset(self):
        if len(self.children) == 5:
            del self.children[-2:]

        self._timer_task.cancel()
        self._elapsed_time = 0
        self.reset_button.update_normal()
        self.mines = NMINES

        minefield = self.create_minefield()
        count = cv2.filter2D(minefield, -1, KERNEL, borderType=cv2.BORDER_CONSTANT)

        self.add_widgets(Count(count, minefield), Minefield(count, minefield))

        self._timer_task = asyncio.create_task(self._time())

    async def _time(self):
        while True:
            self.timer.add_text(str(self._elapsed_time).zfill(6), column=-6)
            await asyncio.sleep(1)
            self._elapsed_time += 1

    def game_over(self, win: bool):
        self._timer_task.cancel()

        count, minefield = self.children[-2:]

        if not win:
            self.reset_button.add_text(KNOCKED_OUT)
            count.canvas[(count.canvas == BOMB) & (minefield.canvas != FLAG)] = EXPLODED

            bad_flags = (count.canvas != BOMB) & (minefield.canvas == FLAG)
            count.canvas[bad_flags] = BAD_FLAG
            count.colors[bad_flags, :3] = FLAG_COLOR
        else:
            self.reset_button.add_text(COOL)

    def create_minefield(self):
        minefield = np.zeros(SIZE, dtype=np.uint8)
        h, w = SIZE

        for _ in range(NMINES):
            while True:
                location =RNG.integers(h), RNG.integers(w)
                if minefield[location] == 0:
                    minefield[location] = 1
                    break

        return minefield
