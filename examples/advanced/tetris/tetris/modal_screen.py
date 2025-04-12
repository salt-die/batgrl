import asyncio

import numpy as np
from batgrl.colors import Color, gradient
from batgrl.gadgets.text import Text

LIGHT_PURPLE = Color.from_hex("8d46dd")
DARK_PURPLE = Color.from_hex("190c54")
GRADIENT = gradient(DARK_PURPLE, LIGHT_PURPLE, n=9)
LINE_GLOW_DURATION = 0.09

ONE = """
  ▄▄▄▄
 █    █
  █   █
  █   █
  █   █
  █   █
  █▄▄▄█
""".splitlines()[1:]

TWO = """
 ▄▄▄▄▄▄▄
█       █
█▄▄▄▄   █
 ▄▄▄▄█  █
█ ▄▄▄▄▄▄█
█ █▄▄▄▄▄
█▄▄▄▄▄▄▄█
""".splitlines()[1:]

THREE = """
 ▄▄▄▄▄▄▄
█       █
█▄▄▄    █
 ▄▄▄█   █
█▄▄▄    █
 ▄▄▄█   █
█▄▄▄▄▄▄▄█
""".splitlines()[1:]

GAME_OVER = """
 ▄▄▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄   ▄▄ ▄▄▄▄▄▄▄    ▄▄▄▄▄▄▄ ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄
█       █      █  █▄█  █       █  █       █  █ █  █       █   ▄  █
█   ▄▄▄▄█  ▄   █       █    ▄▄▄█  █   ▄   █  █▄█  █    ▄▄▄█  █ █ █
█  █  ▄▄█ █▄█  █       █   █▄▄▄   █  █ █  █       █   █▄▄▄█   █▄▄█▄
█  █ █  █      █       █    ▄▄▄█  █  █▄█  █       █    ▄▄▄█    ▄▄  █
█  █▄▄█ █  ▄   █ ██▄██ █   █▄▄▄   █       ██     ██   █▄▄▄█   █  █ █
█▄▄▄▄▄▄▄█▄█ █▄▄█▄█   █▄█▄▄▄▄▄▄▄█  █▄▄▄▄▄▄▄█ █▄▄▄█ █▄▄▄▄▄▄▄█▄▄▄█  █▄█
""".splitlines()[1:]

PAUSED = """
           ▄▄▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄
          █       █      █  █ █  █       █       █      █
          █    ▄  █  ▄   █  █ █  █  ▄▄▄▄▄█    ▄▄▄█  ▄    █
          █   █▄█ █ █▄█  █  █▄█  █ █▄▄▄▄▄█   █▄▄▄█ █ █   █
          █    ▄▄▄█      █       █▄▄▄▄▄  █    ▄▄▄█ █▄█   █
          █   █   █  ▄   █       █▄▄▄▄▄█ █   █▄▄▄█       █
          █▄▄▄█   █▄█ █▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄█
""".splitlines()[1:]


class ModalScreen(Text):
    def __init__(
        self,
        pos_hint={"y_hint": 0.5, "x_hint": 0.5},
        is_enabled=False,
        **kwargs,
    ):
        super().__init__(
            size=(10, 70),
            pos_hint=pos_hint,
            is_enabled=is_enabled,
            **kwargs,
        )
        self.canvas["fg_color"][:9].swapaxes(0, 1)[:] = GRADIENT

    def on_add(self):
        super().on_add()
        self._countdown_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self._line_glow_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

    def on_remove(self):
        super().on_remove()
        self._countdown_task.cancel()
        self._line_glow_task.cancel()

    def on_key(self, key_event):
        if self._countdown_task.done():
            self._countdown_task = asyncio.create_task(self.countdown())

        return True

    def enable(self, callback, is_game_over):
        self.callback = callback

        for i, line in enumerate(GAME_OVER if is_game_over else PAUSED, start=1):
            self.add_str(line, pos=(i, 0))

        self._line_glow_task = asyncio.create_task(self._line_glow())
        self.is_enabled = True

    async def countdown(self):
        for number in (THREE, TWO, ONE):
            self.chars[:] = " "

            for i, line in enumerate(number, start=1):
                self.add_str(line, pos=(i, 31))

            await asyncio.sleep(1)

        self.is_enabled = False
        self._line_glow_task.cancel()

        self.callback()

    async def _line_glow(self):
        colors = self.canvas["fg_color"]

        h = colors.shape[0]
        buffer = colors.copy()
        white = np.array([127, 189, 127])
        alpha = np.array([2, 4, 2])

        while True:
            for i in range(15):
                start, stop, _ = slice(max(0, h - 3 - i), max(0, h - i)).indices(h)
                lines = stop - start

                colors[start:stop].T[:] = (
                    colors[start:stop].T // alpha[:lines] + white[:lines]
                )

                try:
                    await asyncio.sleep(LINE_GLOW_DURATION)
                finally:
                    colors[start:stop] = buffer[start:stop]
