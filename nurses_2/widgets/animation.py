import asyncio
from collections.abc import Sequence
from pathlib import Path

from .graphic_widget_data_structures import Interpolation
from .image import Image
from .widget import Widget

__all__ = "Animation", "Interpolaton"


class Animation(Widget):
    """
    An animation widget.

    Parameters
    ----------
    path : Path
        Path to directory of images for frames in the animation (loaded
        in lexographical order of filenames).
    alpha : float, default: 1.0
        Transparency of the animation.
    interpolation : Interpolation, default: Interpolation.Linear
        Interpolation used when resizing the animation.
    frame_duration : float | int | Sequence[float| int], default: 1/12
        Time between updates of frames of the animation in seconds.
        Raises `ValueError` if a sequence is provided with length not
        equal to the number of frames.
    loop : bool, default: True
        If true, restart animation after last frame.
    """
    def __init__(
        self,
        *,
        path: Path,
        alpha: float=1.0,
        interpolation: Interpolation=Interpolation.LINEAR,
        frame_durations: float | Sequence[float]=1/12,
        loop: bool=True,
        **kwargs
    ):
        super().__init__(**kwargs)

        paths = sorted(path.iterdir(), key=lambda file: file.name)

        self.frames: list[Image] = [Image(size=self.size, path=path) for path in paths]
        if not self.frames:
            raise ValueError(f"{path} empty")

        if isinstance(frame_durations, (int, float)):
            self.frame_durations = [frame_durations] * len(paths)
        else:
            self.frame_durations = frame_durations
            if len(frame_durations) != len(paths):
                raise ValueError("")

        self.loop = loop

        self.alpha = alpha
        self.interpolation = interpolation

        self._i = 0
        self._animation = asyncio.create_task(asyncio.sleep(0))  # dummy task

    def on_size(self):
        for frame in self.frames:
            frame.size = self.size

    @property
    def current_frame(self) -> Image:
        """
        Current frame of animation.
        """
        return self.frames[self._i]

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        self._alpha = alpha

        for frame in self.frames:
            frame.alpha = alpha

    @property
    def interpolation(self) -> Interpolation:
        return self._interpolation

    @interpolation.setter
    def interpolation(self, interpolation: Interpolation):
        self._interpolation = interpolation

        for frame in self.frames:
            frame.interpolation = interpolation

    async def _play_animation(self):
        while True:
            try:
                await asyncio.sleep(self.frame_durations[self._i])
            except asyncio.CancelledError:
                break

            self._i += 1
            if self._i >= len(self.frames):
                if not self.loop:
                    return

                self._i = 0

    def play(self):
        """
        Play animation.
        """
        self.pause()
        self._animation = asyncio.create_task(self._play_animation())

    def pause(self):
        """
        Pause animation.
        """
        self._animation.cancel()

    def stop(self):
        """
        Stop animation.
        """
        self.pause()
        self._i = 0

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        self.current_frame.render_intersection(source, canvas_view, colors_view)
        super().render(canvas_view, colors_view, source)
