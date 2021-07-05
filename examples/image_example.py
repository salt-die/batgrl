from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.auto_position_behavior import Anchor, AutoPositionBehavior
from nurses_2.widgets.auto_resize_behavior import AutoResizeBehavior


PATH_TO_STAR = Path('star.png')
PATH_TO_LOGO = Path('python_discord_logo.png')


class AutoGeometryImage(AutoPositionBehavior, AutoResizeBehavior, Image):
    pass


class MyApp(App):
    async def on_start(self):
        star = AutoGeometryImage(
            anchor=Anchor.TOP_LEFT,
            pos_hint=(0, 0),
            size_hint=(.5, .5),
            path=PATH_TO_STAR,
            alpha_threshold=157,
            is_transparent=True,
        )

        logo = AutoGeometryImage(
            anchor=Anchor.TOP_LEFT,
            pos_hint=(.5, .5),
            size_hint=(.5, .5),
            path=PATH_TO_LOGO,
            alpha_threshold=0,
            is_transparent=True,
        )

        self.root.add_widgets(star, logo)


MyApp(default_char="M").run()
