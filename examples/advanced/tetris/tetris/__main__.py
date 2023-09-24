from nurses_2.app import App

from .tetris import Tetris


class TetrisApp(App):
    async def on_start(self):
        tetris = Tetris(pos_hint=(0.5, 0.5))

        self.add_widget(tetris)

        tetris.modal_screen.enable(callback=tetris.new_game, is_game_over=True)


if __name__ == "__main__":
    TetrisApp(title="Tetris").run()
