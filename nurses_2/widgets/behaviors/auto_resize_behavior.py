from typing import NamedTuple, Optional

def _is_valid_hint(hint):
    return hint is None or 0 < hint


class SizeHint(NamedTuple):
    height: Optional[float]
    width: Optional[float]


class AutoSizeBehavior:
    """
    Dimensions of widget are set to some proportion of its parent's dimensions (given by `size_hint`).

    Notes
    -----
    If a user widget is inheriting both AutoSizeBehavior and AutoPositionBehavior, AutoSizeBehavior should be
    before AutoPositionBehavior as anchor position will require the correct dimensions of the widget.

    Parameters
    ----------
    size_hint : SizeHint, default: SizeHint(1.0, 1.0)
        Dimension as a proportion of parent's dimension. A None in the size_hint indicates
        height or width attribute will be used to size the widget normally.
    """
    def __init__(self, *args, size_hint: SizeHint=SizeHint(1.0, 1.0), **kwargs):
        super().__init__(*args, **kwargs)

        self.size_hint = size_hint

    @property
    def size_hint(self):
        return self._size_hint

    @size_hint.setter
    def size_hint(self, value):
        y, x = value
        assert _is_valid_hint(y) and _is_valid_hint(x), f"{value!r} is not a valid size hint."

        self._size_hint = value
        if self.parent:
            self.update_geometry()

    def update_geometry(self):
        h, w = self.parent.dim
        h_hint, w_hint = self.size_hint

        height = self.height if h_hint is None else int(h_hint * h)
        width = self.width if w_hint is None else int(w_hint * w)

        self.resize((height, width))

        super().update_geometry()
