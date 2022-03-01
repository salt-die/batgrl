from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.animation import Animation
from nurses_2.widgets.window import Window

CAVEMAN_PATH = Path("frames") / "caveman"
SPINNER_PATH = Path("frames") / "spinner"
NIGHT_PATH = Path("frames") / "night"


class MyApp(App):
    async def on_start(self):
        for path in (CAVEMAN_PATH, SPINNER_PATH, NIGHT_PATH):
            window = Window(size=(25, 50), alpha=.7, title=path.name)
            animation = Animation(size_hint=(1.0, 1.0), path=path)
            window.add_widget(animation)
            animation.play()

            self.add_widget(window)


MyApp().run()
