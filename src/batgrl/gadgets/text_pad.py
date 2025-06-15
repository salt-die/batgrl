"""A text-pad gadget for multiline editable text."""

from __future__ import annotations

from dataclasses import astuple, dataclass

from ugrapheme import grapheme_iter, graphemes
from uwcwidth import wcswidth

from ..logging import get_logger
from ..terminal.events import KeyEvent, MouseEvent, PasteEvent
from ..text_tools import canvas_as_text, egc_chr, is_word_char
from .behaviors.focusable import Focusable
from .behaviors.grabbable import Grabbable
from .behaviors.themable import Themable
from .cursor import Cursor
from .gadget import Gadget, Point, Pointlike, PosHint, Size, SizeHint, Sizelike
from .scroll_view import ScrollView
from .text import Text

__all__ = ["Point", "Size", "TextPad"]

logger = get_logger(__name__)


@dataclass
class _TextSelection:
    start: Point
    end: Point


@dataclass
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

    def end_of_content(self) -> Point:
        y, x = self.first
        nlines = self.text.count("\n")
        if nlines:
            last_line = self.text[self.text.rfind("\n") + 1 :]
            return Point(y + nlines, wcswidth(last_line))
        return Point(y, x + wcswidth(self.text))

    def join(self, other: _TextEdit) -> bool:
        if other.end_of_content() == self.first:
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


