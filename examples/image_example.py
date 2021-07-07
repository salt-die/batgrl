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

        logo_flat = AutoGeometryImage(
            size_hint=(.5, .5),
            path=PATH_TO_LOGO_FLAT,
            is_transparent=True,
        )

        logo_full = AutoGeometryImage(
            pos_hint=(.5, .5),
            size_hint=(.5, .5),
            path=PATH_TO_LOGO_FULL,
            is_transparent=True,
        )

        self.root.add_widgets(background, logo_flat, logo_full)


MyApp().run()
