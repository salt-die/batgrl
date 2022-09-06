from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.image import Image

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_LOGO_FLAT = ASSETS / "logo_solo_flat_256.png"
PATH_TO_LOGO_FULL = ASSETS / "python_discord_logo.png"
PATH_TO_BACKGROUND = ASSETS / "background.png"


class MyApp(App):
    async def on_start(self):
        background = Image(size_hint=(1.0, 1.0), path=PATH_TO_BACKGROUND)

        logo_flat = Image(
            size_hint=(.5, .5),
            path=PATH_TO_LOGO_FLAT,
        )

        logo_full = Image(
            size_hint=(.5, .5),
            pos_hint=(.5, .5),
            path=PATH_TO_LOGO_FULL,
            alpha=.8,
        )

        self.add_widgets(background, logo_flat, logo_full)


MyApp(title="Image Example").run()
