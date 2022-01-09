import cv2
import numpy as np

from ...data_structures import Size
from .._binary_to_braille import binary_to_braille
from ..text_widget import TextWidget


class _Traces(TextWidget):
    def __init__(
        self,
        *points: list[float] | np.ndarray,
        xmin: float | None=None,
        xmax: float | None=None,
        ymin: float | None=None,
        ymax: float | None=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
