from nurses_2.app import App
from nurses_2.widgets.widget_data_structures import Anchor

from .tetris import Tetris


class TetrisApp(App):
    async def on_start(self):
        tetris = Tetris(pos_hint=(.5, .5), anchor=Anchor.CENTER)

        self.add_widget(tetris)

        tetris.modal_screen.enable(callback=tetris.new_game, is_game_over=True)


TetrisApp().run()
