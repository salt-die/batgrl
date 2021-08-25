from nurses_2.app import App
from nurses_2.widgets.behaviors import Anchor, AutoPositionBehavior

from .minesweeper import MineSweeper


class AutoPositionMineSweeper(AutoPositionBehavior, MineSweeper):
    ...


class MineSweeperApp(App):
    async def on_start(self):
        self.root.add_widget(
            AutoPositionMineSweeper(pos_hint=(.5, .5), anchor=Anchor.CENTER)
        )


MineSweeperApp().run()
