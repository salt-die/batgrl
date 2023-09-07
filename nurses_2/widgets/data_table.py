"""
A data table widget.
"""
from enum import Enum
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, replace
from itertools import count
from typing import Protocol, TypeVar

from wcwidth import wcswidth

from ..io import MouseEvent
from .behaviors.button_behavior import ButtonBehavior
from .behaviors.themable import Themable
from .grid_layout import GridLayout, Orientation
from .scroll_view import ScrollView
from .text_widget import TextWidget, Point
from .text_widget_data_structures import add_text

__all__ = "SelectItems", "Alignment", " ColumnStyle", "DataTable"


class SelectItems(str, Enum):
    """
    Determines whether rows, columns or cells are selected in a data table.
    """
    CELL = "cell"
    ROW = "row"
    COLUMN = "column"


class Alignment(str, Enum):
    """
    Alignments of a column in a data table.
    """
    CENTER = "center"
    LEFT = "left"
    RIGHT = "right"


class SupportsLessThan(Protocol):
    """
    Supports the less than (`<`) operator.
    """
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
    alignment : Alignment, default: Alignment.LEFT
        Alignment of the column. One of `"left"`, `"right"`, `"center"`.
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
    alignment : Alignment
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
    A callable that renders column data into a string. Uses the built-in `str` by default.
    """
    alignment: Alignment = Alignment.LEFT
    """
    Alignment of the column. One of `"left"`, `"right"`, `"center"`.
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
    """
    Sorted state of a column in a data table.
    """
    NOT_SORTED = "↕"
    ASCENDING = "↑"
    DESCENDING = "↓"


_SORT_INDICATOR_SPACING = 1
"""Spaces between column label text and sort indicator."""
_SORT_INDICATOR_WIDTH = wcswidth(_SortState.NOT_SORTED.value)
"""Character width of sort indicator. (Indicator values should be same width.)"""
_ALIGN_FORMATTER = {Alignment.CENTER: "^", Alignment.LEFT: "<", Alignment.RIGHT: ">"}
"""Convert an alignment to f-string format specification."""


class _CellBase(ButtonBehavior, TextWidget):
    """
    Base for cells in a data table.
    """
    def __init__(self, data_table: "DataTable", column_id: int, **kwargs):
        super().__init__(**kwargs)
        self.data_table = data_table
        self.column_id = column_id
        """Column id to which this cell belongs."""

    @property
    def style(self) -> ColumnStyle:
        """
        Style of column to which this cell belongs.
        """
        return self.data_table._column_styles[self.column_id]


