from itertools import cycle
from pathlib import Path

from batgrl.app import App
from batgrl.colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG
from batgrl.gadgets.image import Image
from batgrl.gadgets.text import Text, cell
from batgrl.geometry import Easing

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_LOGO = ASSETS / "logo_solo_flat_256.png"

ALPHAS = cycle((0.1, 1.0))
POS_HINTS = cycle(
    (
        {"y_hint": 0.0, "x_hint": 0.0, "anchor": "top-left"},
        {"y_hint": 0.5, "x_hint": 0.5, "anchor": "top-left"},
    )
)
SIZE_HINTS = cycle(
    ({"height_hint": 0.25, "width_hint": 0.25}, {"height_hint": 0.5, "width_hint": 0.5})
)


class EasingsApp(App):
    async def on_start(self):
        logo = Image(
            path=PATH_TO_LOGO,
            size_hint=next(SIZE_HINTS),
            pos_hint=next(POS_HINTS),
        )

        label = Text(
            size=(1, 30),
            pos_hint={"x_hint": 0.5, "anchor": "top"},
            default_cell=cell(fg_color=DEFAULT_PRIMARY_FG, bg_color=DEFAULT_PRIMARY_BG),
        )

        self.add_gadgets(logo, label)

        for easing in Easing.__args__:
            label.add_str(f"{easing:^30}")

            await logo.tween(
                pos_hint=next(POS_HINTS),
                alpha=next(ALPHAS),
                size_hint=next(SIZE_HINTS),
                easing=easing,
                duration=3.0,
            )

        self.exit()


if __name__ == "__main__":
    EasingsApp(title="Easings Example", bg_color=DEFAULT_PRIMARY_BG).run()
