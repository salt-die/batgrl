import asyncio
from pathlib import Path
from typing import Sequence

from .graphic_widget import GraphicWidget, Interpolation
from .image import Image


class Animation(GraphicWidget):
    """
    An animation widget.

    Parameters
    ----------
    path : Path
        Path to directory of images for frames in animation (loaded in lexographical
        order of filenames).
    frame_duration : float | int | Sequence[float| int], default: 1/12
        Time between updates of frames of the animation in seconds.  If a sequence is
        provided it should have length equal to number of frames in the animation.
    loop : bool, default: True
        If true, restart animation after last frame.
    """
    def __init__(
        self,
        *,
        path: Path,
        frame_durations: float | Sequence[float]=1/12,
        loop: bool=True,
        **kwargs
    ):
        # Setting alpha and interpolation properties will
        # also update frames. Dummy frames are needed.
        self.frames = ()

        super().__init__(**kwargs)

        paths = sorted(path.iterdir(), key=lambda file: file.name)

        self.frames = [
            Image(
                size_hint=(1.0, 1.0),
                path=path,
                interpolation=self.interpolation,
                alpha=self.alpha,
                is_visible=False,
            )
            for path in paths
        ]
        if not self.frames:
            raise ValueError(f"{path} empty")

        self.add_widgets(self.frames)

        if isinstance(frame_durations, (int, float)):
            self.frame_durations = [frame_durations] * len(paths)
        else:
            self.frame_durations = frame_durations

        self.loop = loop

        self._i = 0
        self.current_frame.is_visible = True
        self._animation = asyncio.create_task(asyncio.sleep(0))  # dummy task

    @property
    def current_frame(self):
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
            self.frames[self._i].is_visible = True

            try:
                await asyncio.sleep(self.frame_durations[self._i])
            except asyncio.CancelledError:
                break

            self._i += 1
            if self._i >= len(self.frames):
                self._i = 0

                if not self.loop:
                    break

            self.frames[self._i - 1].is_visible = False

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
        self.current_frame.is_visible = False

        self._i = 0
        self.current_frame.is_visible = True
