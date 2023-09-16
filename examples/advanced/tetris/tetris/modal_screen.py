import asyncio

import numpy as np

from nurses_2.colors import BLACK, Color, ColorPair, gradient
from nurses_2.widgets.text_widget import TextWidget

LIGHT_PURPLE = Color.from_hex("8d46dd")
DARK_PURPLE = Color.from_hex("190c54")
GRADIENT = gradient(
    ColorPair.from_colors(DARK_PURPLE, BLACK),
    ColorPair.from_colors(LIGHT_PURPLE, BLACK),
    9,
)
LINE_GLOW_DURATION = 0.09

ONE = """
  ▄▄▄▄
 █    █
  █   █
  █   █
  █   █
  █   █
  █▄▄▄█
""".splitlines()[
    1:
]

TWO = """
 ▄▄▄▄▄▄▄
█       █
█▄▄▄▄   █
 ▄▄▄▄█  █
█ ▄▄▄▄▄▄█
█ █▄▄▄▄▄
█▄▄▄▄▄▄▄█
""".splitlines()[
    1:
]

THREE = """
 ▄▄▄▄▄▄▄
█       █
█▄▄▄    █
 ▄▄▄█   █
█▄▄▄    █
 ▄▄▄█   █
█▄▄▄▄▄▄▄█
""".splitlines()[
    1:
]

GAME_OVER = """
 ▄▄▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄   ▄▄ ▄▄▄▄▄▄▄    ▄▄▄▄▄▄▄ ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄
█       █      █  █▄█  █       █  █       █  █ █  █       █   ▄  █
█   ▄▄▄▄█  ▄   █       █    ▄▄▄█  █   ▄   █  █▄█  █    ▄▄▄█  █ █ █
█  █  ▄▄█ █▄█  █       █   █▄▄▄   █  █ █  █       █   █▄▄▄█   █▄▄█▄
█  █ █  █      █       █    ▄▄▄█  █  █▄█  █       █    ▄▄▄█    ▄▄  █
█  █▄▄█ █  ▄   █ ██▄██ █   █▄▄▄   █       ██     ██   █▄▄▄█   █  █ █
█▄▄▄▄▄▄▄█▄█ █▄▄█▄█   █▄█▄▄▄▄▄▄▄█  █▄▄▄▄▄▄▄█ █▄▄▄█ █▄▄▄▄▄▄▄█▄▄▄█  █▄█
""".splitlines()[
    1:
]

PAUSED = """
           ▄▄▄▄▄▄▄ ▄▄▄▄▄▄ ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄
          █       █      █  █ █  █       █       █      █
          █    ▄  █  ▄   █  █ █  █  ▄▄▄▄▄█    ▄▄▄█  ▄    █
          █   █▄█ █ █▄█  █  █▄█  █ █▄▄▄▄▄█   █▄▄▄█ █ █   █
          █    ▄▄▄█      █       █▄▄▄▄▄  █    ▄▄▄█ █▄█   █
          █   █   █  ▄   █       █▄▄▄▄▄█ █   █▄▄▄█       █
          █▄▄▄█   █▄█ █▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄█
""".splitlines()[
    1:
]


class ModalScreen(TextWidget):
    def __init__(
        self,
        pos_hint=(0.5, 0.5),
        is_enabled=False,
        **kwargs,
    ):
        super().__init__(
            size=(10, 70),
            pos_hint=pos_hint,
            is_enabled=is_enabled,
            **kwargs,
        )
        for i, color in enumerate(GRADIENT):
            self.colors[i, :] = color

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
            self.add_str(line, (i, 0))

        self._line_glow_task = asyncio.create_task(self._line_glow())
        self.is_enabled = True

    async def countdown(self):
        for number in (THREE, TWO, ONE):
            self.canvas["char"][:] = " "

            for i, line in enumerate(number, start=1):
                self.add_str(line, (i, 31))

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

                colors[start:stop, :, :3].T[:] = (
                    colors[start:stop, :, :3].T // alpha[:lines] + white[:lines]
                )

                try:
                    await asyncio.sleep(LINE_GLOW_DURATION)
                except asyncio.CancelledError:
                    return
                finally:
                    colors[start:stop] = buffer[start:stop]
