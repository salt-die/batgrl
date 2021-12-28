from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.braille_image import BrailleImage

IMG_SOURCE = Path("images") / "sunset.jpg"


class MyApp(App):
    async def on_start(self):
        self.root.add_widget(BrailleImage(path=IMG_SOURCE, size_hint=(1.0, 1.0)))


MyApp().run()
