import asyncio
from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.animation import Animation, Interpolation
from nurses_2.widgets.auto_position_behavior import Anchor, AutoPositionBehavior


PATH_TO_FRAMES_DIR = Path('frames')


class AutoPositionAnimation(AutoPositionBehavior, Animation):
    pass


class MyApp(App):
    async def on_start(self):
        animation = AutoPositionAnimation(
            dim=(14, 30),
            anchor=Anchor.CENTER,
            pos_hint=(.5, .5),
            paths=PATH_TO_FRAMES_DIR,
            interpolation=Interpolation.NEAREST,
        )

        self.root.add_widget(animation)
        animation.play()


MyApp().run()
