from .widget_data_structures import SizeHint

def _is_valid_hint(hint):
    return hint is None or 0 < hint


class AutoResizeBehavior:
    """
    Resize to some percentage of parent (given by `size_hint`) when parent is resized.

    Parameters
    ----------
    size_hint : tuple[float | None, float | None], default: (1.0, 1.0)
        Dimension as a percentage of parent's dimension. None indicates
        height or width attribute will be used normally.
    """
    def __init__(self, *args, size_hint: SizeHint=SizeHint(1.0, 1.0), **kwargs):
        self.h_hint, self.w_hint = size_hint

        assert _is_valid_hint(self.h_hint) and _is_valid_hint(self.w_hint), f'{size_hint!r} is not a valid size hint'

        super().__init__(*args, **kwargs)

    def update_geometry(self):
        h_hint = self.h_hint
        w_hint = self.w_hint

        h, w = self.parent.dim

        height = self.height if h_hint is None else int(h_hint * h)
        width = self.width if w_hint is None else int(w_hint * w)

        self.resize((height, width))

        super().update_geometry()
