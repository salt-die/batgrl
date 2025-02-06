from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.behaviors.movable import Movable
from batgrl.gadgets.image import Image

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_LOGO_FLAT = ASSETS / "logo_solo_flat_256.png"
PATH_TO_LOGO_FULL = ASSETS / "python_discord_logo.png"
PATH_TO_BACKGROUND = ASSETS / "background.png"


class MovableImage(Movable, Image):
    pass


class ImageApp(App):
    async def on_start(self):
        background = Image(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            path=PATH_TO_BACKGROUND,
            is_transparent=False,
        )

        logo_flat = MovableImage(
            size_hint={"height_hint": 0.5, "width_hint": 0.5},
            path=PATH_TO_LOGO_FLAT,
            ptf_on_grab=True,
        )

        logo_full = MovableImage(
            size_hint={"height_hint": 0.5, "width_hint": 0.5},
            pos_hint={"y_hint": 0.5, "x_hint": 0.5},
            path=PATH_TO_LOGO_FULL,
            blitter="sixel",
            alpha=0.8,
            ptf_on_grab=True,
        )

        self.add_gadgets(background, logo_flat, logo_full)


if __name__ == "__main__":
    ImageApp(title="Image Example").run()
