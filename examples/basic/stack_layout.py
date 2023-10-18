from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.image import Image
from batgrl.gadgets.stack_layout import HStackLayout, VStackLayout

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_LOGO_FLAT = ASSETS / "logo_solo_flat_256.png"
PATH_TO_LOGO_FULL = ASSETS / "python_discord_logo.png"


class StackLayoutApp(App):
    async def on_start(self):
        images = [
            Image(path=PATH_TO_LOGO_FLAT if i % 2 else PATH_TO_LOGO_FULL)
            for i in range(9)
        ]
        hstacks = [HStackLayout() for i in range(3)]
        hstacks[0].add_gadgets(images[:3])
        hstacks[1].add_gadgets(images[3:6])
        hstacks[2].add_gadgets(images[6:])
        vstack = VStackLayout(size_hint={"height_hint": 1.0, "width_hint": 1.0})
        vstack.add_gadgets(hstacks)
        self.add_gadget(vstack)


if __name__ == "__main__":
    StackLayoutApp(title="Stack Layout Example").run()
