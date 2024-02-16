from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.image import Image

from .rubiks_cube import RubiksCube

ASSETS = Path(__file__).parent.parent.parent.parent / "assets"
PATH_TO_BACKGROUND = ASSETS / "background.png"


class RubiksApp(App):
    async def on_start(self):
        background = Image(
            path=PATH_TO_BACKGROUND, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        cube = RubiksCube(size_hint={"height_hint": 1.0, "width_hint": 1.0})
        self.add_gadgets(background, cube)


if __name__ == "__main__":
    RubiksApp(title="Rubiks 3D").run()
