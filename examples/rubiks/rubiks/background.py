from pathlib import Path

from nurses_2.widgets.animation import Animation, Interpolation
from nurses_2.widgets.behaviors import AutoSizeBehavior

PATH_TO_BACKGROUND = Path("..") / "frames" / "night"


class Background(AutoSizeBehavior, Animation):
    def __init__(self):
        super().__init__(
            paths=PATH_TO_BACKGROUND,
            interpolation=Interpolation.NEAREST,
            is_enabled=False,
        )
