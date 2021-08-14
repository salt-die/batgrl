from nurses_2.app import App
from nurses_2.widgets.behaviors import AutoPositionBehavior, Anchor

from .tetris import Tetris


class AutoPositionTetris(AutoPositionBehavior, Tetris):
    ...


class TetrisApp(App):
    async def on_start(self):
        tetris = AutoPositionTetris(pos_hint=(.5, .5), anchor=Anchor.CENTER)

        self.root.add_widget(tetris)

        tetris.modal_screen.enable(callback=tetris.new_game, is_game_over=True)


TetrisApp().run()
