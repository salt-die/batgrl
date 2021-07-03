import asyncio
from contextlib import contextmanager
from pathlib import Path
import time

import cv2

from nurses_2.widgets import Widget

@contextmanager
def open_video(path):
    video = cv2.VideoCapture(str(path))

    try:
        yield video
    finally:
        video.release()


# This is a very remedial video player with no controls.  It may be expanded in the future.
class VideoPlayer(Widget):
    def __init__(self, *args, path: Path, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path

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

                    dim = self.width, self.height
                    resized_frame = cv2.resize(frame, dim)
                    BGR_to_RGB = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

                    self.colors[:, :, 3:] = BGR_to_RGB

                try:
                    await asyncio.sleep(0)
                except asyncio.CancelledError:
                    return

    def start(self):
        asyncio.create_task(self._play_video())
