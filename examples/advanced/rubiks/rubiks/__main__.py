from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.image import Image

from .rubiks_cube import RubiksCube

ASSETS = Path(__file__).parent.parent.parent.parent / "assets"
PATH_TO_BACKGROUND = ASSETS / "background.png"


class RubiksApp(App):
    async def on_start(self):
        self.add_widgets(
            Image(path=PATH_TO_BACKGROUND, size_hint=(1.0, 1.0), alpha=0.2),
            RubiksCube(size_hint=(1.0, 1.0)),
        )


RubiksApp(title="Rubiks 3D").run()
