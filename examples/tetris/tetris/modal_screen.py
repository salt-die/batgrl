import asyncio

import numpy as np

from nurses_2.colors import BLACK, Color, gradient
from nurses_2.widgets import Widget
from nurses_2.widgets.behaviors import AutoPositionBehavior, Anchor

LIGHT_PURPLE = Color.from_hex("8d46dd")
DARK_PURPLE = Color.from_hex("190c54")
GRADIENT = gradient(9, (*DARK_PURPLE, *BLACK), (*LIGHT_PURPLE, *BLACK))
LINE_GLOW_DURATION = .09

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


class ModalScreen(AutoPositionBehavior, Widget):
    def __init__(
        self,
        anchor=Anchor.CENTER,
        pos_hint=(.5, .5),
        is_enabled=False,
        **kwargs,
    ):
        super().__init__(
            size=(10, 70),
            anchor=anchor,
            pos_hint=pos_hint,
            is_enabled=is_enabled,
            **kwargs,
        )
        for i, color in enumerate(GRADIENT):
            self.colors[i, :] = color

        self._countdown_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

    def on_press(self, key_press):
        if self._countdown_task.done():
            self._countdown_task = asyncio.create_task(self.countdown())

        return True

    def enable(self, callback, is_game_over):
        self.callback = callback

        if self.parent is not self.root:
            root = self.root
            self.parent.remove_widget(self)
            root.add_widget(self)

        for i, line in enumerate(GAME_OVER if is_game_over else PAUSED, start=1):
            self.add_text(line, row=i)

        self._line_glow_task = asyncio.create_task(self._line_glow())
        self.is_enabled = True

    async def countdown(self):
        self.canvas[:] = " "

        for number in (THREE, TWO, ONE):
            self.canvas[:] = " "

            for i, line in enumerate(number, start=1):
                self.add_text(line, row=i, column=31)

            await asyncio.sleep(1)

        self.is_enabled = False
        self._line_glow_task.cancel()

        self.callback()

    async def _line_glow(self):
        colors = self.colors

        h = colors.shape[0]
        buffer = colors.copy()
        white = np.array([127, 189, 127])
        alpha = np.array([2, 4, 2])

        while True:
            for i in range(15):
                start, stop, _ = slice(max(0, h - 3 - i), max(0, h - i)).indices(h)
                lines = stop - start

                colors[start: stop, :, :3].T[:] = colors[start: stop, :, :3].T // alpha[:lines] + white[:lines]

                try:
                    await asyncio.sleep(LINE_GLOW_DURATION)
                except asyncio.CancelledError:
                    return
                finally:
                    colors[start: stop] = buffer[start: stop]
