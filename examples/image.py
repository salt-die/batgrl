from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.image import Image

IMAGE_DIR = Path("images")
PATH_TO_LOGO_FLAT = IMAGE_DIR / "logo_solo_flat_256.png"
PATH_TO_LOGO_FULL = IMAGE_DIR / "python_discord_logo.png"
PATH_TO_BACKGROUND = IMAGE_DIR / "background.png"


class MyApp(App):
    async def on_start(self):
        background = Image(path=PATH_TO_BACKGROUND)

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


MyApp().run()
