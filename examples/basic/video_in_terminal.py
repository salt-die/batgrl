"""
An example of how to play videos with batgrl.

`Video.source` can be a `pathlib.Path` to a video, an URL as a string, or an int
for a capturing device.
"""

from pathlib import Path

from batgrl.app import App
from batgrl.colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG
from batgrl.gadgets.braille_video import BrailleVideo
from batgrl.gadgets.video import Video

ASSETS = Path(__file__).parent.parent / "assets"
SPINNER = ASSETS / "spinner.gif"


class VideoApp(App):
    async def on_start(self):
        video = Video(
            source=SPINNER, size_hint={"height_hint": 1.0, "width_hint": 0.5}
        )  # Try `source=0` to capture a webcam.
        braille_video = BrailleVideo(
            source=SPINNER,
            fg_color=DEFAULT_PRIMARY_FG,
            bg_color=DEFAULT_PRIMARY_BG,
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
            pos_hint={"x_hint": 0.5, "anchor": "top-left"},
            gray_threshold=155,
            enable_shading=True,
        )
        self.add_gadgets(video, braille_video)
        video.play()
        braille_video.play()


if __name__ == "__main__":
    VideoApp(title="Video Example").run()
