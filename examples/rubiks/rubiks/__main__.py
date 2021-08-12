from nurses_2.app import App
from nurses_2.widgets.behaviors import AutoSizeBehavior

from .rubiks_cube import RubiksCube


class AutoSizeRubiksCube(AutoSizeBehavior, RubiksCube):
    ...


class RubiksApp(App):
    async def on_start(self):
        self.root.add_widget( AutoSizeRubiksCube() )

RubiksApp().run()
