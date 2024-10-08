from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.image import Image
from batgrl.gadgets.split_layout import HSplitLayout, VSplitLayout

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_LOGO_FLAT = ASSETS / "logo_solo_flat_256.png"
PATH_TO_LOGO_FULL = ASSETS / "python_discord_logo.png"


class SplitLayoutApp(App):
    async def on_start(self):
        image_tl = Image(
            path=PATH_TO_LOGO_FLAT, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        image_tr = Image(
            path=PATH_TO_LOGO_FULL, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        image_bl = Image(
            path=PATH_TO_LOGO_FULL, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        image_br = Image(
            path=PATH_TO_LOGO_FLAT, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )

        split_layout = HSplitLayout(
            split_row=10,
            top_min_height=5,
            bottom_min_height=5,
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
        )
        top_split_layout = VSplitLayout(
            right_min_width=10,
            left_min_width=10,
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
        )
        bottom_split_layout = VSplitLayout(
            right_min_width=10,
            left_min_width=10,
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
        )

        split_layout.top_pane.add_gadget(top_split_layout)
        split_layout.bottom_pane.add_gadget(bottom_split_layout)

        top_split_layout.left_pane.add_gadget(image_tl)
        top_split_layout.right_pane.add_gadget(image_tr)

        bottom_split_layout.left_pane.add_gadget(image_bl)
        bottom_split_layout.right_pane.add_gadget(image_br)

        self.add_gadget(split_layout)


if __name__ == "__main__":
    SplitLayoutApp(title="Split Layout Example").run()
