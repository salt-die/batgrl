"""
An example of how to play videos with nurses.

`VideoPlayer.source` can be a `pathlib.Path` to a video, an URL as a string, or an int for a capturing device.
"""
from nurses_2.app import App
from nurses_2.widgets.braille_video_player import BrailleVideoPlayer
from nurses_2.widgets.video_player import VideoPlayer

LINK_TO_VIDEO = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"


class MyApp(App):
    async def on_start(self):
        video = VideoPlayer(source=LINK_TO_VIDEO, size_hint=(1.0, .5))  # Try `source=0` to capture a webcam.
        braille_video = BrailleVideoPlayer(source=LINK_TO_VIDEO, size_hint=(1.0, .5), pos_hint=(0, .5))

        self.add_widgets(video, braille_video)
        video.play()
        braille_video.play()


MyApp(title="Video Example").run()