class TextPad(Themable, Grabbable, Focusable, Gadget):
    r"""
    A text-pad gadget for multiline editable text.

    Supports pasting, mouse selection, and cursor navigation.

    Parameters
    ----------
    alpha : float, default: 1.0
        Transparency of gadget.
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
    replace_text(start, end, content)
        Replace text from ``start`` to ``end`` with ``content``.
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
        alpha: float = 1.0,
        size: Sizelike = Size(10, 10),
        pos: Pointlike = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
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
        )
        self._selection: _TextSelection | None = None
        """Currently selected text."""
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

        super().__init__(
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
    def alpha(self, alpha: float):
        self._pad.alpha = alpha

    @property
    def text(self) -> str:
        """The text pad's text."""
        return canvas_as_text(self._pad.canvas, self._line_widths)

    @text.setter
    def text(self, text: str):
        self._selection = None
        self.replace_text((0, 0), self.end_of_content, text)
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.cursor = self.end_of_content

    @property
    def cursor(self) -> Point:
        """The cursor position."""
        return self._cursor.pos

    @cursor.setter
    def cursor(self, cursor: Pointlike):
        """After setting cursor position, move pad so that cursor is visible."""
        self._cursor.pos = cursor
        self._scroll_view.scroll_to_rect(cursor)
        if self._selection is not None:
            self._selection.end = self.cursor
        self._highlight_selection()

    @property
    def end_of_content(self) -> Point:
        """Point after last character in text."""
        ll = self._line_widths
        return Point(len(ll) - 1, ll[-1])

    @property
    def page_lines(self) -> int:
        """Number of rows a page-up or page-down moves."""
        return self._scroll_view.port_height

    def replace_text(self, start: Pointlike, end: Pointlike, content: str) -> None:
        """
        Replace text from ``start`` to ``end`` with ``content``.

        Parameters
        ----------
        start : Pointlike
            The start of text to replace.
        end : Pointlike
            The end of text to replace.
        content : str
            The replacement text.
        """
        prev_selection = self._selection
        prev_cursor = self.cursor

        self._selection = None
        self._prev_x = None

        ll = self._line_widths
        pad = self._pad

        if start > end:
            start, end = end, start

        sy, sx = start
        ey, ex = end

        if ey >= len(ll):
            logger.debug(
                "replace_text: Delete end y-coordinate is greater than number of lines."
            )
            ey = len(ll) - 1
        if ex > ll[ey]:
            logger.debug(
                "replace_text: Delete end x-coordinate is greater than line length."
            )
            ex = ll[ey]

        if sy == ey:
            text = canvas_as_text(pad.canvas[sy, sx:ex])
        else:
            lines = [canvas_as_text(pad.canvas[sy, sx : ll[sy]])]
            for y in range(sy + 1, ey):
                lines.append(canvas_as_text(pad.canvas[y, : ll[y]]))
            lines.append(canvas_as_text(pad.canvas[ey, :ex]))
            text = "\n".join(lines)

        len_end = ll[ey] - ex
        len_start = ll[sy] = sx + len_end

        pad.canvas[sy, sx:len_start] = pad.canvas[ey, ex : ex + len_end]
        pad.canvas[sy, len_start:] = pad.default_cell

        remaining = pad.canvas[ey + 1 :]
        pad.canvas[sy + 1 : sy + 1 + len(remaining)] = remaining
        pad.canvas[sy + 1 + len(remaining) :] = pad.default_cell

        del ll[sy + 1 : ey + 1]
        height = max(len(ll), self._scroll_view.port_height)
        width = max(max(ll) + 1, self._scroll_view.port_width)
        pad.size = height, width

        line_remaining = pad.canvas[sy, sx : ll[sy]].copy()

        lines = content.split("\n")  # DO NOT USE `splitlines`.
        if len(lines) == 1:
            line = lines[0]
            line_width = wcswidth(line)

            ll[sy] += line_width
            if ll[sy] >= pad.width:
                pad.width = ll[sy] + 1

            pad.add_str(line, pos=(sy, sx))
            pad.canvas[sy, sx + line_width : ll[sy]] = line_remaining
            self.cursor = sy, sx + line_width
        else:
            first, *lines, last = lines
            newlines = len(lines) + 1
            width_last = wcswidth(last)
            last_y = sy + newlines

            ll[sy] = sx + wcswidth(first)
            for i, line in enumerate(lines, start=sy + 1):
                ll.insert(i, wcswidth(line))
            ll.insert(last_y, width_last + wcswidth(canvas_as_text(line_remaining)))

            height = max(len(ll), self._scroll_view.port_height)
            width = max(max(ll) + 1, self._scroll_view.port_width)
            pad.size = height, width

            pad.canvas[sy + newlines + 1 :] = pad.canvas[sy + 1 : -newlines]
            pad.canvas[sy, ll[sy] :] = pad.default_cell

            pad.add_str(first, pos=(sy, sx))
            for i, line in enumerate(lines, start=sy + 1):
                pad.add_str(line.ljust(pad.width), pos=(i, 0))

            pad.add_str(last, pos=(last_y, 0))
            pad.canvas[last_y, width_last : ll[last_y]] = line_remaining
            pad.canvas[last_y, ll[last_y] :] = pad.default_cell
            self.cursor = last_y, width_last

        inverse_edit = _TextEdit(
            prev_cursor, prev_selection, Point(sy, sx), self.cursor, text
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

    def undo(self):
        """Undo previous edit."""
        if self._undo_stack:
            last_edit = self._undo_stack.pop()
            self._replace_text_to_undo_stack = False
            self._replace_text_clears_redo = False
            self.replace_text(last_edit.start, last_edit.end, last_edit.text)
            self._selection = last_edit.selection
            self.cursor = last_edit.cursor

    def redo(self):
        """Redo previous undo."""
        if self._redo_stack:
            prev_edit = self._redo_stack.pop()
            self._replace_text_clears_redo = False
            self.replace_text(prev_edit.start, prev_edit.end, prev_edit.text)
            self._selection = prev_edit.selection
            self.cursor = prev_edit.cursor

    def _highlight_selection(self):
        fg = self._pad.canvas["fg_color"]
        bg = self._pad.canvas["bg_color"]
        fg[:] = self._pad.default_fg_color
        bg[:] = self._pad.default_bg_color

        if self._selection is not None and self._selection.start != self._selection.end:
            start, end = self._selection.start, self._selection.end
            if start > end:
                sy, sx = end
                ey, ex = start
            else:
                sy, sx = start
                ey, ex = end

            highlight_fg = self.get_color("text_pad_selection_highlight_fg")
            highlight_bg = self.get_color("text_pad_selection_highlight_bg")
            ll = self._line_widths
            if sy == ey:
                fg[sy, sx:ex] = highlight_fg
                bg[sy, sx:ex] = highlight_bg
            else:
                fg[sy, sx : ll[sy]] = highlight_fg
                bg[sy, sx : ll[sy]] = highlight_bg
                fg[ey, :ex] = highlight_fg
                bg[ey, :ex] = highlight_bg
                for i in range(sy + 1, ey):
                    fg[i, : ll[i]] = highlight_fg
                    bg[i, : ll[i]] = highlight_bg
        else:  # Add line highlight.
            fg[self.cursor.y, :] = self.get_color("text_pad_line_highlight_fg")
            bg[self.cursor.y, :] = self.get_color("text_pad_line_highlight_bg")

    def move_cursor_left(self, n: int = 1):
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

    def move_cursor_right(self, n: int = 1):
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

            if y == self.end_of_content.y:
                x = self._line_widths[y]
                break

            y += 1
            n -= len(egcs) + 1
            x = 0

        self.cursor = y, x

    def _fix_x(self, y, x):
        line = canvas_as_text(self._pad.canvas[y, : self._line_widths[y]])
        current_x = 0
        for egc in grapheme_iter(line):
            if current_x + wcswidth(egc) > x:
                return current_x
            current_x += wcswidth(egc)
        return self._line_widths[y]

    def move_cursor_up(self, n: int = 1):
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

    def move_cursor_down(self, n: int = 1):
        """Move cursor down `n` rows."""
        y, x = self._cursor.pos
        ey, ex = self.end_of_content

        if self._prev_x is None or y == ey and x == ex:
            self._prev_x = x

        if y < ey:
            y = min(ey, y + n)
            x = self._fix_x(y, min(self._prev_x, self._line_widths[y]))
        else:
            x = ex

        self.cursor = y, x

    def move_word_left(self):
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

    def move_word_right(self):
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

    def _enter(self):
        if self._selection is None:
            start = end = self.cursor
        else:
            start, end = self._selection.start, self._selection.end
        self.replace_text(start, end, "\n")
        self._redo_stack.clear()

    def _tab(self):
        if self._selection is None:
            start = end = self.cursor
        else:
            start, end = self._selection.start, self._selection.end
        self.replace_text(start, end, "    ")
        self._redo_stack.clear()

    def _backspace(self):
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

    def _delete(self):
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

    def _left(self):
        if self._selection is None:
            self.move_cursor_left()
        else:
            select_start = min(self._selection.start, self._selection.end)
            self._selection = None
            self.cursor = select_start

    def _right(self):
        if self._selection is None:
            self.move_cursor_right()
        else:
            select_end = max(self._selection.start, self._selection.end)
            self._selection = None
            self.cursor = select_end

    def _ctrl_left(self):
        self._selection = None
        self.move_word_left()

    def _ctrl_right(self):
        self._selection = None
        self.move_word_right()

    def _ctrl_a(self):
        """Select all."""
        self._selection = _TextSelection(Point(0, 0), self.end_of_content)
        self.cursor = self.end_of_content

    def _ctrl_d(self):
        """Select word."""
        self._selection = None
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

    def _up(self):
        if self._selection is not None:
            select_start = min(self._selection.start, self._selection.end)
            self._selection = None
            self.cursor = select_start
        self.move_cursor_up()

    def _down(self):
        if self._selection is not None:
            select_end = max(self._selection.start, self._selection.end)
            self._selection = None
            self.cursor = select_end
        self.move_cursor_down()

    def _pgup(self):
        if self._selection is not None:
            select_start = min(self._selection.start, self._selection.end)
            self._selection = None
            self.cursor = select_start
        self.move_cursor_up(self.page_lines)

    def _pgdn(self):
        if self._selection is not None:
            select_end = max(self._selection.start, self._selection.end)
            self._selection = None
            self.cursor = select_end
        self.move_cursor_down(self.page_lines)

    def _home(self):
        self._selection = None
        self._prev_x = None
        self.cursor = self.cursor.y, 0

    def _end(self):
        self._selection = None
        self._prev_x = None
        y = self.cursor.y
        self.cursor = y, self._line_widths[y]

    def _shift_left(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_left()

    def _shift_right(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_right()

    def _shift_ctrl_left(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_word_left()

    def _shift_ctrl_right(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_word_right()

    def _shift_up(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_up()

    def _shift_down(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_down()

    def _shift_pgup(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_up(self.page_lines)

    def _shift_pgdn(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.move_cursor_down(self.page_lines)

    def _shift_home(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self._prev_x = None
        self.cursor = self.cursor.y, 0

    def _shift_end(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self._prev_x = None
        y = self.cursor.y
        self.cursor = y, self._line_widths[y]

    def _escape(self):
        if self._selection is None:
            self.blur()
        else:
            self._selection = None
            self._highlight_selection()

    def _ascii(self, key: str):
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

    def grab(self, mouse_event):
        """Start selection on grab."""
        if mouse_event.button == "left" and self._pad.collides_point(mouse_event.pos):
            super().grab(mouse_event)

            y, x = self._pad.to_local(mouse_event.pos)
            if y >= len(self._line_widths):
                return

            x = min(x, self._line_widths[y])
            cursor = Point(y, x)

            if not mouse_event.shift or self._selection is None:
                self._selection = _TextSelection(cursor, cursor)

            self.cursor = cursor

    def grab_update(self, mouse_event: MouseEvent):
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

    def ungrab(self, mouse_event):
        """Clear an empty selection on ungrab."""
        super().ungrab(mouse_event)
        if self._selection is not None and self._selection.start == self._selection.end:
            self._selection = None

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._pad.is_transparent = self.is_transparent
        self._scroll_view.is_transparent = self.is_transparent

    def update_theme(self):
        """Paint the gadget with current theme."""
        primary_fg = self.get_color("primary_fg")
        primary_bg = self.get_color("primary_bg")

        self._pad.canvas["fg_color"] = self._pad.default_fg_color = primary_fg
        self._pad.canvas["bg_color"] = self._pad.default_bg_color = primary_bg
        self._highlight_selection()

    def on_add(self):
        """Bind pad resize to scroll view resize."""
        super().on_add()

        def resize_pad():
            height = max(len(self._line_widths), self._scroll_view.port_height)
            width = max(max(self._line_widths) + 1, self._scroll_view.port_width)
            self._pad.size = height, width
            self._highlight_selection()

        resize_pad()
        self._bind_uid = self._scroll_view.bind("size", resize_pad)

    def on_remove(self):
        """Unbind pad resize from scroll view resize."""
        self._scroll_view.unbind(self._bind_uid)
        super().on_remove()

    def on_focus(self):
        """Show cursor on focus."""
        self._cursor.is_enabled = True

    def on_blur(self):
        """Hide cursor on blur."""
        self._cursor.is_enabled = False
