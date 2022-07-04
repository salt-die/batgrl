"""
A grid layout widget.
"""
from enum import Enum
from itertools import product, accumulate

from .widget import Size, Widget

__all__ = "GridLayout", "Orientation"


class Orientation(str, Enum):
    """
    Orientation of the grid. For instance, `LR_TB`
    means left-to-right, then top-to-bottom.
    """
    LR_TB = "lr-tb"
    LR_BT = "lr-bt"
    RL_TB = "rl-tb"
    RL_BT = "rl-bt"
    TB_LR = "tb-lr"
    TB_RL = "tb-rl"
    BT_LR = "bt-lr"
    BT_RL = "bt-rl"


class _RepositionProperty:
    def __set_name__(self, owner, name):
        self.name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return getattr(instance, self.name)

    def __set__(self, instance, value):
        if self.name == "_orientation":
            value = Orientation(value)

        setattr(instance, self.name, value)
        instance._reposition_children()


class GridLayout(Widget):
    """
    A widget that automatically positions children into a grid.

    Notes
    -----
    Re-ordering children (such as through `pull_to_front`) and calling `_reposition_children`
    will change the positions of the children in the grid.

    The read-only attribute `minimum_grid_size` is the minimum size the grid must be to show all
    children. This can be used to set the size of the grid layout, e.g.,
    ``my_grid.size = my_grid.minimum_grid_size``.

    Parameters
    ----------
    grid_rows : int, default: 1
        Number of rows.
    grid_columns : int, default: 1
        Number of columns.
    orientation : Orientation, default: Orientation.LR_BT
        The orientation of the grid. Describes how the grid fills as children are added. The
        default is left-to-right then top-to-bottom.
    left_padding : int, default: 0
        Padding on left side of grid.
    right_padding : int, default: 0
        Padding on right side of grid.
    top_padding : int, default: 0
        Padding at the top of grid.
    bottom_padding : int, default: 0
        Padding at the bottom of grid.
    horizontal_spacing : int, default: 0
        Horizontal spacing between children.
    vertical_spacing : int, default: 0
        Vertical spacing between children.

    Attributes
    ----------
    grid_rows : int
        Number of rows.
    grid_columns : int
        Number of columns.
    orientation : Orientation
        The orientation of the grid.
    left_padding : int
        Padding on left side of grid.
    right_padding : int
        Padding on right side of grid.
    top_padding : int
        Padding at the top of grid.
    bottom_padding : int
        Padding at the bottom of grid.
    horizontal_spacing : int
        Horizontal spacing between children.
    vertical_spacing : int
        Vertical spacing between children.

    Raises
    ------
    ValueError
        If grid is full and `add_widget` is called.
    """
    grid_rows: int = _RepositionProperty()

    grid_columns: int = _RepositionProperty()

    orientation: Orientation = _RepositionProperty()

    left_padding: int = _RepositionProperty()

    right_padding: int = _RepositionProperty()

    top_padding: int = _RepositionProperty()

    bottom_padding: int = _RepositionProperty()

    horizontal_spacing: int = _RepositionProperty()

    vertical_spacing: int = _RepositionProperty()

    def __init__(
        self,
        grid_rows: int=1,
        grid_columns: int=1,
        *,
        orientation: Orientation=Orientation.LR_BT,
        left_padding: int=0,
        right_padding: int=0,
        top_padding: int=0,
        bottom_padding: int=0,
        horizontal_spacing: int=0,
        vertical_spacing: int=0,
        **kwargs
    ):
        self._grid_rows = grid_rows
        self._grid_columns = grid_columns
        self._orientation = orientation
        self._left_padding = left_padding
        self._right_padding = right_padding
        self._top_padding = top_padding
        self._bottom_padding = bottom_padding
        self._horizontal_spacing = horizontal_spacing
        self._vertical_spacing = vertical_spacing
        self._minimum_grid_size = Size(0, 0)

        super().__init__(**kwargs)

    def _index_at(self, row: int, col: int) -> int:
        """
        Return the index of the child at a given row and column in the grid.
        """
        rows = self.grid_rows
        cols = self.grid_columns

        match self.orientation:
            case Orientation.LR_TB:
                return col + row * cols
            case Orientation.LR_BT:
                return col + (rows - row - 1) * cols
            case Orientation.RL_TB:
                return (cols - col - 1) + row * cols
            case Orientation.RL_BT:
                return (cols - col - 1) + (rows - row - 1) * cols
            case Orientation.TB_LR:
                return row + col * rows
            case Orientation.TB_RL:
                return row + (cols - col - 1) * rows
            case Orientation.BT_LR:
                return (rows - row - 1) + col * rows
            case Orientation.BT_RL:
                return (rows - row - 1) + (cols - col - 1) * rows

    def _row_height(self, i: int) -> int:
        """
        Height of row `i`.
        """
        return max(
            (
                self.children[index].height
                for col in range(self.grid_columns)
                if (index := self._index_at(i, col)) < len(self.children)
            ),
            default=0,
        )

    def _col_width(self, i: int) -> int:
        """
        Width of column `i`.
        """
        return max(
            (
                self.children[index].width
                for row in range(self.grid_rows)
                if (index := self._index_at(row, i)) < len(self.children)
            ),
            default=0,
        )

    @property
    def minimum_grid_size(self) -> Size:
        """
        Return the minimum grid size to show all children.
        """
        return self._minimum_grid_size

    def _reposition_children(self):
        rows, cols = self.grid_rows, self.grid_columns

        lp = self.left_padding
        rp = self.right_padding
        tp = self.top_padding
        bp = self.bottom_padding
        vs = self.vertical_spacing
        hs = self.horizontal_spacing

        children = self.children
        index_at = self._index_at

        row_height = self._row_height
        col_width = self._col_width

        row_tops = tuple(accumulate(
            tp if i == 0 else row_height(i - 1) + vs for i in range(rows)
        ))
        col_lefts = tuple(accumulate(
            lp if i == 0 else col_width(i - 1) + hs for i in range(cols)
        ))

        for row, col in product(range(rows), range(cols)):
            if (i := index_at(row, col)) < len(self.children):
                children[i].pos = row_tops[row], col_lefts[col]

        self._minimum_grid_size = Size(
            row_tops[-1] + row_height(rows - 1) + bp,
            col_lefts[-1] + col_width(cols - 1) + rp,
        )

    def add_widget(self, widget):
        if len(self.children) >= self.grid_rows * self.grid_columns:
            raise ValueError("too many children, grid is full")

        super().add_widget(widget)

        self._reposition_children()

    def remove_widget(self, widget):
        super().remove_widget(widget)
        self._reposition_children()
