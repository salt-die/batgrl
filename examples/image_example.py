from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.auto_position_behavior import AutoPositionBehavior
from nurses_2.widgets.auto_resize_behavior import AutoResizeBehavior

PATH_TO_LOGO_FLAT = Path('logo_solo_flat_256.png')
PATH_TO_LOGO_FULL = Path('python_discord_logo.png')
PATH_TO_BACKGROUND = Path('background.png')


class AutoGeometryImage(AutoPositionBehavior, AutoResizeBehavior, Image):
    pass


class MyApp(App):
    async def on_start(self):
        background = AutoGeometryImage(path=PATH_TO_BACKGROUND)

        star = AutoGeometryImage(
            size_hint=(.5, .5),
            path=PATH_TO_LOGO_FLAT,
            alpha_threshold=157,
            is_transparent=True,
        )

        logo = AutoGeometryImage(
            pos_hint=(.5, .5),
            size_hint=(.5, .5),
            path=PATH_TO_LOGO_FULL,
        )

        self.root.add_widgets(background, star, logo)


MyApp().run()
