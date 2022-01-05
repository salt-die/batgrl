from nurses_2.app import App

from .minesweeper import MineSweeper, Anchor


class MineSweeperApp(App):
    async def on_start(self):
        self.add_widget(
            MineSweeper(pos_hint=(.5, .5), anchor=Anchor.CENTER)
        )


MineSweeperApp(title="MineSweeper").run()
