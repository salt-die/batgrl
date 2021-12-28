from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.animation import Animation
from nurses_2.widgets.graphic_widget import Interpolation, Anchor

PATH_TO_FRAMES_DIR = Path("frames") / "caveman"


class MyApp(App):
    async def on_start(self):
        animation = Animation(
            size_hint=(.5, .5),
            anchor=Anchor.CENTER,
            pos_hint=(.5, .5),
            paths=PATH_TO_FRAMES_DIR,
            interpolation=Interpolation.NEAREST,
        )

        self.root.add_widget(animation)
        animation.play()


MyApp().run()
