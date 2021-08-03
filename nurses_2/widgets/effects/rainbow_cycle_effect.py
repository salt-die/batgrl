import asyncio
from itertools import cycle

from ...colors import rainbow_gradient
from .effect import Effect


class BackgroundRainbowCycleEffect(Effect):
    def __init__(self, *args, ncolors=20, cycle_speed=1/12, **kwargs):
        super().__init__(*args, **kwargs)

        self._rainbow = cycle(rainbow_gradient(ncolors))
        self._current_color = next(self._rainbow)

        self.cycle_speed = cycle_speed

        self.cycle_task = asyncio.create_task(self.cycle_colors())

    def apply_colors_effect(self, colors_view, rect):
        colors_view[..., 3:] = (colors_view[..., 3:] + self._current_color) % 255

    async def cycle_colors(self):
        rainbow = self._rainbow
        cycle_speed = self.cycle_speed

        while True:
            self._current_color = next(rainbow)
            await asyncio.sleep(cycle_speed)


class ForegroundRainbowCycleEffect(BackgroundRainbowCycleEffect):
    def apply_colors_effect(self, colors, rect):
        colors_view[..., :3] = (colors_view[..., :3] + self._current_color) % 255
