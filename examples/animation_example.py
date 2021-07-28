import asyncio
from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.animation import Animation, Interpolation
from nurses_2.widgets.behaviors import Anchor, AutoPositionBehavior, AutoSizeBehavior


PATH_TO_FRAMES_DIR = Path('frames') / 'caveman'


class AutoGeometryAnimation(AutoSizeBehavior, AutoPositionBehavior, Animation):
    pass


class MyApp(App):
    async def on_start(self):
        animation = AutoGeometryAnimation(
            size_hint=(.5, .5),
            anchor=Anchor.CENTER,
            pos_hint=(.5, .5),
            paths=PATH_TO_FRAMES_DIR,
            interpolation=Interpolation.NEAREST,
        )

        self.root.add_widget(animation)
        animation.play()


MyApp().run()
