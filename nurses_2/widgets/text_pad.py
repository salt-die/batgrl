"""
A text-pad widget for multiline editable text.
"""
from functools import wraps

from wcwidth import wcswidth

from ..io import Key, KeyEvent, Mods, MouseButton, MouseEvent, PasteEvent
from .behaviors.focusable import Focusable
from .behaviors.themable import Themable
from .scroll_view import ScrollView
from .text_widget import Point, TextWidget, add_text, style_char

WORD_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_")


def undoable(method):
    """
    Adds textpad text to the undo stack if a method modifies it.
    """

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        before_text = self.text
        before_cursor = self.cursor
        method(self, *args, **kwargs)
        after_text = self.text
        if before_text != after_text:
            self._undo_stack.append((before_text, before_cursor))
            self._redo_stack.clear()

    return wrapper


class TextPad(Themable, Focusable, ScrollView):
    """
    A text-pad widget for multiline editable text.

    Supports pasting, mouse selection, and cursor navigation.

    Parameters
    ----------
    allow_vertical_scroll : bool, default: True
        Allow vertical scrolling.
    allow_horizontal_scroll : bool, default: True
        Allow horizontal scrolling.
    show_vertical_bar : bool, default: True
        Show the vertical scrollbar.
    show_horizontal_bar : bool, default: True
        Show the horizontal scrollbar.
    scrollwheel_enabled : bool, default: True
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool, default: True
        Allow scrolling with arrow keys.
    scrollbar_color : Color, default: DEFAULT_SCROLLBAR_COLOR
        Background color of scrollbar.
    indicator_normal_color : Color, default: DEFAULT_INDICATOR_NORMAL
        Scrollbar indicator normal color.
    indicator_hover_color : Color, default: DEFAULT_INDICATOR_HOVER
        Scrollbar indicator hover color.
    indicator_press_color : Color, default: DEFAULT_INDICATOR_PRESS
        Scrollbar indicator press color.
    is_grabbable : bool, default: True
        If false, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If true, widget will not be pulled to front when grabbed.
    mouse_button : MouseButton, default: MouseButton.LEFT
        Mouse button used for grabbing.
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
    anchor : Anchor, default: "center"
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
    text : str
        The textpad's text.
    is_focused : bool
        True if widget has focus.
    any_focused : bool
        True if any widget has focus.
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
    scrollwheel_enabled : bool
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool
        Allow scrolling with arrow keys.
    scrollbar_color : Color
        Background color of scrollbar.
    indicator_normal_color : Color
        Scrollbar indicator normal color.
    indicator_hover_color : Color
        Scrollbar indicator hover color.
    indicator_press_color : Color
        Scrollbar indicator press color.
    vertical_proportion : float
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float
        Horizontal scroll position as a proportion of total.
    is_grabbable : bool
        If false, grabbable behavior is disabled.
    disable_ptf : bool
        If true, widget will not be pulled to front when grabbed.
    mouse_button : MouseButton
        Mouse button used for grabbing.
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
    focus:
        Focus widget.
    blur:
        Un-focus widget.
    focus_next:
        Focus next focusable widget.
    focus_previous:
        Focus previous focusable widget.
    on_focus:
        Called when widget is focused.
    on_blur:
        Called when widget loses focus.
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._prev_cursor_pos = Point(0, 0)
        self._last_x = None
        self._selection_start = self._selection_end = None
        self._line_lengths = [0]
        self._undo_stack = []
        self._redo_stack = []

        self._cursor = TextWidget(size=(1, 1), is_enabled=False)
        self._pad = TextWidget(size=(1, 1))
        self._pad.add_widget(self._cursor)
        self.view = self._pad

    def update_theme(self):
        primary = self.color_theme.primary

        self._cursor.colors[:] = primary.reversed()
        self._cursor.default_color_pair = primary.reversed()
        self._pad.colors[:] = primary
        self._pad.default_color_pair = primary
        self.background_color_pair = primary

        self._highlight_selection()

    def on_size(self):
        super().on_size()

        if self.port_width > self._pad.width:
            self._pad.width = self.port_width
        elif self.port_width < self._pad.width:
            self._pad.width = max(self.port_width, max(self._line_lengths) + 1)

        self._highlight_selection()

    def on_focus(self):
        self._cursor.is_enabled = True

    def on_blur(self):
        self._cursor.is_enabled = False

    def undo(self):
        if self._undo_stack:
            self._redo_stack.append((self.text, self.cursor))
            text, cursor = self._undo_stack.pop()
            self._update_text(text)
            self.cursor = cursor

    def redo(self):
        if self._redo_stack:
            self._undo_stack.append((self.text, self.cursor))
            text, cursor = self._redo_stack.pop()
            self._update_text(text)
            self.cursor = cursor

    @property
    def text(self) -> str:
        return "\n".join(
            "".join(row[:line_length])
            for row, line_length in zip(self._pad.canvas["char"], self._line_lengths)
        )

    @text.setter
    def text(self, text: str):
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._update_text(text)
        self.cursor = self.end_text_point

    def _update_text(self, text: str):
        self.unselect()
        lines = text.splitlines()
        self._line_lengths = list(map(wcswidth, lines))

        pad = self._pad
        pad.canvas[:] = style_char(" ")
        pad.height = len(lines)
        pad.width = max(max(self._line_lengths) + 1, self.port_width)

        add_text(pad.canvas, text)

    @property
    def cursor(self) -> Point:
        return self._cursor.pos

    @cursor.setter
    def cursor(self, cursor: Point):
        """
        After setting cursor position, move pad so that cursor is visible.
        """
        y, x = cursor
        self._prev_cursor_pos = self._cursor.pos
        self._cursor.pos = Point(y, x)
        self._cursor.canvas[0, 0] = self._pad.canvas[y, x]

        max_y = self.height - (self.show_horizontal_bar and 1) - 1
        if (rel_y := y + self._pad.y) > max_y:
            self._scroll_down(rel_y - max_y)
        elif rel_y < 0:
            self._scroll_up(-rel_y)

        max_x = self.port_width - 1
        if (rel_x := x + self._pad.x) > max_x:
            self._scroll_right(rel_x - max_x)
        elif rel_x < 0:
            self._scroll_left(-rel_x)

        self._update_selection()

    @property
    def has_selection(self) -> bool:
        return self._selection_start is not None and self._selection_end is not None

    @property
    def end_text_point(self) -> Point:
        """
        Point after last character in text.
        """
        ll = self._line_lengths
        return Point(len(ll) - 1, ll[-1])

    @property
    def page_lines(self) -> int:
        return self.height - 2 - self.show_horizontal_bar

    def select(self):
        if not self.has_selection:
            self._selection_start = self._selection_end = self.cursor

    def unselect(self):
        self._selection_start = self._selection_end = None

    def delete_selection(self):
        if not self.has_selection:
            return

        self._last_x = None

        pad = self._pad

        sy, sx = self._selection_start
        ey, ex = self._selection_end

        len_end = self._line_lengths[ey] - ex
        len_start = self._line_lengths[sy] = sx + len_end
        if len_start >= pad.width:
            pad.width = len_start + 1

        pad.canvas[sy, sx:len_start] = pad.canvas[ey, ex : ex + len_end]
        pad.canvas[sy, len_start:] = style_char(pad.default_char)

        remaining = pad.canvas[ey + 1 :]
        pad.canvas[sy + 1 : sy + 1 + len(remaining)] = remaining
        pad.height -= ey - sy
        del self._line_lengths[sy + 1 : ey + 1]

        self.unselect()

        self.cursor = sy, sx

    def _highlight_selection(self):
        colors = self._pad.colors
        colors[:] = self._pad.default_color_pair

        if self._selection_start != self._selection_end:
            sy, sx = self._selection_start
            ey, ex = self._selection_end
            highlight = self.color_theme.pad_selection_highlight
            ll = self._line_lengths

            if ey > sy:
                colors[sy, sx : ll[sy]] = highlight
                colors[ey, :ex] = highlight
                for i in range(sy + 1, ey):
                    colors[i, : ll[i]] = highlight
            else:
                colors[sy, sx:ex] = highlight
        else:  # If no selection or selection is empty, add line highlight.
            colors[self.cursor.y, :] = self.color_theme.pad_line_highlight

    def _update_selection(self):
        if self.has_selection:
            if self._prev_cursor_pos == self._selection_start:
                self._selection_start = self.cursor
            elif self._prev_cursor_pos == self._selection_end:
                self._selection_end = self.cursor

            if self._selection_start > self._selection_end:
                self._selection_start, self._selection_end = (
                    self._selection_end,
                    self._selection_start,
                )

        self._highlight_selection()

    def move_cursor_left(self, n: int = 1):
        self._last_x = None
        y, x = self._cursor.pos

        while n > 0:
            text_before_cursor = "".join(self._pad.canvas["char"][y, :x])
            nchars_before_cursor = len(text_before_cursor)
            if n <= nchars_before_cursor:
                x = wcswidth(text_before_cursor[:-n])
                break

            if y == 0:
                x = 0
                break

            y -= 1
            x = self._line_lengths[y]
            n -= nchars_before_cursor + 1

        self.cursor = y, x

    def move_cursor_right(self, n: int = 1):
        self._last_x = None
        y, x = self._cursor.pos

        while n > 0:
            text_after_cursor = "".join(
                self._pad.canvas["char"][y, x : self._line_lengths[y]]
            )
            nchars_after_cursor = len(text_after_cursor)
            if n <= nchars_after_cursor:
                x += wcswidth(text_after_cursor[:n])
                break

            if y == self.end_text_point.y:
                x = self._line_lengths[y]
                break

            y += 1
            n -= nchars_after_cursor + 1
            x = 0

        self.cursor = y, x

    def move_cursor_up(self, n: int = 1):
        y, x = self._cursor.pos

        if self._last_x is None or y == x == 0:
            self._last_x = x

        if y > 0:
            y = max(0, y - n)
            x = min(self._last_x, self._line_lengths[y])
        else:
            x = 0

        self.cursor = y, x

    def move_cursor_down(self, n: int = 1):
        y, x = self._cursor.pos
        ey, ex = self.end_text_point

        if self._last_x is None or y == ey and x == ex:
            self._last_x = x

        if y < ey:
            y = min(ey, y + n)
            x = min(self._last_x, self._line_lengths[y])
        else:
            x = ex

        self.cursor = y, x

    def move_word_left(self):
        last_x = self.cursor.x
        first_char_found = False
        while True:
            self.move_cursor_left()
            if self.cursor.x == last_x:
                break

            last_x = self.cursor.x

            current_char = self._pad.canvas[self.cursor]["char"]
            if not first_char_found:
                if not current_char.isspace():
                    first_char_found = True
                    is_word_char = current_char in WORD_CHARS
            elif current_char.isspace() or is_word_char != (current_char in WORD_CHARS):
                self.move_cursor_right()
                break

    def move_word_right(self):
        last_x = self.cursor.x
        first_char_found = False
        while True:
            self.move_cursor_right()
            if self.cursor.x == last_x:
                break

            last_x = self.cursor.x

            current_char = self._pad.canvas[self.cursor]["char"]
            if not first_char_found:
                if not current_char.isspace():
                    first_char_found = True
                    is_word_char = current_char in WORD_CHARS
            elif current_char.isspace() or is_word_char != (current_char in WORD_CHARS):
                break

    @undoable
    def _enter(self):
        self.delete_selection()

        y, x = self.cursor
        pad = self._pad
        pad.height += 1

        pad.canvas[y + 2 :] = pad.canvas[y + 1 : -1]
        pad.canvas[y + 1] = style_char(pad.default_char)

        len_line = self._line_lengths[y] - x
        if len_line > 0:
            pad.canvas[y + 1, :len_line] = pad.canvas[y, x : x + len_line]
            pad.canvas[y, x : x + len_line] = style_char(pad.default_char)

        self._line_lengths[y] = x
        self._line_lengths.insert(y + 1, len_line)

        if pad.width > self.port_width:
            pad.width = max(self.port_width, max(self._line_lengths) + 1)

        self.cursor = y + 1, 0

    @undoable
    def _tab(self):
        self.delete_selection()

        y, x = self.cursor
        pad = self._pad

        self._line_lengths[y] += 4
        if self._line_lengths[y] >= pad.width:
            pad.width = self._line_lengths[y] + 1

        pad.canvas[y, x + 4 :] = pad.canvas[y, x:-4]
        pad.canvas[y, x : x + 4] = style_char(pad.default_char)

        self.cursor = y, x + 4

    @undoable
    def _backspace(self):
        if not self.has_selection:
            self.select()
            self.move_cursor_left()
        self.delete_selection()

    @undoable
    def _delete(self):
        if not self.has_selection:
            self.select()
            self.move_cursor_right()
        self.delete_selection()

    def _left(self):
        if self.has_selection:
            select_start = self._selection_start
            self.unselect()
            self.cursor = select_start
        else:
            self.move_cursor_left()

    def _right(self):
        if self.has_selection:
            select_end = self._selection_end
            self.unselect()
            self.cursor = select_end
        else:
            self.move_cursor_right()

    def _ctrl_left(self):
        self.unselect()
        self.move_word_left()

    def _ctrl_right(self):
        self.unselect()
        self.move_word_right()

    def _up(self):
        if self.has_selection:
            select_start = self._selection_start
            self.unselect()
            self.cursor = select_start
        self.move_cursor_up()

    def _down(self):
        if self.has_selection:
            select_end = self._selection_end
            self.unselect()
            self.cursor = select_end
        self.move_cursor_down()

    def _pgup(self):
        if self.has_selection:
            select_start = self._selection_start
            self.unselect()
            self.cursor = select_start
        self.move_cursor_up(self.page_lines)

    def _pgdn(self):
        if self.has_selection:
            select_end = self._selection_end
            self.unselect()
            self.cursor = select_end
        self.move_cursor_down(self.page_lines)

    def _home(self):
        self.unselect()
        self.cursor = self.cursor.y, 0

    def _end(self):
        self.unselect()
        y = self.cursor.y
        self.cursor = y, self._line_lengths[y]

    def _shift_left(self):
        self.select()
        self.move_cursor_left()

    def _shift_right(self):
        self.select()
        self.move_cursor_right()

    def _shift_ctrl_left(self):
        self.select()
        self.move_word_left()

    def _shift_ctrl_right(self):
        self.select()
        self.move_word_right()

    def _shift_up(self):
        self.select()
        self.move_cursor_up()

    def _shift_down(self):
        self.select()
        self.move_cursor_down()

    def _shift_pgup(self):
        self.select()
        self.move_cursor_up(self.page_lines)

    def _shift_pgdn(self):
        self.select()
        self.move_cursor_down(self.page_lines)

    def _shift_home(self):
        self.select()
        self.cursor = self.cursor.y, 0

    def _shift_end(self):
        self.select()
        y = self.cursor.y
        self.cursor = y, self._line_lengths[y]

    def _escape(self):
        if self.has_selection:
            self.unselect()
            self._highlight_selection()
        else:
            self.blur()

    @undoable
    def _ascii(self, key):
        self.delete_selection()
        y, x = self.cursor
        pad = self._pad

        self._line_lengths[y] += 1
        if self._line_lengths[y] >= pad.width:
            pad.width = self._line_lengths[y] + 1

        pad.canvas[y, x + 1 :] = pad.canvas[y, x:-1]
        pad.canvas[y, x] = style_char(key)

        self.cursor = y, x + 1

    __HANDLERS = {
        (Key.Enter, Mods.NO_MODS): _enter,
        (Key.Tab, Mods.NO_MODS): _tab,
        (Key.Backspace, Mods.NO_MODS): _backspace,
        (Key.Delete, Mods.NO_MODS): _delete,
        (Key.Left, Mods.NO_MODS): _left,
        (Key.Right, Mods.NO_MODS): _right,
        (Key.Left, Mods(False, True, False)): _ctrl_left,
        (Key.Right, Mods(False, True, False)): _ctrl_right,
        (Key.Up, Mods.NO_MODS): _up,
        (Key.Down, Mods.NO_MODS): _down,
        (Key.PageUp, Mods.NO_MODS): _pgup,
        (Key.PageDown, Mods.NO_MODS): _pgdn,
        (Key.Home, Mods.NO_MODS): _home,
        (Key.End, Mods.NO_MODS): _end,
        (Key.Left, Mods(False, False, True)): _shift_left,
        (Key.Right, Mods(False, False, True)): _shift_right,
        (Key.Left, Mods(False, True, True)): _shift_ctrl_left,
        (Key.Right, Mods(False, True, True)): _shift_ctrl_right,
        (Key.Up, Mods(False, False, True)): _shift_up,
        (Key.Down, Mods(False, False, True)): _shift_down,
        (Key.PageUp, Mods(False, False, True)): _shift_pgup,
        (Key.PageDown, Mods(False, False, True)): _shift_pgdn,
        (Key.Home, Mods(False, False, True)): _shift_home,
        (Key.End, Mods(False, False, True)): _shift_end,
        (Key.Escape, Mods.NO_MODS): _escape,
        ("z", Mods(False, True, False)): undo,
        ("z", Mods(False, True, True)): redo,
    }

    def on_key(self, key_event: KeyEvent) -> bool | None:
        if not self.is_focused:
            return

        if key_event.mods == Mods.NO_MODS and len(key_event.key) == 1:
            self._ascii(key_event.key)
        elif handler := self.__HANDLERS.get(key_event):
            handler(self)
        else:
            return super().on_key(key_event)

        return True

    @undoable
    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        if not self.is_focused:
            return

        self.delete_selection()

        y, x = self.cursor
        pad = self._pad
        ll = self._line_lengths
        line_remaining = pad.canvas[y, x : ll[y]].copy()

        paste_lines = paste_event.paste.splitlines()
        if len(paste_lines) == 1:
            [paste] = paste_lines
            len_paste = wcswidth(paste)

            ll[y] += len_paste
            if ll[y] >= pad.width:
                pad.width = ll[y] + 1

            pad.add_str(paste, (y, x))
            pad.canvas[y, x + len_paste : ll[y]] = line_remaining

            self.cursor = y, x + len_paste
        else:
            first, *lines, last = paste_lines
            newlines = len(lines) + 1
            len_last = wcswidth(last)
            last_y = y + newlines

            pad.height += newlines
            pad.canvas[y + newlines + 1 :] = pad.canvas[y + 1 : -newlines]
            pad.canvas[y, x : ll[y]] = style_char(pad.default_char)

            ll[y] = x + wcswidth(first)
            for i, line in enumerate(lines, start=y + 1):
                ll.insert(i, wcswidth(line))
            ll.insert(last_y, len_last + wcswidth("".join(line_remaining["char"])))

            max_width = max(ll)
            if max_width >= pad.width:
                pad.width = max_width + 1

            pad.add_str(first, (y, x))
            for i, line in enumerate(lines, start=y + 1):
                pad.add_str(line.ljust(pad.width), (i, 0))

            pad.add_str(last, (last_y, 0))
            pad.canvas[last_y, len_last : ll[last_y]] = line_remaining
            pad.canvas[last_y, ll[last_y] :] = style_char(pad.default_char)

            self.cursor = last_y, len_last

        return True

    def grab(self, mouse_event):
        if mouse_event.button is MouseButton.LEFT and self._pad.collides_point(
            mouse_event.position
        ):
            super().grab(mouse_event)

            y, x = self._pad.to_local(mouse_event.position)
            x = min(x, self._line_lengths[y])

            if not mouse_event.mods.shift:
                self.unselect()

            self.cursor = y, x
            self.select()  # Need at least an empty selection for `grab_update`.

    def grab_update(self, mouse_event: MouseEvent):
        if self._pad.collides_point(mouse_event.position):
            y, x = self._pad.to_local(mouse_event.position)
            x = min(x, self._line_lengths[y])
            self.cursor = y, x
        else:
            cy, cx = self.cursor
            y, x = self.to_local(mouse_event.position)
            h, w = self.size

            if y < 0:
                self.move_cursor_up()
            elif y >= h:
                self.move_cursor_down()

            if x < 0:
                if cx > 0:
                    self.move_cursor_left()
            elif x >= w:
                if cx < self._line_lengths[cy]:
                    self.move_cursor_right()

    def ungrab(self, mouse_event):
        super().ungrab(mouse_event)
        if self._selection_start == self._selection_end:
            self.unselect()
