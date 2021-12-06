import asyncio
from pathlib import Path
from typing import Iterable, Sequence

from .graphic_widget import GraphicWidget, Interpolation
from .image import Image


class Animation(GraphicWidget):
    """
    An animation widget.

    Parameters
    ----------
    paths : Path | Iterable[Path]
        Path to folder of images for frames in animation (loaded in lexographical
        order of filenames) or an iterable of paths to each frame in the animation.
    frame_duration : float | int | Sequence[float| int], default: 1/12
        Time between updates of frames of the animation in seconds.  If a sequence is
        provided it should have length equal to number of frames in the animation.
    loop : bool, default: True
        If true, restart animation after last frame.
    """
    def __init__(
        self,
        *args,
        paths: Path | Iterable[Path],
        frame_durations: float | Sequence[float]=1/12,
        loop: bool=True,
        **kwargs
    ):
        # Setting alpha and interpolation properties will
        # also update frames. Dummy frames are needed.
        self.frames = ()

        super().__init__(*args, **kwargs)

        if isinstance(paths, Path):
            paths = sorted(
                (file for file in paths.iterdir() if file.is_file()),
                key=lambda file: file.name,
            )

        self.frames = [
            Image(
                size=self.size,
                path=path,
                interpolation=self.interpolation,
            )
            for path in paths
        ]

        for frame in self.frames:
            frame.parent = self

        if isinstance(frame_durations, (int, float)):
            self.frame_durations = [frame_durations] * len(paths)
        else:
            self.frame_durations = frame_durations

        self.loop = loop

        self._current_frame = 0
        self._animation = asyncio.create_task(asyncio.sleep(0))  # dummy task

        self.add_widget(self.frames[0])

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        self._alpha = alpha

        for frame in self.frames:
            frame.alpha = alpha

    @property
    def interpolation(self):
        return self._interpolation

    @interpolation.setter
    def interpolation(self, interpolation):
        self._interpolation = interpolation

        for frame in self.frames:
            frame.interpolation = interpolation

    @property
    def current_frame_index(self):
        return self._current_frame

    @property
    def current_frame(self):
        return self.frames[self._current_frame]

    def resize(self, size):
        for frame in self.frames:
            frame.resize(size)

        super().resize(size)

    async def _play_animation(self):
        frames = self.frames
        frame_durations = self.frame_durations
        children = self.children

        while True:
            children[0] = frames[self._current_frame]

            try:
                await asyncio.sleep(frame_durations[self._current_frame])
            except asyncio.CancelledError:
                break

            if self._current_frame == len(frames) - 1 and not self.loop:
                break

            self._current_frame = (self._current_frame + 1) % len(frames)

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
        self._current_frame = 0
        self.children[0] = self.frames[0]
