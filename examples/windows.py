from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.animation import Animation, Interpolation
from nurses_2.widgets.file_chooser import FileChooser
from nurses_2.widgets.color_picker import ColorPicker
from nurses_2.widgets.window import Window

CAVEMAN_PATH = Path("frames") / "caveman"


class MyApp(App):
    async def on_start(self):
        animation = Animation(size_hint=(1.0, 1.0), path=CAVEMAN_PATH, interpolation=Interpolation.NEAREST)
        animation.play()
        window_1 = Window(size=(25, 50), alpha=.7, title=CAVEMAN_PATH.name)
        window_1.add_widget(animation)

        window_2 = Window(size=(25, 50), alpha=.7, title="File Chooser")
        window_2.add_widget(FileChooser(size_hint=(1.0, 1.0)))

        window_3 = Window(size=(25, 50), alpha=.7, title="Color Picker")
        window_3.add_widget(ColorPicker(size_hint=(1.0, 1.0)))

        self.add_widgets(window_1, window_2, window_3)


MyApp().run()
