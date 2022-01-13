from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.animation import Animation

from .rubiks_cube import RubiksCube

PATH_TO_BACKGROUND = Path("..") / "frames" / "night"


class RubiksApp(App):
    async def on_start(self):
        background = Animation(path=PATH_TO_BACKGROUND, size_hint=(1.0, 1.0))

        self.add_widgets(
            background,
            RubiksCube(size_hint=(1.0, 1.0)),
        )

        background.play()

RubiksApp().run()
