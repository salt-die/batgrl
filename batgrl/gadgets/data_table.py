"""A data table gadget."""
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from itertools import count, islice
from typing import Literal, Protocol, TypeVar

from wcwidth import wcswidth

from ..io import MouseEvent
from .behaviors.button_behavior import ButtonBehavior
from .behaviors.themable import Themable
from .gadget_base import (
    GadgetBase,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)
from .grid_layout import GridLayout
from .scroll_view import ScrollView
from .text import Text, add_text

__all__ = [
    "ColumnStyle",
    "DataTable",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]


class SupportsLessThan(Protocol):
    """Supports the less than (`<`) operator."""

    def __lt__(self, other) -> bool:
        ...


T = TypeVar("T", bound=SupportsLessThan)


@dataclass
class ColumnStyle:
    """
    Style of a column in a data table. Includes how data is rendered,
    alignment, padding, and minimum width.

    Parameters
    ----------
    render : Callable[[T], str] | None, default: None
        A callable that renders column data into a string. Uses the
        built-in `str` by default.
    alignment : Literal["center", "left", "right"], default: "left"
        Alignment of the column.
    padding : int, default: 1
        Left and right padding of column.
    min_width : int, default: 0
        Minimum width of column.
    allow_sorting : bool, default: True
        Whether sorting is allowed for column.

    Attributes
    ----------
    render : Callable[[T], str]
        A callable that renders column data into a string.
    alignment : Literal["center", "left", "right"]
        Alignment of the column.
    padding : int
        Left and right padding of column.
    min_width : int
        Minimum width of column.
    allow_sorting : bool
        Whether sorting is allowed for column.
    """

    render: Callable[[T], str] | None = None
    """
    A callable that renders column data into a string. Uses the built-in `str` by
    default.
    """
    alignment: Literal["center", "left", "right"] = "left"
    """
    Alignment of the column.
    """
    padding: int = 1
    """
    Left and right padding of column.
    """
    min_width: int = 0
    """
    Minimum width of column.
    """
    allow_sorting: bool = True
    """
    Whether sorting is allowed for column.
    """

    def __post_init__(self):
        if self.render is None:
            self.render = str


class _SortState(str, Enum):
    """Sorted state of a column in a data table."""

    NOT_SORTED = "↕"
    ASCENDING = "↑"
    DESCENDING = "↓"


_SORT_INDICATOR_SPACING = 1
"""Spaces between column label text and sort indicator."""
_SORT_INDICATOR_WIDTH = wcswidth(_SortState.NOT_SORTED.value)
"""Character width of sort indicator. (Indicator values should be same width.)"""
_ALIGN_FORMATTER = {
    "center": "^",
    "left": "<",
    "right": ">",
}
"""Convert an alignment to f-string format specification."""


class _CellBase(ButtonBehavior, Text):
    """Base for cells in a data table."""

    def __init__(self, data_table: "DataTable", column_id: int, **kwargs):
        super().__init__(**kwargs)
        self.data_table = data_table
        self.column_id = column_id
        """Column id to which this cell belongs."""

    @property
    def style(self) -> ColumnStyle:
        """Style of column to which this cell belongs."""
        return self.data_table._column_styles[self.column_id]


