from pathlib import Path

import cv2

from nurses_2.graphic_app.graphic_app import GraphicApp
from nurses_2.graphic_app.widgets.graphic_widget import GraphicWidget

from nurses_2.widgets.auto_position_behavior import AutoPositionBehavior
from nurses_2.widgets.auto_resize_behavior import AutoResizeBehavior

PATH_TO_LOGO_FLAT = str(Path('logo_solo_flat_256.png'))
PATH_TO_LOGO_FULL = str(Path('python_discord_logo.png'))
PATH_TO_BACKGROUND = str(Path('background.png'))

class AutoGeometryWidget(AutoPositionBehavior, AutoResizeBehavior, GraphicWidget):
    pass


class MyApp(GraphicApp):
    async def on_start(self):
        background = AutoGeometryWidget(source=PATH_TO_BACKGROUND)

        logo_flat = AutoGeometryWidget(
            size_hint=(.5, .5),
            source=PATH_TO_LOGO_FLAT,
        )

        logo_full = AutoGeometryWidget(
            pos_hint=(.5, .5),
            size_hint=(.5, .5),
            source=PATH_TO_LOGO_FULL,
            alpha=.8,
        )

        self.root.add_widgets(background, logo_flat, logo_full)


MyApp().run()
