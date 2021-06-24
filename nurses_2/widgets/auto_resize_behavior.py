from .widget import Widget

def _is_valid_hint(hint):
    return hint is None or 0 < hint


class AutoResizeBehavior:
    """
    Resize to some percentage of parent (given by `size_hint`) when parent is resized.
    """
    def __init__(self, pos=(0, 0), *, size_hint=(1.0, 1.0), **kwargs):
        self.h_hint, self.w_hint = size_hint

        assert _is_valid_hint(self.h_hint) and _is_valid_hint(self.w_hint), f'{size_hint!r} is not a valid size hint'

        super().__init__((10, 10), pos, **kwargs)

        if self.parent:
            update_geometry(self.parent.dim)

    def update_geometry(self, dim):
        h_hint = self.h_hint
        w_hint = self.w_hint

        h, w = dim

        height = self.height if h_hint is None else int(h_hint * h)
        width = self.width if w_hint is None else int(w_hint * w)

        self.resize((height, width))

        super().update_geometry(dim)