class _ColumnLabel(_CellBase):
    """A column label cell in a data table."""

    def __init__(self, label: str, allow_sorting: bool, **kwargs):
        super().__init__(**kwargs)

        self._sort_state = _SortState.NOT_SORTED
        self.label = label
        """Display text of cell."""
        self.allow_sorting = allow_sorting

        lines = label.split("\n")

        self.cell_min_height = len(lines)
        """Minimum allowed height of cells."""
        self.cell_min_width = max(
            (
                max(wcswidth(line) for line in lines)
                + _SORT_INDICATOR_SPACING  # label width
                + _SORT_INDICATOR_WIDTH
                + 2 * self.style.padding
            ),
            self.style.min_width,
        )
        """Minimum allowed width of cell."""

    @property
    def indicator_pos(self) -> Point:
        return Point(
            self.height // 2, self.width - _SORT_INDICATOR_WIDTH - self.style.padding
        )

    @property
    def sort_state(self) -> _SortState:
        """Sorted state of column of which this label belongs."""
        return self._sort_state

    @sort_state.setter
    def sort_state(self, sort_state: _SortState):
        self._sort_state = _SortState(sort_state)
        if self.allow_sorting:
            self.canvas["char"][self.indicator_pos] = self._sort_state.value

    @property
    def allow_sorting(self) -> bool:
        return self._allow_sorting

    @allow_sorting.setter
    def allow_sorting(self, allow_sorting: bool):
        self._allow_sorting = allow_sorting and self.style.allow_sorting
        if allow_sorting:
            self.colors[
                self.indicator_pos
            ] = self.data_table.color_theme.data_table_sort_indicator
            self.canvas["char"][self.indicator_pos] = self._sort_state.value
        else:
            self.colors[self.indicator_pos] = self.data_table.color_theme.primary
            self.canvas["char"][self.indicator_pos] = " "

    def on_size(self):
        super().on_size()

        self.canvas["char"] = " "
        self.colors[:] = self.data_table.color_theme.primary

        align = _ALIGN_FORMATTER[self.style.alignment]
        padding = self.style.padding
        content_width = (
            self.width - 2 * padding - _SORT_INDICATOR_WIDTH - _SORT_INDICATOR_SPACING
        )
        content = "\n".join(
            f"{line:{align}{content_width}}{' ' * _SORT_INDICATOR_SPACING}"
            for line in self.label.split("\n")
        )
        add_text(self.canvas[:, padding : -_SORT_INDICATOR_WIDTH - padding], content)

        if self.allow_sorting:
            self.colors[
                self.indicator_pos
            ] = self.data_table.color_theme.data_table_sort_indicator
            self.canvas["char"][self.indicator_pos] = self._sort_state.value

    def update_hover(self):
        self.data_table._update_hover()

    def on_release(self):
        if not self.allow_sorting:
            return True

        if self.sort_state is _SortState.ASCENDING:
            self.sort_state = _SortState.DESCENDING
        else:
            self.sort_state = _SortState.ASCENDING

        column_label: _ColumnLabel
        for column_label in self.data_table._column_labels.children:
            if column_label is not self:
                column_label.sort_state = _SortState.NOT_SORTED

        self.data_table._sort(self.column_id, self.sort_state)
        return True


class _DataCell(_CellBase):
    """A data cell in a data table."""

    def __init__(self, data: T, row_id: int, striped: bool = False, **kwargs):
        super().__init__(**kwargs)

        self.data = data
        """Data of cell."""

        lines = self.style.render(data).split("\n")

        self.cell_min_height = len(lines)
        """Minimum allowed height of cell."""
        self.cell_min_width = max(
            (
                max(wcswidth(line) for line in lines)
                + 2 * self.style.padding  # width of rendered data
            ),
            self.style.min_width,
        )
        """Minimum allowed width of cell."""
        self.row_id = row_id
        """Row id of row cell belongs to."""
        self.striped = striped
        """Whether cell is striped."""
        self.selected = False
        """Whether cell is selected."""

    def on_size(self):
        super().on_size()

        self.canvas["char"] = " "
        if self.striped:
            self.colors[:] = self.data_table.color_theme.data_table_stripe
        elif self.selected:
            self.colors[:] = self.data_table.color_theme.data_table_selected
        else:
            self.colors[:] = self.data_table.color_theme.primary

        align = _ALIGN_FORMATTER[self.style.alignment]
        padding = self.style.padding
        content_width = self.width - 2 * padding
        content = "\n".join(
            f"{line:{align}{content_width}}"
            for line in self.style.render(self.data).split("\n")
        )
        add_text(self.canvas[:, padding : self.width - padding], content)

    def update_hover(self):
        self.data_table._update_hover(self.column_id, self.row_id)

    def on_release(self):
        self.data_table._on_release()
        return True


