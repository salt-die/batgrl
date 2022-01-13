from pathlib import Path
from itertools import cycle

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.text_widget import TextWidget, Anchor
from nurses_2.widgets.widget_data_structures import Transition

IMAGE_DIR = Path("images")
PATH_TO_LOGO = IMAGE_DIR / "logo_solo_flat_256.png"

ALPHAS = cycle((0.0, 1.0))
POS_HINTS = cycle(((0.0, 0.0), (.5, .5)))
SIZE_HINTS = cycle(((.25, .25), (.5, .5)))

class MyApp(App):
    async def on_start(self):
        logo = Image(
            path=PATH_TO_LOGO,
            size_hint=next(SIZE_HINTS),
            pos_hint=next(POS_HINTS),
        )

        label = TextWidget(size=(1, 20), pos_hint=(None, .5), anchor=Anchor.TOP_CENTER)

        self.add_widgets(logo, label)

        for transition in Transition:
            label.add_text(f"{transition:^20}")

            await logo.transition(
                pos_hint=next(POS_HINTS),
                alpha=next(ALPHAS),
                size_hint=next(SIZE_HINTS),
                transition_type=transition,
                duration=5.0,
            )

        self.exit()


MyApp().run()
