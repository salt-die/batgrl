from itertools import cycle
from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.text_widget import Easing, TextWidget

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_LOGO = ASSETS / "logo_solo_flat_256.png"

ALPHAS = cycle((0.1, 1.0))
POS_HINTS = cycle(((0.0, 0.0), (0.5, 0.5)))
SIZE_HINTS = cycle(((0.25, 0.25), (0.5, 0.5)))


class MyApp(App):
    async def on_start(self):
        logo = Image(
            path=PATH_TO_LOGO,
            size_hint=next(SIZE_HINTS),
            pos_hint=next(POS_HINTS),
        )

        label = TextWidget(size=(1, 30), pos_hint=(None, 0.5), anchor="top")

        self.add_widgets(logo, label)

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


MyApp(title="Easings Example").run()
