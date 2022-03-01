from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.animation import Animation
from nurses_2.widgets.window import Window
from nurses_2.widgets.behaviors.focus_behavior import FocusBehavior

CAVEMAN_PATH = Path("frames") / "caveman"
SPINNER_PATH = Path("frames") / "spinner"
NIGHT_PATH = Path("frames") / "night"


class FocusableWindow(FocusBehavior, Window):
    ...


class MyApp(App):
    async def on_start(self):
        for path in (CAVEMAN_PATH, SPINNER_PATH, NIGHT_PATH):
            window = FocusableWindow(size=(25, 50))
            animation = Animation(size_hint=(1.0, 1.0), path=path)
            window.add_widget(animation)
            animation.play()

            self.add_widget(window)


MyApp().run()
