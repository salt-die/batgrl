"""A text-pad gadget for multiline editable text."""

from __future__ import annotations

from dataclasses import astuple, dataclass
from typing import Any, Literal

from numpy import ndarray
from tree_sitter import Tree
from ugrapheme import grapheme_iter, graphemes
from uwcwidth import wcswidth

from ..array_types import UInt32_2D
from ..colors import Neptune, SyntaxHighlightTheme
from ..geometry import clamp
from ..queries import Highlighter, TSPoint, changed_ranges_point_range, get_highlighter
from ..terminal.events import KeyEvent, MouseButton, MouseEvent, PasteEvent
from ..text_tools import canvas_as_text, egc_chr, egc_ord, is_word_char
from .behaviors.focusable import Focusable
from .behaviors.grabbable import Grabbable
from .behaviors.themable import Themable
from .cursor import Cursor
from .gadget import Gadget, Point, Pointlike, PosHint, Size, SizeHint, Sizelike
from .scroll_view import ScrollView
from .text import Text

__all__ = ["Point", "Size", "TextPad"]

EMPTY_LINE_CHARACTER = " "
"""Character used to display selected empty-lines."""


@dataclass(slots=True)
class _TextSelection:
    start: Point
    end: Point


@dataclass(slots=True)
class _TextEdit:
    cursor: Point
    selection: _TextSelection | None
    start: Point
    end: Point
    text: str

    @property
    def first(self) -> Point:
        return min(self.start, self.end)

    @first.setter
    def first(self, first: Point):
        if self.start <= self.end:
            self.start = first
        else:
            self.end = first

    @property
    def last(self) -> Point:
        return max(self.start, self.end)

    @last.setter
    def last(self, last: Point):
        if self.end >= self.start:
            self.end = last
        else:
            self.start = last

    def end_of_text(self) -> Point:
        y, x = self.first
        nlines = self.text.count("\n")
        if nlines:
            last_line = self.text[self.text.rfind("\n") + 1 :]
            return Point(y + nlines, wcswidth(last_line))
        return Point(y, x + wcswidth(self.text))

    def join(self, other: _TextEdit) -> bool:
        if other.end_of_text() == self.first:
            fy, fx = self.first
            ly, lx = self.last
            oly, olx = other.last
            self.first = other.first
            if ly == fy:
                self.last = Point(oly, olx + (lx - fx))
            else:
                self.last = Point(oly + (ly - fy), lx)
            self.text = other.text + self.text
            return True

        if self.last == other.first:
            self.last = other.last
            self.text += other.text
            return True

        return False


@dataclass
class _TreeEdit:
    start_byte_offset: int
    start_point: TSPoint
    end_byte_offset: int
    end_point: TSPoint


