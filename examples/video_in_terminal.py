"""
How to play videos with nurses.

Requires opencv-python.
"""
from nurses_2.app import App
from nurses_2.widgets.auto_resize_behavior import AutoResizeBehavior
from nurses_2.widgets.video_player import VideoPlayer

PATH_TO_VIDEO = ""  # "path/to/video.mp4"


class AutoResizeVideoPlayer(AutoResizeBehavior, VideoPlayer):
    """
    AutoResizeBehavior default arguments will resize VideoPlayer to screen size
    whenever the screen size changes.
    """


class MyApp(App):
    async def on_start(self):
        player = AutoResizeVideoPlayer(path=PATH_TO_VIDEO)

        self.root.add_widget(player)
        player.start()


MyApp().run()
