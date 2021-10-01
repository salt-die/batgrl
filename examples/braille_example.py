from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.braille_graphic_widget import BrailleGraphicWidget
from nurses_2.widgets.behaviors import AutoSizeBehavior

IMG_SOURCE = Path("images") / "sunset.jpg"


class AutoSizeBraille(AutoSizeBehavior, BrailleGraphicWidget):
    ...


class MyApp(App):
    async def on_start(self):
        self.root.add_widget(AutoSizeBraille(path=IMG_SOURCE))


MyApp().run()
