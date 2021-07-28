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
    size_hint : SizeHint, default: (1.0, 1.0)
        Dimension as a proportion of parent's dimension. None indicates
        height or width attribute will be used normally.
    """
    def __init__(self, *args, size_hint: SizeHint=SizeHint(1.0, 1.0), **kwargs):
        self.h_hint, self.w_hint = size_hint

        assert _is_valid_hint(self.h_hint) and _is_valid_hint(self.w_hint), f"{size_hint!r} is not a valid size hint."

        super().__init__(*args, **kwargs)

    def update_geometry(self):
        h_hint = self.h_hint
        w_hint = self.w_hint

        h, w = self.parent.dim

        height = self.height if h_hint is None else int(h_hint * h)
        width = self.width if w_hint is None else int(w_hint * w)

        self.resize((height, width))

        super().update_geometry()
