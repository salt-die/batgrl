"""
An example of how to play videos with batgrl.

`Video.source` can be a `pathlib.Path` to a video, an URL as a string, or an int
for a capturing device.
"""

from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.video import Video

ASSETS = Path(__file__).parent.parent / "assets"
SPINNER = ASSETS / "spinner.gif"


class VideoApp(App):
    async def on_start(self):
        half_video = Video(
            source=SPINNER,
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
        )  # Try `source=0` to capture a webcam.
        sixel_video = Video(
            source=SPINNER,
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
            pos_hint={"x_hint": 0.5, "anchor": "top-left"},
            blitter="sixel",
        )
        self.add_gadgets(half_video, sixel_video)
        half_video.play()
        sixel_video.play()


if __name__ == "__main__":
    VideoApp(title="Video Example").run()
