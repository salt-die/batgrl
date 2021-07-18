import asyncio
from contextlib import contextmanager
from pathlib import Path
import time

import cv2
import numpy as np

from ..colors import BLACK_ON_BLACK
from .widget import Widget


# This is a very remedial video player.  Currently it only starts and stops.
# Seeking and other controls from `cv2` may get added in the future.
class VideoPlayer(Widget):
    """
    A video player.

    Parameters
    ----------
    path : pathlib.Path
        Path to video.
    """
    def __init__(self, *args, path: Path, **kwargs):
        kwargs.pop('default_char', None)
        kwargs.pop('default_color', None)
        kwargs.pop('is_transparent', None)

        super().__init__(*args, default_char="▀", default_color=BLACK_ON_BLACK, **kwargs)

        self.path = path
        self._video = asyncio.create_task(asyncio.sleep(0))  # dummy task

    async def _play_video(self):
        with open_video(self.path) as video:
            # Bring in to locals:
            concat = np.concatenate
            resize = cv2.resize
            recolor = cv2.cvtColor
            MSEC = cv2.CAP_PROP_POS_MSEC
            BGR2RGB = cv2.COLOR_BGR2RGB
            monotonic = time.monotonic

            video_get = video.get
            video_read = video.read

            start_time = monotonic()

            while True:
                seconds_ahead = video_get(MSEC) / 1000 + start_time - monotonic()

                if seconds_ahead <= 0:  # Prevents video from rendering too fast.
                    read_flag, frame = video_read()
                    if not read_flag:
                        return

                    dim = self.width, 2 * self.height
                    resized_frame = resize(frame, dim)
                    BGR_to_RGB = recolor(resized_frame, BGR2RGB)

                    concat((BGR_to_RGB[::2], BGR_to_RGB[1::2]), axis=-1, out=self.colors)

                    seconds_ahead = 0

                try:
                    await asyncio.sleep(seconds_ahead)
                except asyncio.CancelledError:
                    return

    def play(self):
        self._video = asyncio.create_task(self._play_video())

    def stop(self):
        self._video.cancel()


@contextmanager
def open_video(path):
    video = cv2.VideoCapture(str(path))

    try:
        yield video
    finally:
        video.release()
