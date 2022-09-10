from pathlib import Path

from nurses_2.app import run_widget_as_app
from nurses_2.widgets.braille_image import BrailleImage

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_IMAGE = ASSETS / "loudypixelsky.png"

run_widget_as_app(BrailleImage(path=PATH_TO_IMAGE, size_hint=(1.0, 1.0)))
