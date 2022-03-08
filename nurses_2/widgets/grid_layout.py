from .widget import Anchor, PosHint, SizeHint, Widget

__all__ = "Container", "GridLayout"


class GridLayout(Widget):
    """
    A widget that automatically positions and resizes its children into a grid.

    Notes
    -----
    Re-ordering children (such as through `pull_to_front`) and calling `_reposition_children`
    will change the positions of the children in the grid.

    Parameters
    ----------
    grid_rows : int, default: 1
        Number of rows.
    grid_columns : int, default: 1
        Number of columns.

    Raises
    ------
    ValueError
        If grid is full and `add_widget` is called.
    """
    def __init__(self, grid_rows: int=1, grid_columns: int=1, **kwargs):
        self.grid_rows = grid_rows
        self.grid_columns = grid_columns

        super().__init__(**kwargs)

    def _reposition_children(self):
        r, c = self.grid_rows, self.grid_columns
        r_hint, c_hint = size_hint = SizeHint(1 / r, 1 / c)

        for i, child in enumerate(self.children):
            y, x = divmod(i, c)
            child._pos_hint = PosHint(y * r_hint, x * c_hint)
            child.anchor = Anchor.TOP_LEFT
            child._size_hint = size_hint
            child.update_geometry()

    @property
    def grid_rows(self) -> int:
        return self._grid_rows

    @grid_rows.setter
    def grid_rows(self, grid_rows: int):
        self._grid_rows = grid_rows
        self._reposition_children()

    @property
    def grid_columns(self) -> int:
        return self._grid_columns

    @grid_columns.setter
    def grid_columns(self, grid_columns: int):
        self._grid_columns = grid_columns
        self._reposition_children()

    def add_widget(self, widget):
        rows, columns = self.grid_rows, self.grid_columns

        if len(self.children) >= rows * columns:
            raise ValueError("too many children, grid is full")

        r_hint, c_hint = 1 / rows, 1 / columns

        y, x = divmod(len(self.children), columns)
        widget._pos_hint = PosHint(y * r_hint, x * c_hint)
        widget._size_hint = SizeHint(r_hint, c_hint)

        super().add_widget(widget)