class _ColumnLabel(_CellBase):
    """
    A column label cell in a data table.
    """
    def __init__(self, label: str, allow_sorting: bool, **kwargs):
        super().__init__(**kwargs)

        self._sort_state = _SortState.NOT_SORTED
        self.label = label
        """Display text of cell."""
        self.allow_sorting = allow_sorting

        lines = label.splitlines()

        self.cell_min_height = len(lines)
        """Minimum allowed height of cells."""
        self.cell_min_width = max(
            (
                max(wcswidth(line) for line in lines) +  # label width
                _SORT_INDICATOR_SPACING +
                _SORT_INDICATOR_WIDTH +
                2 * self.style.padding
            ),
            self.style.min_width,
        )
        """Minimum allowed width of cell."""

    @property
    def indicator_pos(self) -> Point:
        return Point(self.height // 2, self.width - _SORT_INDICATOR_WIDTH - self.style.padding)

    @property
    def sort_state(self) -> _SortState:
        """
        Sorted state of column of which this label belongs.
        """
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
            self.colors[self.indicator_pos] = self.data_table.color_theme.data_table_sort_indicator
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
        content_width = self.width - 2 * padding - _SORT_INDICATOR_WIDTH - _SORT_INDICATOR_SPACING
        content = "\n".join(
            f"{line:{align}{content_width}}{' ' * _SORT_INDICATOR_SPACING}"
            for line in self.label.splitlines()
        )
        add_text(self.canvas[:, padding:-_SORT_INDICATOR_WIDTH - padding], content)

        if self.allow_sorting:
            self.colors[self.indicator_pos] = self.data_table.color_theme.data_table_sort_indicator
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
    """
    A data cell in a data table.
    """
    def __init__(self, data: T, row_id: int, striped: bool=False, **kwargs):
        super().__init__(**kwargs)

        self.data = data
        """Data of cell."""

        lines = self.style.render(data).splitlines()

        self.cell_min_height = len(lines)
        """Minimum allowed height of cell."""
        self.cell_min_width = max(
            (
                max(wcswidth(line) for line in lines) +  # width of rendered data
                2 * self.style.padding
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
            for line in self.style.render(self.data).splitlines()
        )
        add_text(self.canvas[:, padding:self.width - padding], content)

    def update_hover(self):
        self.data_table._update_hover(self.column_id, self.row_id)

    def on_release(self):
        self.data_table._on_release()
        return True


class DataTable(Themable, ScrollView):
    """
    A data table widget.

    Parameters
    ----------
    data : dict[str, Sequence[T]] | None=None, default: None
        If given, construct a data table from this data. To gain more
        control over column styling use :meth:`add_column`.
    default_style : ColumnStyle | None, default: None
        Default style for new columns.
    select_items : SelectItems, default: SelectItems.Row
        Determines which items are selected when data table is clicked.
    zebra_stripes : bool, default: True
        Whether alternate rows are colored differently.
    allow_sorting : bool, default: True
        Whether columns can be sorted.
    allow_vertical_scroll : bool, default: True
        Allow vertical scrolling.
    allow_horizontal_scroll : bool, default: True
        Allow horizontal scrolling.
    show_vertical_bar : bool, default: True
        Show the vertical scrollbar.
    show_horizontal_bar : bool, default: True
        Show the horizontal scrollbar.
    is_grabbable : bool, default: True
        Allow moving scroll view by dragging mouse.
    scrollwheel_enabled : bool, default: True
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool, default: True
        Allow scrolling with arrow keys.
    vertical_proportion : float, default: 0.0
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float, default: 0.0
        Horizontal scroll position as a proportion of total.
    is_grabbable : bool, default: True
        If false, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If true, widget will not be pulled to front when grabbed.
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint, default: SizeHint(None, None)
        Proportion of parent's height and width. Non-None values will have
        precedent over :attr:`size`.
    min_height : int | None, default: None
        Minimum height set due to size_hint. Ignored if corresponding size
        hint is None.
    max_height : int | None, default: None
        Maximum height set due to size_hint. Ignored if corresponding size
        hint is None.
    min_width : int | None, default: None
        Minimum width set due to size_hint. Ignored if corresponding size
        hint is None.
    max_width : int | None, default: None
        Maximum width set due to size_hint. Ignored if corresponding size
        hint is None.
    pos_hint : PosHint, default: PosHint(None, None)
        Position as a proportion of parent's height and width. Non-None values
        will have precedent over :attr:`pos`.
    anchor : Anchor, default: Anchor.TOP_LEFT
        The point of the widget attached to :attr:`pos_hint`.
    is_transparent : bool, default: False
        If true, background_char and background_color_pair won't be painted.
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    background_char : str | None, default: None
        The background character of the widget if not `None` and if the widget
        is not transparent.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if not `None` and if the
        widget is not transparent.

    Attributes
    ----------
    default_style : ColumnStyle
        Default style for new columns.
    select_items : SelectItems
        Which items are selected when data table is clicked.
    zebra_stripes : bool
        Whether alternate rows are colored differently.
    allow_sorting : bool
        Whether columns can be sorted.
    view : Widget | None
        The scrolled widget.
    allow_vertical_scroll : bool
        Allow vertical scrolling.
    allow_horizontal_scroll : bool
        Allow horizontal scrolling.
    show_vertical_bar : bool
        Show the vertical scrollbar.
    show_horizontal_bar : bool
        Show the horizontal scrollbar.
    is_grabbable : bool
        Allow moving scroll view by dragging mouse.
    scrollwheel_enabled : bool
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool
        Allow scrolling with arrow keys.
    vertical_proportion : float
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float
        Horizontal scroll position as a proportion of total.
    view : Widget | None
        The scroll view's child.
    is_grabbable : bool
        If false, grabbable behavior is disabled.
    disable_ptf : bool
        If true, widget will not be pulled to front when grabbed.
    is_grabbed : bool
        True if widget is grabbed.
    mouse_dyx : Point
        Last change in mouse position.
    mouse_dy : int
        Last vertical change in mouse position.
    mouse_dx : int
        Last horizontal change in mouse position.
    size : Size
        Size of widget.
    height : int
        Height of widget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of widget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position relative to parent.
    top : int
        Y-coordinate of position.
    y : int
        Y-coordinate of position.
    left : int
        X-coordinate of position.
    x : int
        X-coordinate of position.
    bottom : int
        :attr:`top` + :attr:`height`.
    right : int
        :attr:`left` + :attr:`width`.
    absolute_pos : Point
        Absolute position on screen.
    center : Point
        Center of widget in local coordinates.
    size_hint : SizeHint
        Size as a proportion of parent's size.
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    min_height : int
        Minimum height allowed when using :attr:`size_hint`.
    max_height : int
        Maximum height allowed when using :attr:`size_hint`.
    min_width : int
        Minimum width allowed when using :attr:`size_hint`.
    max_width : int
        Maximum width allowed when using :attr:`size_hint`.
    pos_hint : PosHint
        Position as a proportion of parent's size.
    y_hint : float | None
        Vertical position as a proportion of parent's size.
    x_hint : float | None
        Horizontal position as a proportion of parent's size.
    anchor : Anchor
        Determines which point is attached to :attr:`pos_hint`.
    background_char : str | None
        Background character.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Widget | None
        Parent widget.
    children : list[Widget]
        Children widgets.
    is_transparent : bool
        True if widget is transparent.
    is_visible : bool
        True if widget is visible.
    is_enabled : bool
        True if widget is enabled.
    root : Widget | None
        If widget is in widget tree, return the root widget.
    app : App
        The running app.

    Methods
    -------
    add_column:
        Add a column to the data table.
    add_row:
        Add a row to the data table.
    remove_column:
        Remove a column by column id.
    remove_row:
        Remove a row by row id.
    row_id_from_index:
        Returns the row id of the row at index.
    column_id_from_index:
        Returns the column id of the column at index.
    update_theme:
        Paint the widget with current theme.
    grab:
        Grab the widget.
    ungrab:
        Ungrab the widget.
    grab_update:
        Update widget with incoming mouse events while grabbed.
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point is within widget's bounding box.
    collides_widget:
        True if other is within widget's bounding box.
    add_widget:
        Add a child widget.
    add_widgets:
        Add multiple child widgets.
    remove_widget:
        Remove a child widget.
    pull_to_front:
        Move to end of widget stack so widget is drawn last.
    walk_from_root:
        Yield all descendents of root widget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a widget property.
    unsubscribe:
        Unsubscribe to a widget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    on_add:
        Called after a widget is added to widget tree.
    on_remove:
        Called before widget is removed from widget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this widget and all descendents.
    """
    _IDS = count()

    def __init__(
        self,
        data: dict[str, Sequence[T]] | None=None,
        default_style: ColumnStyle | None=None,
        select_items: SelectItems=SelectItems.ROW,
        zebra_stripes: bool=True,
        allow_sorting: bool=True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._column_ids: list[int] = []
        """Column ids. Index of id corresponds to index of column in table."""
        self._column_styles: dict[int, ColumnStyle] = {}
        """Column id to column style."""
        self._column_labels = GridLayout(grid_rows=1, grid_columns=0, orientation=Orientation.LR_TB)
        """Grid layout containing column label cells."""
        self._rows: dict[int, GridLayout] = {}
        """Row id to grid layout for row."""
        self._hover_column_id = -1
        """Column id of column that mouse is hovering or -1 if no columns are hovered."""
        self._hover_row_id = -1
        """Row id of row that mouse is hovering or -1 if no columns are hovered."""
        self._table = GridLayout(grid_rows=1, grid_columns=1, orientation=Orientation.TB_LR)
        """Grid layout of column label and row grid layouts."""
        self._table.add_widget(self._column_labels)
        self.view = self._table

        self.default_style = default_style or ColumnStyle()
        """Default style for new columns."""
        self._select_items = select_items
        """Determines which items are selected when data table is clicked."""
        self._zebra_stripes = zebra_stripes
        """Whether alternate rows are colored differently."""
        self._allow_sorting = allow_sorting
        """Whether columns can be sorted."""

        if data is not None:
            for label, column in data.items():
                self.add_column(label, data=column)

    def _repaint_cells(self):
        for row in self._table.children[1:]:
            for i, cell in enumerate(row.children):
                cell.striped = self.zebra_stripes and i % 2 == 1
                self._paint_cell_normal(cell)

        column_id = self._hover_column_id
        row_id = self._hover_row_id
        self._hover_column_id = -1
        self._hover_row_id = -1
        self._update_hover(column_id, row_id)

    @property
    def select_items(self) -> SelectItems:
        """
        Determines which items are selected when data table is clicked.
        """
        return self._select_items

    @select_items.setter
    def select_items(self, select_items: SelectItems):
        select_items = SelectItems(select_items)
        self._select_items = select_items
        for row in self._table.children[1:]:
            for cell in row.children:
                cell.selected = False
        self._repaint_cells()

    @property
    def zebra_stripes(self) -> bool:
        """
        Whether alternate rows are colored differently.
        """
        return self._zebra_stripes

    @zebra_stripes.setter
    def zebra_stripes(self, zebra_stripes: bool):
        self._zebra_stripes = zebra_stripes
        self._repaint_cells()

    @property
    def allow_sorting(self) -> bool:
        """
        Whether columns can be sorted.
        """
        return self._allow_sorting

    @allow_sorting.setter
    def allow_sorting(self, allow_sorting: bool):
        self._allow_sorting = allow_sorting
        for column_label in self._column_labels.children:
            column_label.allow_sorting = allow_sorting

    def update_theme(self):
        primary = self.color_theme.primary
        self.background_color_pair = primary
        self._table.background_color_pair = primary

        label: _ColumnLabel
        for label in self._column_labels.children:
            label.default_color_pair = primary
            label.colors[:] = primary
            label.colors[label.indicator_pos] = self.color_theme.data_table_sort_indicator

        cell: _DataCell
        for row in self._rows.values():
            row.background_color_pair = primary
            for cell in row.children:
                self._paint_cell_normal(cell)
        self._update_hover(self._hover_column_id, self._hover_row_id)

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        if not self.collides_point(mouse_event.position):
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

    def _update_hover(self, column_id: int=-1, row_id: int=-1):
        cell: _DataCell

        match self.select_items:
            case SelectItems.ROW:
                if self._hover_row_id != row_id:
                    if self._hover_row_id != -1:
                        for cell in self._rows[self._hover_row_id].children:
                            self._paint_cell_normal(cell)
                    if row_id != -1:
                        for cell in self._rows[row_id].children:
                            self._paint_cell_hover(cell)
            case SelectItems.COLUMN:
                if self._hover_column_id != column_id:
                    if self._hover_column_id != -1:
                        old_column_index = self._column_ids.index(self._hover_column_id)
                        for row in self._rows.values():
                            self._paint_cell_normal(row.children[old_column_index])
                    if column_id != -1:
                        new_column_index = self._column_ids.index(column_id)
                        for row in self._rows.values():
                            self._paint_cell_hover(row.children[new_column_index])
            case SelectItems.CELL:
                if self._hover_column_id != column_id or self._hover_row_id != row_id:
                    if self._hover_column_id != -1 and self._hover_row_id != -1:
                        old_column_index = self._column_ids.index(self._hover_column_id)
                        self._paint_cell_normal(self._rows[self._hover_row_id].children[old_column_index])
                    if column_id != -1 and row_id != -1:
                        new_column_index = self._column_ids.index(column_id)
                        self._paint_cell_hover(self._rows[row_id].children[new_column_index])

        self._hover_row_id = row_id
        self._hover_column_id = column_id

    def _on_release(self):
        cell: _DataCell

        match self.select_items:
            case SelectItems.ROW:
                for cell in self._rows[self._hover_row_id].children:
                    cell.selected = not cell.selected
                    self._paint_cell_hover(cell)
            case SelectItems.COLUMN:
                column_index = self._column_ids.index(self._hover_column_id)
                for row in self._rows.values():
                    cell = row.children[column_index]
                    cell.selected = not cell.selected
                    self._paint_cell_hover(cell)
            case SelectItems.CELL:
                column_index = self._column_ids.index(self._hover_column_id)
                cell = self._rows[self._hover_row_id].children[column_index]
                cell.selected = not cell.selected
                self._paint_cell_hover(cell)

    def _sort(self, column_id: int, sort_state: _SortState):
        column_index = self._column_ids.index(column_id)
        sorted_rows = sorted(
            self._table.children[1:],
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

    def add_column(self, label: str, data: Sequence[T] | None=None, style: ColumnStyle | None=None) -> int:
        """
        Add a column to the data table.

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
            Column ID. This ID can be used to remove the column.
        """
        if data is None:
            data = []
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
        self._column_labels.add_widget(column_label)

        striped = self.zebra_stripes and len(self._column_labels.children) % 2 == 0
        for i, data in enumerate(data, start=1):
            if i < len(self._table.children):
                current_row = self._table.children[i]
                row_id = current_row.children[0].row_id
            else:
                current_row = GridLayout(grid_rows=1, grid_columns=0, orientation=Orientation.LR_BT)
                row_id = next(self._IDS)
                self._rows[row_id] = current_row
                self._table.grid_rows += 1
                self._table.add_widget(current_row)

            current_cell = _DataCell(data_table=self, column_id=column_id, data=data, row_id=row_id, striped=striped)
            current_row.grid_columns += 1
            current_row.add_widget(current_cell)

        self._fix_sizes()
        return column_id

    def add_row(self, row: Iterable[SupportsLessThan]) -> int:
        """
        Add a row to the data table.

        There must be at least one column before a row can be added. The number
        of items in the row must match the number of columns.

        Parameters
        ----------
        row : Iterable[SupportsLessThan]
            The row to add.

        Returns
        -------
        int
            Row ID. This ID can be used to remove the row.
        """
        if not self._column_labels.children:
            raise IndexError("No columns")

        row_layout = GridLayout(grid_rows=1, grid_columns=0, orientation=Orientation.LR_BT)
        row_id = next(self._IDS)
        self._rows[row_id] = row_layout
        self._table.grid_rows += 1
        self._table.add_widget(row_layout)

        column_label: _ColumnLabel
        for i, (column_label, row_item) in enumerate(zip(self._column_labels.children, row, strict=True)):
            striped = self.zebra_stripes and i % 2 == 1
            cell = _DataCell(
                data_table=self,
                column_id=column_label.column_id,
                data=row_item,
                row_id=row_id,
                striped=striped,
            )
            row_layout.grid_columns += 1
            row_layout.add_widget(cell)

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

        if column_id == self._hover_column_id:
            self._hover_column_id = -1

        column_index = self._column_ids.index(column_id)
        del self._column_ids[column_index]
        for row in self._table.children:
            row.remove_widget(row.children[column_index])
            row.grid_columns -= 1
            row._reposition_children()
        self._table._reposition_children()
        self._fix_sizes()
        self._repaint_cells()

    def remove_row(self, row_id: int):
        """
        Remove a row by row id.

        Row id can be retrieved by index with :meth:`row_id_from_index`.

        Parameters
        ----------
        row_id : int
            The id of the row to remove.
        """
        if row_id == self._hover_row_id:
            self._hover_row_id = -1

        row = self._rows.pop(row_id)
        self._table.remove_widget(row)
        self._table.grid_rows -= 1
        self._table._reposition_children()
        self._fix_sizes()

    def row_id_from_index(self, index: int):
        """
        Returns the row id of the row at index.

        Parameters
        ----------
        index : int
            Index of row in table.
        """
        return self._table.children[index - 1].children[0].row_id

    def column_id_from_index(self, index: int):
        """
        Returns the column id of the column at index.

        Parameters
        ----------
        index : int
            Index of column in table.
        """
        return self._column_labels.children[index].column_id
