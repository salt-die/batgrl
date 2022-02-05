from pathlib import Path

from nurses_2.app import run_widget_as_app
from nurses_2.widgets.braille_image import BrailleImage

IMG_SOURCE = Path("images") / "sunset.jpg"

run_widget_as_app(BrailleImage, path=IMG_SOURCE, size_hint=(1.0, 1.0))
