from pathlib import Path

import cv2
import numpy as np

from nurses_2.app import App
from nurses_2.widgets.braille_graphic_widget import BrailleGraphicWidget
from nurses_2.widgets.behaviors import AutoSizeBehavior

PATH_TO_TREE = Path("images") / "trees.jpg"


class AutoSizeBraille(AutoSizeBehavior, BrailleGraphicWidget):
    def __init__(self, *args, source, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = source

    def update_geometry(self):
        super().update_geometry()
        self.load_texture(self.source)


class MyApp(App):
    async def on_start(self):
        braille_widget = AutoSizeBraille(source=PATH_TO_TREE)
        self.root.add_widget(braille_widget)


MyApp().run()
