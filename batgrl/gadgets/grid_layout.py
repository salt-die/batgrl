"""A grid layout gadget."""
from itertools import accumulate, product
from typing import Literal

from numpy.typing import NDArray

from ..colors import ColorPair
from .gadget import (
    Char,
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)

__all__ = [
    "GridLayout",
    "Orientation",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]

Orientation = Literal[
    "lr-tb",
    "lr-bt",
    "rl-tb",
    "rl-bt",
    "tb-lr",
    "tb-rl",
    "bt-lr",
    "bt-rl",
]
"""
Orientation of the grid.

Describes how the grid fills as children are added. As an example, the orientation
"lr-tb" means left-to-right, then top-to-bottom.
"""


class _RepositionProperty:
    def __set_name__(self, owner, name):
        self.name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return getattr(instance, self.name)

    def __set__(self, instance, value):
        setattr(instance, self.name, value)
        instance._reposition_children()


class GridLayout(Gadget):
    r"""
    A gadget that automatically positions children into a grid.

    Parameters
    ----------
    grid_rows : int, default: 1
        Number of rows.
    grid_columns : int, default: 1
        Number of columns.
    orientation : Orientation, default: "lr-tb"
        The orientation of the grid.
    padding_left : int, default: 0
        Padding on left side of grid.
    padding_right : int, default: 0
        Padding on right side of grid.
    padding_top : int, default: 0
        Padding at the top of grid.
    padding_bottom : int, default: 0
        Padding at the bottom of grid.
    horizontal_spacing : int, default: 0
        Horizontal spacing between children.
    vertical_spacing : int, default: 0
        Vertical spacing between children.
    background_char : NDArray[Char] | str | None, default: None
        The background character of the gadget. If not given and not transparent, the
        background characters of the root gadget are painted. If not given and
        transparent, characters behind the gadget are visible. The character must be
        single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the gadget. If not given and not transparent, the
        background color pair of the root gadget is painted. If not given and
        transparent, the color pairs behind the gadget are visible.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        A transparent gadget allows regions beneath it to be painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    minimum_grid_size : Size
        Minimum grid size needed to show all children.
    grid_rows : int
        Number of rows.
    grid_columns : int
        Number of columns.
    orientation : Orientation
        The orientation of the grid.
    padding_left : int
        Padding on left side of grid.
    padding_right : int
        Padding on right side of grid.
    padding_top : int
        Padding at the top of grid.
    padding_bottom : int
        Padding at the bottom of grid.
    horizontal_spacing : int
        Horizontal spacing between children.
    vertical_spacing : int
        Vertical spacing between children.
    background_char : NDArray[Char] | None
        The background character of the gadget.
    background_color_pair : ColorPair | None
        The background color pair of the gadget.
    size : Size
        Size of gadget.
    height : int
        Height of gadget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of gadget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of gadget.
    y : int
        Y-coordinate of top of gadget.
    left : int
        X-coordinate of left side of gadget.
    x : int
        X-coordinate of left side of gadget.
    bottom : int
        Y-coordinate of bottom of gadget.
    right : int
        X-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    parent: GadgetBase | None
        Parent gadget.
    children : list[GadgetBase]
        Children gadgets.
    is_transparent : bool
        True if gadget is transparent.
    is_visible : bool
        True if gadget is visible.
    is_enabled : bool
        True if gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    index_at(row, col):
        Return index of the child gadget in :attr:`children` at position `row, col` in
        the grid.
    on_size():
        Update gadget after a resize.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        Return true if point collides with visible portion of gadget.
    collides_gadget(other):
        Return true if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\*gadgets):
        Add multiple child gadgets.
    remove_gadget(gadget):
        Remove a child gadget.
    pull_to_front():
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root():
        Yield all descendents of the root gadget (preorder traversal).
    walk():
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse():
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors():
        Yield all ancestors of this gadget.
    subscribe(source, attr, action):
        Subscribe to a gadget property.
    unsubscribe(source, attr):
        Unsubscribe to a gadget property.
    on_key(key_event):
        Handle key press event.
    on_mouse(mouse_event):
        Handle mouse event.
    on_paste(paste_event):
        Handle paste event.
    tween(...):
        Sequentially update gadget properties over time.
    on_add():
        Apply size hints and call children's `on_add`.
    on_remove():
        Call children's `on_remove`.
    prolicide():
        Recursively remove all children.
    destroy():
        Remove this gadget and recursively remove all its children.

    Notes
    -----
    Grid layouts remove size and pos hints from their children.

    Re-ordering children (such as through :meth:`pull_to_front`) and calling
    :meth:`_reposition_children` will change the positions of the children in the grid.

    The read-only attribute :attr:`minimum_grid_size` is the minimum size the grid must
    be to show all children. This can be used to set the size of the grid layout, e.g.,
    ``my_grid.size = my_grid.minimum_grid_size``.
    """

    grid_rows: int = _RepositionProperty()

    grid_columns: int = _RepositionProperty()

    padding_left: int = _RepositionProperty()

    padding_right: int = _RepositionProperty()

    padding_top: int = _RepositionProperty()

    padding_bottom: int = _RepositionProperty()

    horizontal_spacing: int = _RepositionProperty()

    vertical_spacing: int = _RepositionProperty()

    def __init__(
        self,
        *,
        grid_rows: int = 1,
        grid_columns: int = 1,
        orientation: Orientation = "lr-tb",
        padding_left: int = 0,
        padding_right: int = 0,
        padding_top: int = 0,
        padding_bottom: int = 0,
        horizontal_spacing: int = 0,
        vertical_spacing: int = 0,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: NDArray[Char] | str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        self._grid_rows = grid_rows
        self._grid_columns = grid_columns
        self._orientation = orientation
        self._padding_left = padding_left
        self._padding_right = padding_right
        self._padding_top = padding_top
        self._padding_bottom = padding_bottom
        self._horizontal_spacing = horizontal_spacing
        self._vertical_spacing = vertical_spacing
        self._minimum_grid_size = Size(0, 0)

        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

    @property
    def orientation(self) -> Orientation:
        """
        The orientation of the grid.

        Describes how the grid fills as children are added. The default is left-to-right
        then top-to-bottom.
        """
        return self._orientation

    @orientation.setter
    def orientation(self, orientation: Orientation):
        if self._orientation not in Orientation.__args__:
            raise TypeError(f"{orientation} is not a valid orientation.")
        self._orientation = orientation
        self._reposition_children()

    def on_size(self):
        """Repositon children on resize."""
        self._reposition_children()

    def index_at(self, row: int, col: int) -> int:
        """
        Return the index of the child gadget in :attr:`children` at a given row and
        column in the grid.

        Parameters
        ----------
        row : int
            The row of the child.
        col : int
            The column of the child.

        Returns
        -------
        int
            Index of the child in :attr:`children`.
        """
        rows = self.grid_rows
        cols = self.grid_columns

        match self.orientation:
            case "lr-tb":
                return col + row * cols
            case "lr-bt":
                return col + (rows - row - 1) * cols
            case "rl-tb":
                return (cols - col - 1) + row * cols
            case "rl-bt":
                return (cols - col - 1) + (rows - row - 1) * cols
            case "tb-lr":
                return row + col * rows
            case "tb-rl":
                return row + (cols - col - 1) * rows
            case "bt-lr":
                return (rows - row - 1) + col * rows
            case "bt-rl":
                return (rows - row - 1) + (cols - col - 1) * rows

    def _row_height(self, i: int) -> int:
        """Height of row `i`."""
        return max(
            (
                self.children[index].height
                for col in range(self.grid_columns)
                if (index := self.index_at(i, col)) < len(self.children)
            ),
            default=0,
        )

    def _col_width(self, i: int) -> int:
        """Width of column `i`."""
        return max(
            (
                self.children[index].width
                for row in range(self.grid_rows)
                if (index := self.index_at(row, i)) < len(self.children)
            ),
            default=0,
        )

    @property
    def minimum_grid_size(self) -> Size:
        """Return the minimum grid size to show all children."""
        nrows, ncols = self.grid_rows, self.grid_columns
        if nrows == 0 or ncols == 0:
            return Size(0, 0)

        bottom = (
            self.padding_top
            + sum(self._row_height(i) for i in range(nrows))
            + self.vertical_spacing * (nrows - 1)
            + self.padding_bottom
        )
        right = (
            self.padding_left
            + sum(self._col_width(i) for i in range(ncols))
            + self.horizontal_spacing * (ncols - 1)
            + self.padding_right
        )

        return Size(bottom, right)

    def _reposition_children(self):
        if self.grid_rows == 0 or self.grid_columns == 0:
            return

        row_tops = tuple(
            accumulate(
                self.padding_top
                if i == 0
                else self._row_height(i - 1) + self.vertical_spacing
                for i in range(self.grid_rows)
            )
        )
        col_lefts = tuple(
            accumulate(
                self.padding_left
                if i == 0
                else self._col_width(i - 1) + self.horizontal_spacing
                for i in range(self.grid_columns)
            )
        )

        for row, col in product(range(self.grid_rows), range(self.grid_columns)):
            if (i := self.index_at(row, col)) < len(self.children):
                self.children[i].pos = row_tops[row], col_lefts[col]

    def add_gadget(self, gadget):
        """Check to see if grid is full before adding gadget and remove its hints."""
        if len(self.children) >= self.grid_rows * self.grid_columns:
            raise ValueError("too many children, grid is full")

        gadget.size_hint = {}
        gadget.pos_hint = {}
        super().add_gadget(gadget)

        self._reposition_children()

    def remove_gadget(self, gadget):
        """Reposition children when a gadget is removed."""
        super().remove_gadget(gadget)
        self._reposition_children()
