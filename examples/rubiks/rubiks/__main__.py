from pathlib import Path

from nurses_2.app import App

from .rubiks_cube import RubiksCube

PATH_TO_BACKGROUND = Path("..") / "frames" / "night"


class RubiksApp(App):
    async def on_start(self):
        self.add_widget(
            RubiksCube(
                background_image_path=PATH_TO_BACKGROUND,
                size_hint=(1.0, 1.0),
            )
        )

RubiksApp().run()