class TextPad(Themable, Grabbable, Focusable, Gadget):
    r"""
    A text-pad gadget for multiline editable text.

    Supports pasting, mouse selection, and cursor navigation.

    Parameters
    ----------
    syntax_highlight_language : str | None, default: None
        If provided, text will be syntax highlighted for given language.
    syntax_highlight_theme : SyntaxHighlightTheme, default: Neptune
        Color theme for syntax highlighting.
    alpha : float, default: 1.0
        Transparency of gadget.
    is_grabbable : bool, default: True
        Whether grabbable behavior is enabled.
    ptf_on_grab : bool, default: False
        Whether the gadget will be pulled to front when grabbed.
    mouse_button : MouseButton | Literal["any"], default: "left"
        Mouse button used for grabbing.
    size : Sizelike, default: Size(10, 10)
        Size of gadget.
    pos : Pointlike, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    syntax_highlight_language : str | None
        If provided, text will be syntax highlighted for given language.
    syntax_highlight_theme : SyntaxHighlightTheme
        Color theme for syntax highlighting.
    alpha : float
        Transparency of gadget.
    text : str
        The text pad's text.
    cursor : Point
        The cursor position.
    page_lines : int
        Number of rows a page-up or -down moves.
    is_focused : bool
        Whether gadget has focus.
    any_focused : bool
        Whether any gadget has focus.
    is_grabbable : bool
        Whether grabbable behavior is enabled.
    ptf_on_grab : bool
        Whether the gadget will be pulled to front when grabbed.
    mouse_button : MouseButton | Literal["any"]
        Mouse button used for grabbing.
    is_grabbed : bool
        Whether gadget is grabbed.
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
        y-coordinate of top of gadget.
    y : int
        y-coordinate of top of gadget.
    left : int
        x-coordinate of left side of gadget.
    x : int
        x-coordinate of left side of gadget.
    bottom : int
        y-coordinate of bottom of gadget.
    right : int
        x-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : TotalSizeHint
        Size as a proportion of parent's height and width.
    pos_hint : TotalPosHint
        Position as a proportion of parent's height and width.
    parent: Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        Whether gadget is transparent.
    is_visible : bool
        Whether gadget is visible.
    is_enabled : bool
        Whether gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App | None
        The running app.

    Methods
    -------
    replace_text(start, end, text)
        Replace text from ``start`` to ``end`` with ``text``.
    undo()
        Undo previous edit.
    redo()
        Redo previous undo.
    move_cursor_left(n)
        Move cursor left `n` characters.
    move_cursor_right(n)
        Move cursor right `n` characters.
    move_cursor_up(n)
        Move cursor up `n` rows.
    move_cursor_down(n)
        Move cursor down `n` rows.
    move_word_left()
        Move cursor a word left.
    move_word_right()
        Move cursor a word right.
    get_color(color_name)
        Get a color by name from the current color theme.
    update_theme()
        Paint the gadget with current theme.
    focus()
        Focus gadget.
    blur()
        Un-focus gadget.
    focus_next()
        Focus next focusable gadget.
    focus_previous()
        Focus previous focusable gadget.
    on_focus()
        Update gadget when it gains focus.
    on_blur()
        Update gadget when it loses focus.
    grab(mouse_event)
        Grab the gadget.
    ungrab(mouse_event)
        Ungrab the gadget.
    grab_update(mouse_event)
        Update gadget with incoming mouse events while grabbed.
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(gadget_it, \*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    tween(...)
        Sequentially update gadget properties over time.
    on_size()
        Update gadget after a resize.
    on_transparency()
        Update gadget after transparency is enabled/disabled.
    on_add()
        Update gadget after being added to the gadget tree.
    on_remove()
        Update gadget after being removed from the gadget tree.
    on_key(key_event)
        Handle a key press event.
    on_mouse(mouse_event)
        Handle a mouse event.
    on_paste(paste_event)
        Handle a paste event.
    on_terminal_focus(focus_event)
        Handle a focus event.
    """

    def __init__(
        self,
        *,
        syntax_highlight_language: str | None = None,
        syntax_highlight_theme: SyntaxHighlightTheme = Neptune,
        alpha: float = 1.0,
        is_grabbable: bool = True,
        ptf_on_grab: bool = False,
        mouse_button: MouseButton | Literal["any"] = "left",
        size: Sizelike = Size(10, 10),
        pos: Pointlike = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ) -> None:
        self._cursor = Cursor()
        """The textpad's cursor."""
        self._prev_x: int | None = None
        """If the cursor has moved vertically, its previous x-coordinate."""
        self._pad = Text(size=(1, 1), is_transparent=is_transparent)
        """The textpad's text area."""
        self._scroll_view = ScrollView(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            arrow_keys_enabled=False,
            is_grabbable=False,
            alpha=0,
            is_transparent=is_transparent,
            dynamic_bars=True,
        )
        self._selection: _TextSelection | None = None
        """Currently selected text."""
        self._active_line: int | None = None
        """If there is no selection, the active line is the line the cursor resides."""
        self._line_widths: list[int] = [0]
        """Line widths of each line in the text area."""
        self._replace_text_to_undo_stack: bool = True
        """Whether ``replace_text`` uses the undo or redo stack."""
        self._replace_text_clears_redo: bool = True
        """Whether ``replace_text`` clears the redo stack."""
        self._undo_stack: list[_TextEdit] = []
        """Stack of undo text edits."""
        self._redo_stack: list[_TextEdit] = []
        """Stack of redo text edits."""
        self._highlighter: Highlighter | None
        """Parser and queries for syntax highlighting."""
        if syntax_highlight_language is None:
            self._highlighter = None
        else:
            self._highlighter = get_highlighter(syntax_highlight_language)
        self._syntax_highlight_theme: SyntaxHighlightTheme = syntax_highlight_theme
        """Theme for syntax highlighting."""
        self._syntax_tree: Tree | None = None

        super().__init__(
            is_grabbable=is_grabbable,
            ptf_on_grab=ptf_on_grab,
            mouse_button=mouse_button,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.alpha = alpha
        self._pad.add_gadget(self._cursor)
        self._scroll_view.view = self._pad
        self.add_gadget(self._scroll_view)

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._pad.alpha

    @alpha.setter
    def alpha(self, alpha: float) -> None:
        self._pad.alpha = alpha

    @property
    def text(self) -> str:
        """The text pad's text."""
        return canvas_as_text(self._pad.canvas, self._line_widths)

    @text.setter
    def text(self, text: str):
        self._clear_selection()
        self.replace_text((0, 0), self.end_of_text, text)
        self._undo_stack.clear()
        self._redo_stack.clear()

    @property
    def cursor(self) -> Point:
        """The cursor position."""
        return self._cursor.pos

    @cursor.setter
    def cursor(self, cursor: Pointlike) -> None:
        self._cursor.pos = cursor
        self._scroll_view.scroll_to_rect(cursor)
        self._update_selection()
        self._update_active_line()

    @property
    def end_of_text(self) -> Point:
        """Point after last character in text."""
        return Point(len(self._line_widths) - 1, self._line_widths[-1])

    @property
    def page_lines(self) -> int:
        """Number of rows a page-up or page-down moves."""
        return self._scroll_view.port_height

    @property
    def syntax_highlight_language(self) -> str | None:
        """Language for syntax highlighting."""
        if self._highlighter is None:
            return None
        return self._highlighter.language_name

    @syntax_highlight_language.setter
    def syntax_highlight_language(self, syntax_highlight_language: str | None) -> None:
        if syntax_highlight_language is None:
            self._highlighter = None
        else:
            self._highlighter = get_highlighter(syntax_highlight_language)
        self.update_theme()

    def _clear_active_line(self) -> None:
        if self._active_line is None:
            return

        y = self._active_line
        self._active_line = None
        if self._highlighter is None:
            self._pad.canvas["fg_color"][y : y + 1] = self.get_color("primary_fg")
            self._pad.canvas["bg_color"][y : y + 1] = self.get_color("primary_bg")
        else:
            self._pad.canvas["bg_color"][y : y + 1] = (
                self._syntax_highlight_theme.default_bg
            )

    def _update_active_line(self) -> None:
        if self._selection is not None and self._selection.start != self._selection.end:
            return

        y = self.cursor.y
        if self._active_line is not None and self._active_line != y:
            self._clear_active_line()

        self._active_line = y

        if self._highlighter is None:
            self._pad.canvas["fg_color"][y : y + 1] = self.get_color(
                "text_pad_line_highlight_fg"
            )
            self._pad.canvas["bg_color"][y : y + 1] = self.get_color(
                "text_pad_line_highlight_bg"
            )
        else:
            self._pad.canvas["bg_color"][y : y + 1] = (
                self._syntax_highlight_theme.active_line
            )

    def _hide_empty_lines(self) -> None:
        """Replace any EMPTY_LINE_CHARACTER on empty lines with whitespace."""
        if self._selection is None:
            return

        if self._highlighter is None:
            fg_color = self.get_color("primary_fg")
            bg_color = self.get_color("primary_bg")
        else:
            fg_color = self._syntax_highlight_theme.default_fg
            bg_color = self._syntax_highlight_theme.default_bg

        sy, ey = self._selection.start.y, self._selection.end.y
        if sy > ey:
            sy, ey = ey, sy
        for y in range(sy, ey):
            if self._line_widths[y] == 0:
                self._pad.canvas[y, 0:1]["ord"] = egc_ord(" ")
                self._pad.canvas[y, 0:1]["fg_color"] = fg_color
                self._pad.canvas[y, 0:1]["bg_color"] = bg_color

    def _show_empty_lines(self) -> None:
        """Show empty lines in selection with EMPTY_LINE_CHARACTER."""
        if self._selection is None:
            return

        sy, ey = self._selection.start.y, self._selection.end.y
        if sy > ey:
            sy, ey = ey, sy

        if self._highlighter is None:
            fg_color = self.get_color("text_pad_selection_highlight_fg")
            bg_color = self.get_color("text_pad_selection_highlight_bg")
        else:
            fg_color = self._syntax_highlight_theme.default_fg
            bg_color = self._syntax_highlight_theme.selection

        for y in range(sy, ey):
            if self._line_widths[y] == 0 and y != self._cursor.y:
                self._pad.canvas[y, 0:1]["ord"] = egc_ord(EMPTY_LINE_CHARACTER)
                self._pad.canvas[y, 0:1]["fg_color"] = fg_color
                self._pad.canvas[y, 0:1]["bg_color"] = bg_color

    def _fill_array(self, start: Point, end: Point, arr: ndarray, value: Any) -> None:
        """Fill ``arr`` from ``start`` to ``end`` with ``value``."""
        if start < end:
            (sy, sx), (ey, ex) = start, end
        else:
            (sy, sx), (ey, ex) = end, start

        if sy == ey:
            arr[sy, sx:ex] = value
        else:
            arr[sy, sx : self._line_widths[sy]] = value
            for i in range(sy + 1, ey):
                arr[i, : self._line_widths[i]] = value
            arr[ey, :ex] = value

    def _repaint_selection(self, start: Point, end: Point, *, selected: bool) -> None:
        """Repaint text from ``start`` to ``end`` as if it was selected or not."""
        if start == end:
            return

        if selected:
            if self._highlighter is None:
                fg = self.get_color("text_pad_selection_highlight_fg")
                bg = self.get_color("text_pad_selection_highlight_bg")
            else:
                fg = None
                bg = self._syntax_highlight_theme.selection
        else:
            if self._highlighter is None:
                fg = self.get_color("primary_fg")
                bg = self.get_color("primary_bg")
            else:
                fg = None
                bg = self._syntax_highlight_theme.default_bg

        if fg is not None:
            self._fill_array(start, end, self._pad.canvas["fg_color"], fg)
        self._fill_array(start, end, self._pad.canvas["bg_color"], bg)

    def _clear_selection(self) -> None:
        if self._selection is None:
            return

        self._hide_empty_lines()
        start = self._selection.start
        end = self._selection.end
        self._selection = None
        self._repaint_selection(start, end, selected=False)

    def _update_selection(self) -> None:
        """
        Expand or shrink and repaint currently selected text by setting selection.end to
        current cursor position.
        """
        if self._selection is None:
            return

        if self._active_line is not None:
            self._clear_active_line()
        self._hide_empty_lines()

        if (
            self.cursor <= self._selection.start <= self._selection.end
            or self._selection.end <= self._selection.start <= self.cursor
        ):
            clear_start = self._selection.start
            clear_end = self._selection.end
            paint_start = self.cursor
            paint_end = self._selection.start
        elif (
            self.cursor <= self._selection.end <= self._selection.start
            or self._selection.start <= self._selection.end <= self.cursor
        ):
            clear_start = None
            clear_end = None
            paint_start = self.cursor
            paint_end = self._selection.end
        else:
            # self._selection.start <= self.cursor <= self._selection.end
            # or self._selection.end <= self.cursor <= self._selection.start
            clear_start = self.cursor
            clear_end = self._selection.end
            paint_start = None
            paint_end = None

        self._selection.end = self.cursor
        if clear_start is not None and clear_end is not None:
            self._repaint_selection(clear_start, clear_end, selected=False)
        if paint_start is not None and paint_end is not None:
            self._repaint_selection(paint_start, paint_end, selected=True)

        self._show_empty_lines()

    def _tree_edit(self, start: Pointlike, end: Pointlike) -> _TreeEdit | None:
        """
        Convert point (row, column) in text pad to tree-sitter points and byte
        offsets.
        """
        if self._highlighter is None:
            return None

        ords: UInt32_2D = self._pad.canvas["ord"]

        sy, sx = start
        start_byte_offset = 0
        start_row_byte_offset = 0

        for v in range(sy):
            for u in range(self._line_widths[v]):
                start_byte_offset += len(egc_chr(ords[v, u]).encode())
            start_byte_offset += 1

        for u in range(sx):
            start_row_byte_offset += len(egc_chr(ords[sy, u]).encode())

        start_byte_offset += start_row_byte_offset

        ey, ex = end
        nbytes = ey - sy
        if sy == ey:
            for u in range(sx, ex):
                nbytes += len(egc_chr(ords[sy, u]).encode())
            end_row_byte_offset = start_row_byte_offset + nbytes
        else:
            # Last bit of first line
            for u in range(sx, self._line_widths[sy]):
                nbytes += len(egc_chr(ords[sy, u]).encode())

            # All of middle lines
            for v in range(sy + 1, ey):
                for u in range(self._line_widths[v]):
                    nbytes += len(egc_chr(ords[v, u]).encode())

            # First bit of last line
            end_row_byte_offset = 0
            for u in range(ex):
                end_row_byte_offset += len(egc_chr(ords[ey, u]).encode())
            nbytes += end_row_byte_offset

        end_byte_offset = start_byte_offset + nbytes
        return _TreeEdit(
            start_byte_offset,
            (sy, start_row_byte_offset),
            end_byte_offset,
            (ey, end_row_byte_offset),
        )

    def _pos_to_point(self, pos: Point, point: Pointlike, byte_offset: int) -> TSPoint:
        """
        Convert ``pos`` (row, column) to a tree sitter point (row, byte_offset).

        The return value is calculated starting from previously calculated ``point``
        and ``byte_offset`` to save some effort.
        """
        ords: UInt32_2D = self._pad.canvas["ord"]
        sy, sx = point
        ey, ex = pos
        if ey == sy:
            for u in range(sx, ex):
                byte_offset += len(egc_chr(ords[sy, u]).encode())
            return ey, byte_offset

        byte_offset = 0
        for u in range(ex):
            byte_offset += len(egc_chr(ords[ey, u]).encode())
        return ey, byte_offset

    def _tree_sitter_read_pad(self, _, point: tuple[int, int]) -> bytes:
        y, x = self._pad._tree_sitter_point_to_pos(point)
        if y >= len(self._line_widths):
            return b""

        end_column = self._line_widths[y]
        if self._pad._injection_range is not None:
            if y > self._pad._injection_range.end_row:
                return b""

            if y == self._pad._injection_range.end_row:
                end_column = self._pad._injection_range.end_column

        ords = self._pad.canvas["ord"][y, x:end_column].tolist()
        return "".join(egc_chr(ord_) for ord_ in ords).encode() + b"\n"

    def _highlight(
        self, tree_edit: _TreeEdit, new_end_byte: int, new_end_point: TSPoint
    ) -> None:
        """Incremental highlight of text."""
        if self._highlighter is None:
            return None

        old_tree = self._syntax_tree
        if old_tree is None:
            self._syntax_tree = self._highlighter.parser.parse(
                self._tree_sitter_read_pad
            )
            return

        old_tree.edit(
            tree_edit.start_byte_offset,
            tree_edit.end_byte_offset,
            new_end_byte,
            tree_edit.start_point,
            tree_edit.end_point,
            new_end_point,
        )
        self._syntax_tree = self._highlighter.parser.parse(
            self._tree_sitter_read_pad, old_tree
        )

        changed_ranges = old_tree.changed_ranges(self._syntax_tree)
        if changed_ranges:
            point_range = changed_ranges_point_range(changed_ranges)
        else:
            point_range = tree_edit.start_point, new_end_point

        self._pad._highlight(
            self._syntax_highlight_theme,
            self._highlighter,
            self._syntax_tree,
            point_range,
        )

    def replace_text(self, start: Pointlike, end: Pointlike, text: str) -> None:
        """
        Replace text pad text from ``start`` to ``end`` with ``text``.

        Parameters
        ----------
        start : Pointlike
            The start of text to replace.
        end : Pointlike
            The end of text to replace.
        text : str
            The replacement text.
        """
        prev_selection = self._selection
        prev_cursor = self.cursor

        self._clear_selection()
        self._clear_active_line()
        self._prev_x = None

        pad = self._pad
        nlines = len(self._line_widths)

        if start > end:
            start, end = end, start

        tree_edit = self._tree_edit(start, end)

        sy, sx = start
        ey, ex = end

        # Clamp start and end within text.
        sy = clamp(sy, 0, nlines - 1)
        sx = clamp(sx, 0, self._line_widths[sy])
        ey = clamp(ey, 0, nlines - 1)
        ex = clamp(ex, 0, self._line_widths[ey])

        if sy == ey:
            replaced = canvas_as_text(pad.canvas[sy, sx:ex])
        else:
            replaced_lines = [
                canvas_as_text(pad.canvas[sy, sx : self._line_widths[sy]])
            ]
            for y in range(sy + 1, ey):
                replaced_lines.append(
                    canvas_as_text(pad.canvas[y, : self._line_widths[y]])
                )
            replaced_lines.append(canvas_as_text(pad.canvas[ey, :ex]))
            replaced = "\n".join(replaced_lines)

        line_after_replace = pad.canvas[ey, ex : self._line_widths[ey]].copy()
        line_after_replace_width = self._line_widths[ey] - ex

        lines = text.split("\n")
        new_lines = len(lines) - 1

        line_widths: list[int] = [wcswidth(line) for line in lines]
        line_widths[0] += sx
        end_x = line_widths[-1]
        line_widths[-1] += line_after_replace_width
        self._line_widths[sy : ey + 1] = line_widths

        # Label all lines after ``end`` "remainder":
        # If the pad will shrink, move remainder before resizing pad (before
        # remainder is clipped). Otherwise, move remainder after resizing pad (so pad
        # has enough vertical space).
        dy = new_lines - ey + sy
        if dy < 0:
            pad.canvas[ey + 1 + dy : nlines + dy] = pad.canvas[ey + 1 : nlines]
            pad.canvas[nlines + dy :] = pad.default_cell

        self._set_pad_size()

        if dy > 0:
            pad.canvas[ey + 1 + dy : nlines + dy] = pad.canvas[ey + 1 : nlines]

        end_y = sy + new_lines
        if new_lines == 0:
            [line] = lines
            pad.add_str(line, pos=start)
            pad.canvas[sy, end_x : self._line_widths[sy]] = line_after_replace
            pad.canvas[sy, self._line_widths[sy] :] = pad.default_cell
        else:
            first_line, *middle_lines, last_line = lines
            pad.add_str(first_line, pos=start)
            pad.canvas[sy, self._line_widths[sy] :] = pad.default_cell
            for y, line in enumerate(middle_lines, start=sy + 1):
                pad.add_str(line, pos=(y, 0))
                pad.canvas[y, self._line_widths[y] :] = pad.default_cell
            pad.add_str(last_line, pos=(end_y, 0))
            pad.canvas[
                end_y,
                end_x : self._line_widths[end_y],
            ] = line_after_replace
            pad.canvas[end_y, self._line_widths[end_y] :] = pad.default_cell
        cursor = Point(end_y, end_x)

        inverse_edit = _TextEdit(
            prev_cursor, prev_selection, Point(sy, sx), cursor, replaced
        )
        if self._replace_text_to_undo_stack:
            stack = self._undo_stack
        else:
            stack = self._redo_stack
            self._replace_text_to_undo_stack = True

        if self._replace_text_clears_redo:
            self._redo_stack.clear()
        else:
            self._replace_text_clears_redo = True

        if not (stack and stack[-1].join(inverse_edit)):
            stack.append(inverse_edit)

        if tree_edit is not None:
            new_end_byte = tree_edit.start_byte_offset + len(text.encode())
            new_end_point = self._pos_to_point(cursor, start, tree_edit.start_point[1])
            self._highlight(tree_edit, new_end_byte, new_end_point)

        self.cursor = cursor

    def undo(self) -> None:
        """Undo previous edit."""
        if not self._undo_stack:
            return

        last_edit = self._undo_stack.pop()
        self._replace_text_to_undo_stack = False
        self._replace_text_clears_redo = False
        self.replace_text(last_edit.start, last_edit.end, last_edit.text)
        self.cursor = last_edit.cursor

        if last_edit.selection is not None:
            self._selection = last_edit.selection
            self._clear_active_line()
            self._repaint_selection(
                self._selection.start, self._selection.end, selected=True
            )
            self._show_empty_lines()

    def redo(self) -> None:
        """Redo previous undo."""
        if not self._redo_stack:
            return

        prev_edit = self._redo_stack.pop()
        self._replace_text_clears_redo = False
        self.replace_text(prev_edit.start, prev_edit.end, prev_edit.text)
        self.cursor = prev_edit.cursor

        if prev_edit.selection is not None:
            self._selection = prev_edit.selection
            self._clear_active_line()
            self._repaint_selection(
                self._selection.start, self._selection.end, selected=True
            )
            self._show_empty_lines()

    def move_cursor_left(self, n: int = 1) -> None:
        """Move cursor left `n` characters."""
        self._prev_x = None
        y, x = self._cursor.pos

        while n > 0:
            text_before_cursor = canvas_as_text(self._pad.canvas[y, :x])
            egcs = graphemes(text_before_cursor)
            if n <= len(egcs):
                x = wcswidth(egcs[:-n])
                break

            if y == 0:
                x = 0
                break

            y -= 1
            x = self._line_widths[y]
            n -= len(egcs) + 1

        self.cursor = y, x

    def move_cursor_right(self, n: int = 1) -> None:
        """Move cursor right `n` characters."""
        self._prev_x = None
        y, x = self._cursor.pos

        while n > 0:
            text_after_cursor = canvas_as_text(
                self._pad.canvas[y, x : self._line_widths[y]]
            )
            egcs = graphemes(text_after_cursor)
            if n <= len(egcs):
                x += wcswidth(egcs[:n])
                break

            if y == self.end_of_text.y:
                x = self._line_widths[y]
                break

            y += 1
            n -= len(egcs) + 1
            x = 0

        self.cursor = y, x

    def _fix_x(self, y, x) -> int:
        line = canvas_as_text(self._pad.canvas[y, : self._line_widths[y]])
        current_x = 0
        for egc in grapheme_iter(line):
            if current_x + wcswidth(egc) > x:
                return current_x
            current_x += wcswidth(egc)
        return self._line_widths[y]

    def move_cursor_up(self, n: int = 1) -> None:
        """Move cursor up `n` rows."""
        y, x = self._cursor.pos

        if self._prev_x is None or y == x == 0:
            self._prev_x = x

        if y > 0:
            y = max(0, y - n)
            x = self._fix_x(y, min(self._prev_x, self._line_widths[y]))
        else:
            x = 0

        self.cursor = y, x

    def move_cursor_down(self, n: int = 1) -> None:
        """Move cursor down `n` rows."""
        y, x = self._cursor.pos
        ey, ex = self.end_of_text

        if self._prev_x is None or y == ey and x == ex:
            self._prev_x = x

        if y < ey:
            y = min(ey, y + n)
            x = self._fix_x(y, min(self._prev_x, self._line_widths[y]))
        else:
            x = ex

        self.cursor = y, x

    def move_word_left(self) -> None:
        """Move cursor a word left."""
        self._prev_x = None
        last_x = self.cursor.x
        first_char_found = char_is_word_char = False
        while True:
            self.move_cursor_left()
            if self.cursor.x == last_x:
                break

            last_x = self.cursor.x

            current_char = egc_chr(self._pad.canvas[self.cursor]["ord"])
            if not first_char_found:
                if not current_char.isspace():
                    first_char_found = True
                    char_is_word_char = is_word_char(current_char)
            elif current_char.isspace() or char_is_word_char != is_word_char(
                current_char
            ):
                self.move_cursor_right()
                break

    def move_word_right(self) -> None:
        """Move cursor a word right."""
        self._prev_x = None
        last_x = self.cursor.x
        first_char_found = char_is_word_char = False
        while True:
            self.move_cursor_right()
            if self.cursor.x == last_x:
                break

            last_x = self.cursor.x

            current_char = egc_chr(self._pad.canvas[self.cursor]["ord"])
            if not first_char_found:
                if not current_char.isspace():
                    first_char_found = True
                    char_is_word_char = is_word_char(current_char)
            elif current_char.isspace() or char_is_word_char != is_word_char(
                current_char
            ):
                break

    def _enter(self) -> None:
        if self._selection is None:
            start = end = self.cursor
        else:
            start, end = self._selection.start, self._selection.end
        self.replace_text(start, end, "\n")
        self._redo_stack.clear()

    def _tab(self) -> None:
        if self._selection is None:
            start = end = self.cursor
        else:
            start, end = self._selection.start, self._selection.end
        self.replace_text(start, end, "    ")
        self._redo_stack.clear()

    def _backspace(self) -> None:
        if self._selection is None:
            end = self.cursor
            self.move_cursor_left()
            start = self.cursor
            self.cursor = end
            if start == end:
                return
        else:
            start, end = self._selection.start, self._selection.end
        self.replace_text(start, end, "")

    def _delete(self) -> None:
        if self._selection is None:
            start = self.cursor
            self.move_cursor_right()
            end = self.cursor
            self.cursor = start
            if start == end:
                return
        else:
            start, end = self._selection.start, self._selection.end
        self.replace_text(start, end, "")

    def _left(self) -> None:
        if self._selection is None:
            self.move_cursor_left()
        else:
            select_start = min(self._selection.start, self._selection.end)
            self._clear_selection()
            self.cursor = select_start

    def _right(self) -> None:
        if self._selection is None:
            self.move_cursor_right()
        else:
            select_end = max(self._selection.start, self._selection.end)
            self._clear_selection()
            self.cursor = select_end

    def _ctrl_left(self) -> None:
        self._clear_selection()
        self.move_word_left()

    def _ctrl_right(self) -> None:
        self._clear_selection()
        self.move_word_right()

    def _ctrl_a(self) -> None:
        """Select all."""
        self._selection = _TextSelection(Point(0, 0), self.end_of_text)
        self._repaint_selection(
            self._selection.start, self._selection.end, selected=True
        )
        self.cursor = self.end_of_text

    def _ctrl_d(self) -> None:
        """Select word."""
        self._clear_selection()
        last_x = self.cursor.x
        while True:
            self.move_cursor_left()
            if last_x == self.cursor.x:
                break
            if not is_word_char(egc_chr(self._pad.canvas[self.cursor]["ord"])):
                self.move_cursor_right()
                break
            last_x = self.cursor.x

        self._selection = _TextSelection(self.cursor, self.cursor)
        last_x = self.cursor.x
        while True:
            if not is_word_char(egc_chr(self._pad.canvas[self.cursor]["ord"])):
                break
            self.move_cursor_right()
            if last_x == self.cursor.x:
                break
            last_x = self.cursor.x

    def _up(self) -> None:
        if self._selection is not None:
            select_start = min(self._selection.start, self._selection.end)
            self._clear_selection()
            self.cursor = select_start
        self.move_cursor_up()

    def _down(self) -> None:
        if self._selection is not None:
            select_end = max(self._selection.start, self._selection.end)
            self._clear_selection()
            self.cursor = select_end
        self.move_cursor_down()

    def _pgup(self) -> None:
        if self._selection is not None:
            select_start = min(self._selection.start, self._selection.end)
            self._clear_selection()
            self.cursor = select_start
        self.move_cursor_up(self.page_lines)

    def _pgdn(self) -> None:
        if self._selection is not None:
            select_end = max(self._selection.start, self._selection.end)
            self._clear_selection()
            self.cursor = select_end
        self.move_cursor_down(self.page_lines)

    def _home(self) -> None:
        self._clear_selection()
        self._prev_x = None
        self.cursor = self.cursor.y, 0

    def _end(self) -> None:
        self._clear_selection()
        self._prev_x = None
        y = self.cursor.y
        self.cursor = y, self._line_widths[y]

    def _shift_left(self) -> None:
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_left()

    def _shift_right(self) -> None:
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_right()

    def _shift_ctrl_left(self) -> None:
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_word_left()

    def _shift_ctrl_right(self) -> None:
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_word_right()

    def _shift_up(self) -> None:
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_up()

    def _shift_down(self) -> None:
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_down()

    def _shift_pgup(self) -> None:
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_up(self.page_lines)

    def _shift_pgdn(self) -> None:
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_down(self.page_lines)

    def _shift_home(self) -> None:
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self._prev_x = None
        self.cursor = self.cursor.y, 0

    def _shift_end(self) -> None:
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self._prev_x = None
        y = self.cursor.y
        self.cursor = y, self._line_widths[y]

    def _escape(self) -> None:
        if self._selection is None:
            self.blur()
        else:
            self._clear_selection()

    def _ascii(self, key: str) -> None:
        if self._selection is None:
            start = end = self.cursor
        else:
            start, end = self._selection.start, self._selection.end
        self.replace_text(start, end, key)

    __HANDLERS = {
        ("enter", False, False, False): _enter,
        ("tab", False, False, False): _tab,
        ("backspace", False, False, False): _backspace,
        ("delete", False, False, False): _delete,
        ("left", False, False, False): _left,
        ("right", False, False, False): _right,
        ("left", False, True, False): _ctrl_left,
        ("right", False, True, False): _ctrl_right,
        ("up", False, False, False): _up,
        ("down", False, False, False): _down,
        ("page_up", False, False, False): _pgup,
        ("page_down", False, False, False): _pgdn,
        ("home", False, False, False): _home,
        ("end", False, False, False): _end,
        ("left", False, False, True): _shift_left,
        ("right", False, False, True): _shift_right,
        ("left", False, True, True): _shift_ctrl_left,
        ("right", False, True, True): _shift_ctrl_right,
        ("up", False, False, True): _shift_up,
        ("down", False, False, True): _shift_down,
        ("page_up", False, False, True): _shift_pgup,
        ("page_down", False, False, True): _shift_pgdn,
        ("home", False, False, True): _shift_home,
        ("end", False, False, True): _shift_end,
        ("escape", False, False, False): _escape,
        ("z", False, True, False): undo,
        ("y", False, True, False): redo,
        ("r", False, True, False): redo,
        ("a", False, True, False): _ctrl_a,
        ("d", False, True, False): _ctrl_d,
    }

    def on_key(self, key_event: KeyEvent) -> bool | None:
        """Process key press."""
        if not self.is_focused:
            return super().on_key(key_event)

        if (
            not key_event.alt
            and not key_event.ctrl
            and not key_event.shift
            and len(key_event.key) == 1
        ):
            self._ascii(key_event.key)
        elif handler := self.__HANDLERS.get(
            astuple(key_event)
        ):  # FIXME: Might break if extra args added to key_event
            handler(self)
        else:
            return super().on_key(key_event)

        return True

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        """Add paste to text pad."""
        if not self.is_focused:
            return

        if self._selection is None:
            start = end = self.cursor
        else:
            start, end = self._selection.start, self._selection.end
        self.replace_text(start, end, paste_event.paste)
        self._redo_stack.clear()

        return True

    def grab(self, mouse_event) -> None:
        """Start selection on grab."""
        if self._pad.collides_point(mouse_event.pos):
            super().grab(mouse_event)

            y, x = self._pad.to_local(mouse_event.pos)
            if y >= len(self._line_widths):
                return

            x = min(x, self._line_widths[y])
            cursor = Point(y, x)

            if not mouse_event.shift or self._selection is None:
                self._clear_selection()
                self._selection = _TextSelection(cursor, cursor)

            self.cursor = cursor

    def grab_update(self, mouse_event: MouseEvent) -> None:
        """Update selection on grab update."""
        if self._pad.collides_point(mouse_event.pos):
            y, x = self._pad.to_local(mouse_event.pos)
            if y < len(self._line_widths):
                x = min(x, self._line_widths[y])
                self.cursor = y, x
        else:
            cy, cx = self.cursor
            y, x = self.to_local(mouse_event.pos)
            h, w = self.size

            if y < 0:
                self.move_cursor_up()
            elif y >= h:
                self.move_cursor_down()

            if x < 0:
                if cx > 0:
                    self.move_cursor_left()
            elif x >= w:
                if cx < self._line_widths[cy]:
                    self.move_cursor_right()

    def ungrab(self, mouse_event) -> None:
        """Clear an empty selection on ungrab."""
        super().ungrab(mouse_event)
        if self._selection is not None and self._selection.start == self._selection.end:
            self._clear_selection()

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._pad.is_transparent = self.is_transparent
        self._scroll_view.is_transparent = self.is_transparent

    def update_theme(self) -> None:
        """Paint the gadget with current theme."""
        selection = self._selection
        self._clear_selection()

        if self._highlighter is None:
            self._cursor.reverse = True
            self._cursor.fg_color = None
            self._cursor.bg_color = None
            self._pad.default_fg_color = self.get_color("primary_fg")
            self._pad.default_bg_color = self.get_color("primary_bg")
            self._pad.canvas[["style", "fg_color", "bg_color"]] = (
                self._pad.default_cell[["style", "fg_color", "bg_color"]]
            )
            self._syntax_tree = None
        else:
            self._cursor.reverse = None
            self._cursor.fg_color = self._syntax_highlight_theme.cursor_fg
            self._cursor.bg_color = self._syntax_highlight_theme.cursor_bg
            self._pad.default_fg_color = self._syntax_highlight_theme.default_fg
            self._pad.default_bg_color = self._syntax_highlight_theme.default_bg
            self._syntax_tree = self._highlighter.parser.parse(
                self._tree_sitter_read_pad
            )
            self._pad._highlight(
                self._syntax_highlight_theme, self._highlighter, self._syntax_tree
            )

        self._selection = selection
        if selection is None or selection.start == selection.end:
            self._update_active_line()
        else:
            self._repaint_selection(selection.start, selection.end, selected=True)
            self._show_empty_lines()

    def _set_pad_size(self) -> None:
        nlines = len(self._line_widths)
        pad_width = max(self._line_widths) + 1
        h, w = self.size
        height = max(nlines, h - (pad_width > w))
        width = max(pad_width, w - 2 * (nlines > h))
        self._pad.size = height, width

    def on_size(self) -> None:
        """Update pad size on resize."""
        self._set_pad_size()

    def on_focus(self) -> None:
        """Show cursor on focus."""
        self._cursor.is_enabled = True
        self._update_active_line()

    def on_blur(self) -> None:
        """Hide cursor on blur."""
        self._cursor.is_enabled = False
        self._clear_selection()
        self._clear_active_line()
