import asyncio
import atexit
from pathlib import Path
import time
from typing import Union

import cv2
import numpy as np

from ..colors import BLACK_ON_BLACK
from .widget import Widget


# Seeking is not implemented yet, but may get added soon™
class VideoPlayer(Widget):
    """
    A video player.

    Parameters
    ----------
    source : pathlib.Path | str | int
        A path to video, URL to video stream, or capturing device (by index).
    """
    def __init__(self, *args, source: Union[Path, str, int], **kwargs):
        kwargs.pop('default_char', None)
        kwargs.pop('default_color_pair', None)
        kwargs.pop('is_transparent', None)

        super().__init__(*args, default_char="▀", default_color_pair=BLACK_ON_BLACK, **kwargs)

        self._resource = None
        self._video = asyncio.create_task(asyncio.sleep(0))  # dummy task

        self.source = source

    @property
    def video(self):
        return self._video

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, new_source):
        self.stop()
        self._source = new_source

    def _load_video(self):
        source = self.source
        if isinstance(source, Path):
            source = str(source)

        self._resource = cv2.VideoCapture(source)
        atexit.register(self._resource.release)

    def close(self):
        if self._resource is not None:
            self._resource.release()

            # `cv2` may write warnings to stdout on Windows when releasing cameras.
            # We force a screen regeneration by calling resize on the root widget.
            self.root.resize(self.root.dim)

            atexit.unregister(self._resource.release)
            self._resource = None
            self._current_frame = None
            self.canvas[:] = self.default_char
            self.colors[:, :] = self.default_color_pair

    def resize(self, dim):
        super().resize(dim)

        # If video is paused, resize current frame.
        if self._video.done() and self._current_frame is not None:
            dim = self.width, 2 * self.height
            resized_frame = cv2.resize(self._current_frame, dim)
            BGR_to_RGB = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

            np.concatenate((BGR_to_RGB[::2], BGR_to_RGB[1::2]), axis=-1, out=self.colors)

    async def _play_video(self):
        # Bring in to locals:
        concat = np.concatenate
        resize = cv2.resize
        recolor = cv2.cvtColor
        MSEC = cv2.CAP_PROP_POS_MSEC
        BGR2RGB = cv2.COLOR_BGR2RGB
        monotonic = time.monotonic

        video_get = self._resource.get
        video_grab = self._resource.grab
        video_retrieve = self._resource.retrieve

        video_grab()
        start_time = monotonic() - video_get(MSEC) / 1000

        while True:
            if not video_grab():
                break

            seconds_ahead = video_get(MSEC) / 1000 + start_time - monotonic()
            if seconds_ahead < 0:
                continue

            ret_flag, self._current_frame = video_retrieve()
            if not ret_flag:
                break

            dim = self.width, 2 * self.height
            resized_frame = resize(self._current_frame, dim)
            BGR_to_RGB = recolor(resized_frame, BGR2RGB)

            concat((BGR_to_RGB[::2], BGR_to_RGB[1::2]), axis=-1, out=self.colors)

            try:
                await asyncio.sleep(seconds_ahead)
            except asyncio.CancelledError:
                return

        self.close()

    def play(self):
        """
        Play video.
        """
        if self._resource is None:
            self._load_video()

        self._video.cancel()
        self._video = asyncio.create_task(self._play_video())

    def pause(self):
        """
        Pause video.
        """
        self._video.cancel()

    def stop(self):
        """
        Stop video.
        """
        self.pause()
        self.close()
