from .widget import Widget

def _is_valid_hint(hint):
    return hint is None or 0 < hint <= 1


class AutoResizeBehavior:
    """A widget behavior that auto-resizes to some percentage of its parent.
    """
    def __init__(self, *args, size_hint=(1.0, 1.0), **kwargs):
        self.y_hint, self.x_hint = size_hint
        assert _is_valid_hint(self.y_hint) and _is_valid_hint(self.x_hint), f'{size_hint!r} is not a valid size hint'

        super().__init__(*args, **kwargs)

    def update_geometry(self, dim):
        y_hint = self.y_hint
        x_hint = self.x_hint

        y, x = widget.dim

        height = self.height if y_hint is None else int(y_hint * y)
        width = self.width if x_hint is None else int(x_hint * x)

        self.resize((height, width))

        super().update_geometry(dim)