class DataTable(Themable, GadgetBase):
    r"""
    A data table gadget.

    Parameters
    ----------
    data : dict[str, Sequence[T]] | None=None, default: None
        If given, construct a data table from this data. To gain more
        control over column styling use :meth:`add_column`.
    default_style : ColumnStyle | None, default: None
        Default style for new columns.
    select_items : Literal["cell", "row", "column"], default: "row"
        Determines which items are selected when data table is clicked.
    zebra_stripes : bool, default: True
        Whether alternate rows are colored differently.
    allow_sorting : bool, default: True
        Whether columns can be sorted.
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
    default_style : ColumnStyle
        Default style for new columns.
    select_items : Literal["cell", "row", "column"]
        Which items are selected when data table is clicked.
    zebra_stripes : bool
        Whether alternate rows are colored differently.
    allow_sorting : bool
        Whether columns can be sorted.
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
    add_column(label, ...):
        Add a column to the data table.
    add_row(data):
        Add a row to the data table.
    remove_column(column_id):
        Remove a column by column id.
    remove_row(row_id):
        Remove a row by row id.
    row_id_from_index(index):
        Returns the row id of the row at index.
    column_id_from_index(index):
        Returns the column id of the column at index.
    update_theme():
        Paint the gadget with current theme.
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
    """

    _IDS = count()

    def __init__(
        self,
        *,
        data: dict[str, Sequence[T]] | None = None,
        default_style: ColumnStyle | None = None,
        select_items: Literal["cell", "row", "column"] = "row",
        zebra_stripes: bool = True,
        allow_sorting: bool = True,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self._column_ids: list[int] = []
        """Column ids. Index of id corresponds to index of column in table."""
        self._column_styles: dict[int, ColumnStyle] = {}
        """Column id to column style."""
        self._column_labels = GridLayout(
            grid_rows=1, grid_columns=0, orientation="lr-tb"
        )
        """Grid layout containing column label cells."""
        self._rows: dict[int, GridLayout] = {}
        """Row id to grid layout for row."""
        self._hover_column_id = -1
        """Column id of column that mouse is hovering or -1 if no columns are
        hovered.
        """
        self._hover_row_id = -1
        """Row id of row that mouse is hovering or -1 if no columns are hovered."""
        self._table = GridLayout(grid_rows=1, grid_columns=1, orientation="tb-lr")
        """Grid layout of column label and row grid layouts."""
        self._table.add_gadget(self._column_labels)

        self.default_style = default_style or ColumnStyle()
        """Default style for new columns."""
        self._select_items = select_items
        """Determines which items are selected when data table is clicked."""
        self._zebra_stripes = zebra_stripes
        """Whether alternate rows are colored differently."""
        self._allow_sorting = allow_sorting
        """Whether columns can be sorted."""

        self._scroll_view = ScrollView(
            size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        self._scroll_view.view = self._table
        self.add_gadget(self._scroll_view)

        def update_bars():
            self._scroll_view.show_horizontal_bar = (
                self._table.width > self._scroll_view.port_width
            )
            self._scroll_view.show_vertical_bar = (
                self._table.height > self._scroll_view.port_height
            )

        self.subscribe(self._table, "size", update_bars)

        if data is not None:
            for label, column_data in data.items():
                self.add_column(label, data=column_data)

    @property
    def select_items(self) -> Literal["cell", "row", "column"]:
        """Determines which items are selected when data table is clicked."""
        return self._select_items

    @select_items.setter
    def select_items(self, select_items: Literal["cell", "row", "column"]):
        select_items = select_items
        self._select_items = select_items
        for row in self._iter_rows():
            for cell in row.children:
                cell.selected = False
        self._repaint_cells()

    @property
    def zebra_stripes(self) -> bool:
        """Whether alternate rows are colored differently."""
        return self._zebra_stripes

    @zebra_stripes.setter
    def zebra_stripes(self, zebra_stripes: bool):
        self._zebra_stripes = zebra_stripes
        self._repaint_cells()

    @property
    def allow_sorting(self) -> bool:
        """Whether columns can be sorted."""
        return self._allow_sorting

    @allow_sorting.setter
    def allow_sorting(self, allow_sorting: bool):
        self._allow_sorting = allow_sorting
        for column_label in self._column_labels.children:
            column_label.allow_sorting = allow_sorting

    def update_theme(self):
        """Paint the gadget with current theme."""
        primary = self.color_theme.primary
        self.background_color_pair = primary
        self._table.background_color_pair = primary

        label: _ColumnLabel
        for label in self._column_labels.children:
            label.default_color_pair = primary
            label.colors[:] = primary
            label.colors[
                label.indicator_pos
            ] = self.color_theme.data_table_sort_indicator

        cell: _DataCell
        for row in self._rows.values():
            row.background_color_pair = primary
            for cell in row.children:
                self._paint_cell_normal(cell)
        self._update_hover(self._hover_column_id, self._hover_row_id)

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        """Highlight row on mouse collision."""
        y, x = self.to_local(mouse_event.position)
        if not (
            0 <= y < self._scroll_view.port_height
            and 0 <= x < self._scroll_view.port_width
        ):
            self._update_hover()
        return super().on_mouse(mouse_event)

    def _paint_cell_hover(self, cell: _DataCell):
        if cell.selected:
            cell.colors[:] = self.color_theme.data_table_selected_hover
        elif cell.striped:
            cell.colors[:] = self.color_theme.data_table_stripe_hover
        else:
            cell.colors[:] = self.color_theme.data_table_hover

    def _paint_cell_normal(self, cell: _DataCell):
        if cell.selected:
            cell.colors[:] = self.color_theme.data_table_selected
        elif cell.striped:
            cell.colors[:] = self.color_theme.data_table_stripe
        else:
            cell.colors[:] = self.color_theme.primary

    def _repaint_cells(self):
        for row in self._iter_rows():
            for i, cell in enumerate(row.children):
                cell.striped = self.zebra_stripes and i % 2 == 1
                self._paint_cell_normal(cell)

        column_id = self._hover_column_id
        row_id = self._hover_row_id
        self._hover_column_id = -1
        self._hover_row_id = -1
        self._update_hover(column_id, row_id)

    def _update_hover(self, column_id: int = -1, row_id: int = -1):
        cell: _DataCell

        match self.select_items:
            case "row":
                if self._hover_row_id != row_id:
                    if self._hover_row_id != -1:
                        for cell in self._rows[self._hover_row_id].children:
                            self._paint_cell_normal(cell)
                    if row_id != -1:
                        for cell in self._rows[row_id].children:
                            self._paint_cell_hover(cell)
            case "column":
                if self._hover_column_id != column_id:
                    if self._hover_column_id != -1:
                        old_column_index = self._column_ids.index(self._hover_column_id)
                        for row in self._rows.values():
                            self._paint_cell_normal(row.children[old_column_index])
                    if column_id != -1:
                        new_column_index = self._column_ids.index(column_id)
                        for row in self._rows.values():
                            self._paint_cell_hover(row.children[new_column_index])
            case "cell":
                if self._hover_column_id != column_id or self._hover_row_id != row_id:
                    if self._hover_column_id != -1 and self._hover_row_id != -1:
                        old_column_index = self._column_ids.index(self._hover_column_id)
                        self._paint_cell_normal(
                            self._rows[self._hover_row_id].children[old_column_index]
                        )
                    if column_id != -1 and row_id != -1:
                        new_column_index = self._column_ids.index(column_id)
                        self._paint_cell_hover(
                            self._rows[row_id].children[new_column_index]
                        )

        self._hover_row_id = row_id
        self._hover_column_id = column_id

    def _on_release(self):
        cell: _DataCell

        match self.select_items:
            case "row":
                for cell in self._rows[self._hover_row_id].children:
                    cell.selected = not cell.selected
                    self._paint_cell_hover(cell)
            case "column":
                column_index = self._column_ids.index(self._hover_column_id)
                for row in self._rows.values():
                    cell = row.children[column_index]
                    cell.selected = not cell.selected
                    self._paint_cell_hover(cell)
            case "cell":
                column_index = self._column_ids.index(self._hover_column_id)
                cell = self._rows[self._hover_row_id].children[column_index]
                cell.selected = not cell.selected
                self._paint_cell_hover(cell)

    def _sort(self, column_id: int, sort_state: _SortState):
        column_index = self._column_ids.index(column_id)
        sorted_rows = sorted(
            self._iter_rows(),
            key=lambda row: row.children[column_index].data,
            reverse=sort_state is _SortState.DESCENDING,
        )
        self._table.children = [self._table.children[0], *sorted_rows]
        self._table._reposition_children()

    def _fix_sizes(self):
        row_heights = [
            max(cell.cell_min_height for cell in row.children)
            for row in self._table.children
        ]
        column_widths = [
            max(row.children[i].cell_min_width for row in self._table.children)
            for i in range(len(self._column_ids))
        ]
        row: GridLayout
        cell: _CellBase
        for row, row_height in zip(self._table.children, row_heights):
            for cell, column_width in zip(row.children, column_widths):
                cell.size = row_height, column_width
            row.size = row.minimum_grid_size
        self._table.size = self._table.minimum_grid_size

        # Remove hovered rows/columns:
        self._hover_column_id = -1
        self._hover_row_id = -1
        self._repaint_cells()

    def _iter_rows(self):
        return islice(self._table.children, 1, None)

    def add_column(
        self,
        label: str,
        data: Sequence[T] | None = None,
        style: ColumnStyle | None = None,
    ) -> int:
        """
        Add a column to the data table.

        If this is the first column added to the table, a row will be added for each
        item in `data`. Otherwise, the number of items in data must be equal to the
        number of rows in the table.

        Parameters
        ----------
        label : str
            The column label.
        data : Sequence[T] | None, default: None
            Column data.
        style : ColumnStyle | None, default: None
            Column style. Uses :attr:`default_style` by default.

        Returns
        -------
        int
            Column id. This id can be used to remove the column.
        """
        if data is None:
            data = []
        if self._column_ids and len(data) != len(self._rows):
            raise ValueError(
                "Number of items in column data inconsistent with number of rows."
            )
        if style is None:
            style = replace(self.default_style)

        column_id = next(self._IDS)
        self._column_ids.append(column_id)
        self._column_styles[column_id] = style

        column_label = _ColumnLabel(
            data_table=self,
            column_id=column_id,
            label=label,
            allow_sorting=self.allow_sorting and style.allow_sorting,
        )
        self._column_labels.grid_columns += 1
        self._column_labels.add_gadget(column_label)

        if len(self._column_ids) == 1:
            self._table.grid_rows += len(data)
            for item in data:
                row_id = next(self._IDS)
                row = GridLayout(grid_rows=1, grid_columns=1, orientation="lr-bt")
                row.add_gadget(
                    _DataCell(
                        data_table=self, column_id=column_id, data=item, row_id=row_id
                    )
                )
                self._rows[row_id] = row
                self._table.add_gadget(row)
        else:
            for item, row in zip(data, self._iter_rows()):
                row_id = row.children[0].row_id
                row.grid_columns += 1
                row.add_gadget(
                    _DataCell(
                        data_table=self, column_id=column_id, data=item, row_id=row_id
                    )
                )

        self._fix_sizes()
        return column_id

    def add_row(self, data: Sequence[SupportsLessThan]) -> int:
        """
        Add a row to the data table.

        There must be at least one column before a row can be added. The number
        of items in the row must match the number of columns.

        Parameters
        ----------
        data : Sequence[SupportsLessThan]
            The row data.

        Returns
        -------
        int
            Row id. This id can be used to remove the row.
        """
        if not self._column_ids or len(data) != len(self._column_ids):
            raise ValueError(
                "Number of items in row data inconsistent with number of columns."
            )

        row_id = next(self._IDS)
        row_layout = GridLayout(
            grid_rows=1, grid_columns=len(data), orientation="lr-bt"
        )
        row_layout.add_gadgets(
            _DataCell(data_table=self, column_id=column_id, data=item, row_id=row_id)
            for column_id, item in zip(self._column_ids, data)
        )
        self._rows[row_id] = row_layout
        self._table.grid_rows += 1
        self._table.add_gadget(row_layout)
        self._fix_sizes()
        return row_id

    def remove_column(self, column_id: int):
        """
        Remove a column by column id.

        Column id can be retrieved by index with :meth:`column_id_from_index`.

        Parameters
        ----------
        column_id : int
            The id of the column to remove.
        """
        column_index = self._column_ids.index(column_id)
        del self._column_ids[column_index]
        for row in self._table.children:
            row.remove_gadget(row.children[column_index])
            row.grid_columns -= 1
        self._fix_sizes()

    def remove_row(self, row_id: int):
        """
        Remove a row by row id.

        Row id can be retrieved by index with :meth:`row_id_from_index`.

        Parameters
        ----------
        row_id : int
            The id of the row to remove.
        """
        row = self._rows.pop(row_id)
        self._table.remove_gadget(row)
        self._table.grid_rows -= 1
        self._fix_sizes()

    def row_id_from_index(self, index: int) -> int:
        """
        Return the row id of the row at index.

        Parameters
        ----------
        index : int
            Index of row in table.

        Returns
        -------
        int
            Row id of the row tat index.
        """
        return self._table.children[index + 1].children[0].row_id

    def column_id_from_index(self, index: int) -> int:
        """
        Return the column id of the column at index.

        Parameters
        ----------
        index : int
            Index of column in table.

        Returns
        -------
        int
            Column id of the column at index.
        """
        return self._column_labels.children[index].column_id
