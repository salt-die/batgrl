import asyncio
from itertools import cycle

from ....colors import rainbow_gradient
from .effect import Effect


class RainbowCycleEffect(Effect):
    """
    An effect that adds colors from a rainbow gradient.

    Parameters
    ----------
    ncolors : int, default: 20
        Number of colors in the rainbow gradient.
    cycle_speed : float, default: 1/12
        Seconds between updates.
    enable_foreground_rainbow : bool, default: False
        Add colors to foreground.
    enable_background_rainbow : bool, default: True
        Add colors to background.
    """
    def __init__(
        self,
        ncolors=20,
        cycle_speed=1/12,
        enable_foreground_rainbow=False,
        enable_background_rainbow=True,
        **kwargs
    ):
        super().__init__(**kwargs)

        self._rainbow = cycle(rainbow_gradient(ncolors))
        self._current_color = next(self._rainbow)

        self.cycle_speed = cycle_speed

        self.enable_foreground_rainbow = enable_foreground_rainbow
        self.enable_background_rainbow = enable_background_rainbow

        self.cycle_task = asyncio.create_task(self.cycle_colors())

    def apply_effect(self, canvas_view, colors_view, source_slice: tuple[slice, slice]):
        if self.enable_foreground_rainbow:
            colors_view[..., :3] = colors_view[..., :3] + self._current_color

        if self.enable_background_rainbow:
            colors_view[..., 3:] = colors_view[..., 3:] + self._current_color

    async def cycle_colors(self):
        rainbow = self._rainbow
        cycle_speed = self.cycle_speed

        while True:
            self._current_color = next(rainbow)
            await asyncio.sleep(cycle_speed)
