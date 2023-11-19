"""
An example of how to play videos with batgrl.

`VideoPlayer.source` can be a `pathlib.Path` to a video, an URL as a string, or an int
for a capturing device.
"""
from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.braille_video_player import BrailleVideoPlayer
from batgrl.gadgets.video_player import VideoPlayer

ASSETS = Path(__file__).parent.parent / "assets"
SPINNER = ASSETS / "spinner.gif"


class VideoApp(App):
    async def on_start(self):
        video = VideoPlayer(
            source=SPINNER, size_hint={"height_hint": 1.0, "width_hint": 0.5}
        )  # Try `source=0` to capture a webcam.
        braille_video = BrailleVideoPlayer(
            source=SPINNER,
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
            pos_hint={"y_hint": 0, "x_hint": 0.5, "anchor": "top-left"},
            gray_threshold=170,
        )
        self.add_gadgets(video, braille_video)
        video.play()
        braille_video.play()


if __name__ == "__main__":
    VideoApp(title="Video Example").run()
