from wcwidth import wcswidth

from ..clamp import clamp
from ..colors import lerp_colors, WHITE, ColorPair
from ..io import Key, KeyEvent, Mods, MouseButton, MouseEvent, PasteEvent
from .behaviors.focus_behavior import FocusBehavior
from .behaviors.themable import Themable
from .scroll_view import ScrollView
from .text_widget import TextWidget, Point

# TODO: Add an Undo stack.


class TextPad(Themable, FocusBehavior, ScrollView):
    """
    A text-pad widget for multiline editable text.

    Supports pasting, mouse selection, and cursor navigation.

    Parameters
    ----------
    ptf_on_focus : bool, default: True
        Pull widget to front when it gains focus.
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
        If False, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If True, widget will not be pulled to front when grabbed.
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
    text : str
        The textpad's text.
    ptf_on_focus : bool
        Pull widget to front when it gains focus.
    is_focused : bool
        Return True if widget has focus.
    any_focused : bool
        Return True if any widget has focus.
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
        If False, grabbable behavior is disabled.
    disable_ptf : bool
        If True, widget will not be pulled to front when grabbed.
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
    update_geometry:
        Called when parent is resized. Applies size and pos hints.
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
        Yield all descendents (or ancestors if `reverse` is True).
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

    Notes
    -----
    The cursor for text input widgets is the real terminal cursor. Because the terminal cursor isn't subject to
    the painter's algorithm for rendering widgets, it's possible for a text input widget to be covered by
    another widget, but the cursor still be visible. This may be resolved in the future by attaching clipping
    regions to widgets.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._cursor = self._prev_cursor = Point(0, 0)
        self._last_x = None
        self._selection_start = self._selection_end = None
        self._line_lengths = [0]

        self._pad = TextWidget(size=(1, 1))

        self.update_theme()

    def update_theme(self):
        primary = self.color_theme.primary_color_pair
        backgound = primary.bg_color

        self._pad.colors[:] = primary
        self._pad.default_color_pair = primary
        self.background_color_pair = ColorPair.from_colors(backgound, backgound)

        self.selection_hightlight = lerp_colors(backgound, WHITE, 1/10)
        self.line_highlight = lerp_colors(backgound, WHITE, 1/40)

        self._highlight_selection()

    def on_add(self):
        super().on_add()

        self.view = self._pad

        # To keep real cursor's position in-sync with virtual cursor's absolute position,
        # subscribe to every ancestor's `pos` property.

        self.subscribe(self._pad, "pos", self._update_cursor)
        self.subscribe(self, "pos", self._update_cursor)

        for ancestor in self.walk(reverse=True):
            if ancestor is not self.root:
                self.subscribe(ancestor, "pos", self._update_cursor)

        self.focus()

    def on_remove(self):
        super().on_remove()

        self.view = None

        self.unsubscribe(self._pad, "pos")
        self.unsubscribe(self, "pos")

        for ancestor in self.walk(reverse=True):
            if ancestor is not self.root:
                self.unsubscribe(ancestor, "pos")

    def on_size(self):
        super().on_size()

        if self.width > self._pad.width:
                self._pad.width = self.width
        elif self.width < self._pad.width:
            self._pad.width = max(self.width, max(self._line_lengths) + 1)

        self._highlight_selection()

    def _update_cursor(self):
        """
        Move or hide terminal cursor to match position of `self.cursor`.
        """
        if not self.root:
            return

        py, px = self._pad.absolute_pos
        cy, cx = self._cursor
        cursor = y, x = py + cy, px + cx
        out = self.root.env_out

        if (
            self.is_focused
            and self._pad.collides_point(cursor)
            and not (self.show_vertical_bar and self._vertical_bar.collides_point(cursor))
            and not (self.show_horizontal_bar and self._horizontal_bar.collides_point(cursor))
        ):
            out._buffer.append(f"\x1b[{y + 1};{x + 1}H")  # Move cursor.
            out.show_cursor()
        else:
            out.hide_cursor()

    on_focus = _update_cursor

    on_blur = _update_cursor

    @property
    def text(self) -> str:
        return "\n".join(
            "".join(row[:nchars])
            for row, nchars in zip(self._pad.canvas, self._line_lengths)
        )

    @text.setter
    def text(self, text: str):
        lines = text.splitlines()
        self._line_lengths = list(map(wcswidth, lines))

        pad = self._pad
        pad.canvas[:] = " "
        pad.height = len(lines)
        pad.width = max(max(self._line_lengths) + 1, self.width)

        for i, line in enumerate(lines):
            pad.add_text(line, row=i)

    @property
    def cursor(self) -> Point:
        return self._cursor

    @cursor.setter
    def cursor(self, cursor: Point):
        """
        After setting cursor position, move pad so that cursor is visible.
        """
        y, x = cursor
        self._prev_cursor = self._cursor
        self._cursor = Point(y, x)

        max_y = self.height - (self.show_horizontal_bar and 1) - 1
        if (rel_y := y + self._pad.y) > max_y:
            self._scroll_down(rel_y - max_y)
        elif rel_y < 0:
            self._scroll_up(-rel_y)

        max_x = self.width - (self.show_vertical_bar and 2) - 1
        if (rel_x := x + self._pad.x) > max_x:
            self._scroll_right(rel_x - max_x)
        elif rel_x < 0:
            self._scroll_left(-rel_x)

        self._update_cursor()
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

        pad.canvas[sy, sx: len_start] = pad.canvas[ey, ex: ex + len_end]
        pad.canvas[sy, len_start:] = pad.default_char

        remaining = pad.canvas[ey + 1:]
        pad.canvas[sy + 1: sy + 1 + len(remaining)] = remaining
        pad.height -= ey - sy
        del self._line_lengths[sy + 1: ey + 1]

        self.unselect()

        self.cursor = sy, sx

    def _highlight_selection(self):
        colors = self._pad.colors
        colors[:] = self._pad.default_color_pair

        if self._selection_start != self._selection_end:
            sy, sx = self._selection_start
            ey, ex = self._selection_end
            highlight = self.selection_hightlight
            ll = self._line_lengths

            if ey > sy:
                colors[sy, sx: ll[sy], 3:] = highlight
                colors[ey, :ex, 3:] = highlight
                for i in range(sy + 1, ey):
                    colors[i, :ll[i], 3:] = highlight
            else:
                colors[sy, sx: ex, 3:] = highlight
        else:  # If no selection or selection is empty, add line highlight.
            colors[self.cursor.y, :, 3:] = self.line_highlight

    def _update_selection(self):
        if self.has_selection:
            if self._prev_cursor == self._selection_start:
                self._selection_start = self.cursor
            elif self._prev_cursor == self._selection_end:
                self._selection_end = self.cursor

            if self._selection_start > self._selection_end:
                self._selection_start, self._selection_end = self._selection_end, self._selection_start

        self._highlight_selection()

    def move_cursor_left(self, n: int=1):
        self._last_x = None
        y, x = self._cursor

        while n > 0:
            to_start = clamp(n, 0, x)
            n -= to_start
            x -= to_start

            if y == 0:
                break
            elif n > 0:
                y -= 1
                n -= 1
                x = self._line_lengths[y]

        self.cursor = y, x

    def move_cursor_right(self, n: int=1):
        self._last_x = None
        y, x = self._cursor

        while n > 0:
            to_end = clamp(n, 0, self._line_lengths[y] - x)
            n -= to_end
            x += to_end

            if y == self.end_text_point.y:
                break
            elif n > 0:
                y += 1
                n -= 1
                x = 0

        self.cursor = y, x

    def move_cursor_up(self, n: int=1):
        y, x = self._cursor

        if self._last_x is None or y == x == 0:
            self._last_x = x

        if y > 0:
            y = max(0, y - n)
            x = min(self._last_x, self._line_lengths[y])
        else:
            x = 0

        self.cursor = y, x

    def move_cursor_down(self, n: int=1):
        y, x = self._cursor
        ey, ex = self.end_text_point

        if self._last_x is None or y == ey and x == ex:
            self._last_x = x

        if y < ey:
            y = min(ey, y + n)
            x = min(self._last_x, self._line_lengths[y])
        else:
            x = ex

        self.cursor = y, x

    def _enter(self):
        self.delete_selection()

        y, x = self.cursor
        pad = self._pad
        pad.height += 1

        pad.canvas[y + 2:] = pad.canvas[y + 1: -1]
        pad.canvas[y + 1] = pad.default_char

        len_line = self._line_lengths[y] - x
        if len_line > 0:
            pad.canvas[y + 1, :len_line] = pad.canvas[y, x: x + len_line]
            pad.canvas[y, x: x + len_line] = pad.default_char

        self._line_lengths[y] = x
        self._line_lengths.insert(y + 1, len_line)

        if pad.width > self.width:
            pad.width = max(self.width, max(self._line_lengths) + 1)

        self.cursor = y + 1, 0

    def _tab(self):
        self.delete_selection()

        y, x = self.cursor
        pad = self._pad

        self._line_lengths[y] += 4
        if self._line_lengths[y] >= pad.width:
            pad.width = self._line_lengths[y] + 1

        pad.canvas[y, x + 4:] = pad.canvas[y, x: -4]
        pad.canvas[y, x: x + 4] = pad.default_char

        self.cursor = y, x + 4

    def _backspace(self):
        if not self.has_selection:
            self.select()
            y, x = self.cursor
            if x > 0:
                self._selection_start = y, x - 1
            elif y > 0:
                self._selection_start = y - 1, self._line_lengths[y - 1]

        self.delete_selection()

    def _delete(self):
        if not self.has_selection:
            self.select()
            y, x = self.cursor
            if x < self._line_lengths[y]:
                self._selection_end = y, x + 1
            elif y < self.end_text_point.y:
                self._selection_end = y + 1, 0

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

    def _ascii(self, key):
        self.delete_selection()
        y, x = self.cursor
        pad = self._pad

        self._line_lengths[y] += 1
        if self._line_lengths[y] >= pad.width:
            pad.width = self._line_lengths[y] + 1

        pad.canvas[y, x + 1:] = pad.canvas[y, x: -1]
        pad.canvas[y, x] = key

        self.cursor = y, x + 1

    __HANDLERS = {
        (Key.Enter, Mods.NO_MODS): _enter,
        (Key.Tab, Mods.NO_MODS): _tab,
        (Key.Backspace, Mods.NO_MODS): _backspace,
        (Key.Delete, Mods.NO_MODS): _delete,
        (Key.Left, Mods.NO_MODS): _left,
        (Key.Right, Mods.NO_MODS): _right,
        (Key.Up, Mods.NO_MODS): _up,
        (Key.Down, Mods.NO_MODS): _down,
        (Key.PageUp, Mods.NO_MODS): _pgup,
        (Key.PageDown, Mods.NO_MODS): _pgdn,
        (Key.Home, Mods.NO_MODS): _home,
        (Key.End, Mods.NO_MODS): _end,
        (Key.Left, Mods(False, False, True)): _shift_left,
        (Key.Right, Mods(False, False, True)): _shift_right,
        (Key.Up, Mods(False, False, True)): _shift_up,
        (Key.Down, Mods(False, False, True)): _shift_down,
        (Key.PageUp, Mods(False, False, True)): _shift_pgup,
        (Key.PageDown, Mods(False, False, True)): _shift_pgdn,
        (Key.Home, Mods(False, False, True)): _shift_home,
        (Key.End, Mods(False, False, True)): _shift_end,
        (Key.Escape, Mods.NO_MODS): _escape,
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

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        if not self.is_focused:
            return

        self.delete_selection()

        y, x = self.cursor
        pad = self._pad
        ll = self._line_lengths
        line_remaining = pad.canvas[y, x: ll[y]].copy()

        paste_lines = paste_event.paste.splitlines()
        if len(paste_lines) == 1:
            [paste] = paste_lines
            len_paste = wcswidth(paste)

            ll[y] += len_paste
            if ll[y] >= pad.width:
                pad.width = ll[y] + 1

            pad.add_text(paste, row=y, column=x)
            pad.canvas[y, x + len_paste: ll[y]] = line_remaining

            self.cursor = y, x + len_paste
        else:
            first, *lines, last = paste_lines
            newlines = len(lines) + 1
            len_last = wcswidth(last)

            pad.height += newlines
            pad.canvas[y + newlines + 1:] = pad.canvas[y + 1: -newlines]
            pad.canvas[y, x: ll[y]] = pad.default_char

            ll[y] = x + wcswidth(first)
            for i, line in enumerate(lines, start=y + 1):
                ll.insert(i, wcswidth(line))
            ll.insert(i + 1, len_last + len(line_remaining))

            max_width = max(ll)
            if max_width >= pad.width:
                pad.width = max_width + 1

            pad.add_text(first, row=y, column=x)
            for i, line in enumerate(lines, start=y + 1):
                pad.add_text(line.ljust(pad.width), row=i)

            pad.add_text(last, row=i + 1)
            pad.canvas[i + 1, len_last: ll[i + 1]] = line_remaining
            pad.canvas[i + 1, ll[i + 1]:] = pad.default_char

            self.cursor = i + 1, len_last

        return True

    def grab(self, mouse_event):
        if mouse_event.button is MouseButton.LEFT and self._pad.collides_point(mouse_event.position):
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
