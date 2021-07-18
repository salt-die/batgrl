import asyncio
from pathlib import Path
from typing import Iterable, Sequence, Union

from ..colors import BLACK_ON_BLACK
from .widget import Widget
from .image import Image, Interpolation


class Animation(Widget):
    """
    An animation widget.

    Parameters
    ----------
    paths : Path | Iterable[Path]
        Path to folder of images for frames in animation (loaded in lexographical order of
        filenames) or an iterable of paths to each frame in the animation.
    animation_speed : float | Sequence[float], default: 1/12
        Time between updates of frames of the animation in seconds.  If sequence is
        provided it must have length equal to number of frames in the animation.
    loop : bool, default: True
        If true, restart animation after last frame.
    alpha : float, default: 1.0
        If a frame has an alpha channel, it will be multiplied by `alpha`.
        Otherwise, `alpha` is default value for a frame's alpha channel.
    interpolation : Interpolation, default: Interpolation.LINEAR
        The interpolation used when resizing the animation.
    """

    def __init__(
        self,
        *args,
        paths: Union[Path, Iterable[Path]],
        animation_speed: Union[float, Sequence[float]]=1/12,
        loop=True,
        alpha=1.0,
        interpolation=Interpolation.LINEAR,
        **kwargs
    ):
        # Assert each path exists.
        if isinstance(paths, Path):
            assert paths.exists(), f"{paths} doesn't exist"
            assert paths.is_dir(), f"{paths} isn't a directory"
            paths = sorted((file for file in paths.iterdir() if file.is_file()), key=lambda file: file.name)
        else:
            paths = list(paths)
            for path in paths:
                assert path.exists(), f"{path} doesn't exist"
                assert path.is_file(), f"{path} isn't a file"

        # Assert number of frames matches length of animation_speed
        if not isinstance(animation_speed, float):
            assert len(animation_speed) == len(frames), (
                f"number of frames ({len(frames)}) not equal"
                f" to length of animation_speed ({len(animation_speed)})"
            )
        else:
            animation_speed = (animation_speed, ) * len(paths)

        kwargs.pop('default_char', None)
        kwargs.pop('default_color', None)
        super().__init__(*args, default_char="▀", default_color=BLACK_ON_BLACK, **kwargs)

        self.frames = tuple(
            (Image(dim=self.dim, path=path, alpha=alpha, interpolation=interpolation), time)
            for path, time in zip(paths, animation_speed)
        )
        for frame, _ in self.frames:
            frame.parent = self

        self.loop = loop

        self.add_widget(self.frames[0][0])
        self.current_frame = 0

        self._animation = asyncio.create_task(asyncio.sleep(0))  # dummy task

    def resize(self, dim):
        for frame, _ in self.frames:
            frame.resize(dim)

        super().resize(dim)

    async def _play_animation(self):
        frames = self.frames
        children = self.children

        while True:
            children[0], sleep = frames[self.current_frame]

            try:
                await asyncio.sleep(sleep)
            except asyncio.CancelledError:
                break

            self.current_frame += 1
            if self.current_frame >= len(frames):
                self.current_frame = 0
                if not self.loop:
                    break

    def play(self):
        self.stop()
        self._animation = asyncio.create_task(self._play_animation())

    def pause(self):
        self._animation.cancel()

    def stop(self):
        self.pause()
        self.current_frame = 0
        self.children[0] = self.frames[0][0]
