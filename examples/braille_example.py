from pathlib import Path

import cv2
import numpy as np

from nurses_2.app import App
from nurses_2.widgets.braille_graphic_widget import BrailleGraphicWidget
from nurses_2.widgets.behaviors import AutoSizeBehavior

PATH_TO_TREE = Path("images") / "parallax_01" / "00.png"


class AutoSizeBraille(AutoSizeBehavior, BrailleGraphicWidget):
    pass


class MyApp(App):
    async def on_start(self):
        braille_widget = AutoSizeBraille()

        self.root.add_widget(braille_widget)

        img_grey = cv2.imread(str(PATH_TO_TREE), cv2.IMREAD_GRAYSCALE)
        _, img_binary = cv2.threshold(img_grey, 255 >> 1, 1, cv2.THRESH_BINARY)

        h, w = braille_widget.size
        braille_widget.texture = cv2.resize(img_binary, (2 * w, 4 * h))
        braille_widget.apply_texture()

MyApp().run()
