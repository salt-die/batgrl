import asyncio
from contextlib import contextmanager
from pathlib import Path
import time

import cv2
import numpy as np

from .widget import Widget
from ..colors import BLACK_ON_BLACK

@contextmanager
def open_video(path):
    video = cv2.VideoCapture(str(path))

    try:
        yield video
    finally:
        video.release()


# This is a very remedial video player.  Currently it only starts and stops.
# Seeking and other controls from `cv2` may get added in the future.
class VideoPlayer(Widget):
    """
    A video player.
    """
    def __init__(self, *args, path: Path, **kwargs):
        kwargs.pop('default_char', None)
        kwargs.pop('default_color', None)

        super().__init__(*args, default_char="▀", default_color=BLACK_ON_BLACK, **kwargs)

        self.path = path
        self._video = asyncio.create_task(asyncio.sleep(0))  # dummy task

    async def _play_video(self):
        with open_video(self.path) as video:
            start_time = time.monotonic()

            while True:
                delta = video.get(cv2.CAP_PROP_POS_MSEC) / 1000 + start_time - time.monotonic()

                # This check prevents video from rendering too fast.
                if delta <= 0:
                    read_flag, frame = video.read()
                    if not read_flag:
                        return

                    dim = self.width, 2 * self.height
                    resized_frame = cv2.resize(frame, dim)
                    BGR_to_RGB = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

                    self.colors[:, :, :3] = BGR_to_RGB[::2]
                    self.colors[:, :, 3:] = BGR_to_RGB[1::2]

                try:
                    await asyncio.sleep(0)
                except asyncio.CancelledError:
                    return

    def start(self):
        self._video = asyncio.create_task(self._play_video())

    def stop(self):
        self._video.cancel()
