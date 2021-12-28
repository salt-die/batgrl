"""
How to play videos with nurses.

Requires opencv-python.
"""
import pathlib

from nurses_2.app import App
from nurses_2.widgets.video_player import VideoPlayer

PATH_TO_VIDEO: pathlib.Path = pathlib.Path("path") / "to" / "video.mp4"


class MyApp(App):
    async def on_start(self):
        player = VideoPlayer(source=PATH_TO_VIDEO, size_hint=(1.0, 1.0))

        self.root.add_widget(player)
        player.play()


MyApp().run()
