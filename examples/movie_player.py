import asyncio
from contextlib import contextmanager
from pathlib import Path
import time

import cv2
import numpy as np

from nurses_2.app import App
from nurses_2.widgets import Widget
from nurses_2.widgets.auto_resize_behavior import AutoResizeBehavior

PATH_TO_VIDEO = ""  # Path("path/to/video.mp4")

@contextmanager
def open_video(path):
    video = cv2.VideoCapture(str(path))

    try:
        yield video
    finally:
        video.release()


class VideoPlayer(AutoResizeBehavior, Widget):
    def __init__(self, *args, path, **kwargs):
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

                    self.colors[:, :, 3:] = cv2.cvtColor(cv2.resize(frame, (self.width, self.height)), cv2.COLOR_BGR2RGB)

                try:
                    await asyncio.sleep(0)
                except asyncio.CancelledError:
                    return

    def start(self):
        asyncio.create_task(self._play_video())


class MyApp(App):
    async def on_start(self):
        player = VideoPlayer(path=PATH_TO_VIDEO)

        self.root.add_widget(player)

        player.start()


MyApp().run()
