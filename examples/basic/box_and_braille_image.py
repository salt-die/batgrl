from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.box_image import BoxImage
from batgrl.gadgets.braille_image import BrailleImage

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_IMAGE = ASSETS / "loudypixelsky.png"


class ImageApp(App):
    async def on_start(self):
        box_image = BoxImage(
            path=PATH_TO_IMAGE, size_hint={"height_hint": 1.0, "width_hint": 0.5}
        )
        braille_image = BrailleImage(
            path=PATH_TO_IMAGE,
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
            pos_hint={"x_hint": 0.5, "anchor": "top-left"},
        )
        self.add_gadgets(box_image, braille_image)


if __name__ == "__main__":
    ImageApp(title="Box and Braille Image Example").run()
