"""A textbox gadget for single-line editable text."""
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray
from wcwidth import wcswidth

from ..io import Key, KeyEvent, Mods, MouseButton, MouseEvent, PasteEvent
from .behaviors.focusable import Focusable
from .behaviors.grabbable import Grabbable
from .behaviors.themable import Themable
from .gadget import Gadget
from .gadget_base import (
    Char,
    GadgetBase,
    Point,
    PosHint,
    PosHintDict,
    Region,
    Size,
    SizeHint,
    SizeHintDict,
    coerce_char,
)
from .text import Text, style_char
from .text_tools import is_word_char

__all__ = [
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "Textbox",
]


class Textbox(Themable, Focusable, Grabbable, GadgetBase):
    r"""
    A textbox gadget for single-line editable text.

    Supports pasting, mouse selection, and cursor navigation.

    Parameters
    ----------
    enter_callback : Callable[[Textbox], None] | None, default: None
        If provided, called when textbox has focus and `enter` is pressed.
        The gadget will be passed as first argument to the callback.
    placeholder : str, default: ""
        Placeholder text for textbox.
    hide_input : bool, default: False
        If true, input is hidden with :attr:`hide_char`.
    hide_char : NDArray[Char] | str, default: "*"
        Character to hide input when :attr:`hide_input` is true.
    max_chars : int | None, default: None
        Maximum allowed number of characters in textbox.
    is_grabbable : bool, default: True
        If false, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton, default: MouseButton.LEFT
        Mouse button used for grabbing.
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
    text : str
        The textbox's text.
    cursor : int
        The cursor column.
    is_selecting : bool
        Whether there is a selection.
    has_nonempty_selection : bool
        Whether selection is non-empty.
    placeholder : str
        Placeholder text for textbox.
    hide_input : bool
        If true, input is hidden with :attr:`hide_char`.
    hide_char : NDArray[Char]
        Character to hide input when :attr:`hide_input` is true.
    max_chars : int | None
        Maximum allowed number of characters in textbox.
    is_focused : bool
        Return true if gadget has focus.
    any_focused : bool
        Return true if any gadget has focus.
    is_grabbable : bool
        If false, grabbable behavior is disabled.
    disable_ptf : bool
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton
        Mouse button used for grabbing.
    is_grabbed : bool
        True if gadget is grabbed.
    mouse_dyx : Point
        Last change in mouse position.
    mouse_dy : int
        Last vertical change in mouse position.
    mouse_dx : int
        Last horizontal change in mouse position.
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
    undo():
        Undo previous edit.
    redo():
        Redo previous undo.
    select():
        Start a new selection at cursor if none.
    unselect():
        Unselect current selection.
    delete_selection():
        Delete current selection.
    move_cursor_left(n):
        Move cursor left `n` characters.
    move_cursor_right(n):
        Move cursor right `n` characters.
    move_word_left():
        Move cursor a word left.
    move_word_right():
        Move cursor a word right.
    update_theme():
        Paint the gadget with current theme.
    focus():
        Focus gadget.
    blur():
        Un-focus gadget.
    focus_next():
        Focus next focusable gadget.
    focus_previous():
        Focus previous focusable gadget.
    on_focus():
        Update gadget when it gains focus.
    on_blur():
        Update gadget when it loses focus.
    grab(mouse_event):
        Grab the gadget.
    ungrab(mouse_event):
        Ungrab the gadget.
    grab_update(mouse_event):
        Update gadget with incoming mouse events while grabbed.
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

    def __init__(
        self,
        *,
        enter_callback: Callable[["Textbox"], None] | None = None,
        placeholder: str = "",
        hide_input: bool = False,
        hide_char: NDArray[Char] | str = "*",
        max_chars: int | None = None,
        is_grabbable: bool = True,
        disable_ptf: bool = False,
        mouse_button: MouseButton = MouseButton.LEFT,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            is_grabbable=is_grabbable,
            disable_ptf=disable_ptf,
            mouse_button=mouse_button,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self._selection_start = self._selection_end = None
        self._line_length = 0
        self._undo_stack = []
        self._redo_stack = []
        self._undo_buffer = []
        self._undo_buffer_type = "add"

        self._placeholder_gadget = Text()
        self._placeholder_gadget.set_text(placeholder)
        self._cursor = Gadget(size=(1, 1), is_enabled=False, is_transparent=True)
        self._box = Text(size=self.size)
        self._box.add_gadgets(self._placeholder_gadget, self._cursor)

        self.add_gadgets(self._box)

        self.enter_callback = enter_callback
        """
        If provided, called when textbox has focus and `enter` is pressed.
        The gadget will be passed as first argument to the callback.
        """
        self.placeholder = placeholder
        """Placeholder text for textbox."""
        self.hide_input = hide_input
        """If true, input is hidden with :attr:`hide_char`."""
        self.hide_char = hide_char
        self.max_chars = max_chars
        """Maximum allowed number of characters in textbox."""

    @property
    def hide_char(self) -> NDArray[Char]:
        """Character to hide input when :attr:`hide_input` is true."""
        return self._hide_char

    @hide_char.setter
    def hide_char(self, char: NDArray | str):
        self._hide_char = coerce_char(char, style_char("*"))

    def update_theme(self):
        """Paint the gadget with current theme."""
        primary = self.color_theme.textbox_primary

        self._placeholder_gadget.colors[:] = self.color_theme.textbox_placeholder
        self._box.colors[:] = primary
        self._box.default_color_pair = primary
        self._cursor.background_color_pair = primary.reversed()

        self._highlight_selection()

    def on_size(self):
        """Resize and reposition children on resize."""
        self._box.width = max(self.width, self._line_length + 1)
        if self._box.x + self._line_length < self.width:
            self._box.x = min(0, self.width - self._line_length)
        self.cursor = self.cursor

    def on_focus(self):
        """Show cursor and select all text on focus."""
        self._cursor.is_enabled = True
        if self._line_length > 0:
            self._ctrl_a()

    def on_blur(self):
        """Hide cursor on blur."""
        self._cursor.is_enabled = False

    def render(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        """Render visible region of gadget into root's `canvas` and `colors` arrays."""
        super().render(canvas, colors)
        if self.hide_input:
            hider_region = self._box.region & Region.from_rect(
                self._box.absolute_pos, (1, self._line_length)
            )
            for rect in hider_region.rects():
                canvas[rect.to_slices()] = self.hide_char

    @property
    def placeholder(self) -> str:
        """Placeholder text for textbox."""
        return self._placeholder

    @placeholder.setter
    def placeholder(self, placeholder: str):
        self._placeholder = placeholder
        self._placeholder_gadget.set_text(placeholder)
        self._placeholder_gadget.colors[:] = self.color_theme.textbox_placeholder
        self._placeholder_gadget.is_enabled = self._line_length == 0 and bool(
            placeholder
        )

    def _move_undo_buffer_to_stack(self, buffer_type=None):
        self._undo_buffer_type = buffer_type
        if self._undo_buffer:
            self._undo_stack.append(self._undo_buffer)
            self._undo_buffer = []
            self._redo_stack.clear()

    def undo(self):
        """Undo previous edit."""
        self._move_undo_buffer_to_stack()
        if self._undo_stack:
            redo = []
            for func, args, selection_start, selection_end, cursor in reversed(
                self._undo_stack.pop()
            ):
                redo.append(func(*args))
                self._selection_start = selection_start
                self._selection_end = selection_end
                self.cursor = cursor
            self._redo_stack.append(redo)

    def redo(self):
        """Redo previous undo."""
        if self._redo_stack and not self._undo_buffer:
            undo = []
            for func, args, selection_start, selection_end, cursor in reversed(
                self._redo_stack.pop()
            ):
                undo.append(func(*args))
                self._selection_start = selection_start
                self._selection_end = selection_end
                self.cursor = cursor
            self._undo_stack.append(undo)

    @property
    def text(self) -> str:
        """The textbox's text."""
        return "".join(self._box.canvas["char"][0, : self._line_length])

    @text.setter
    def text(self, text: str):
        text = text.replace("\n", " ")[: self.max_chars]
        self.unselect()
        self._del_text(0, self._line_length)
        self._add_text(0, text)
        self._redo_stack.clear()
        self._undo_stack.clear()
        self._undo_buffer.clear()
        self.cursor = self._line_length

    @property
    def cursor(self) -> int:
        """The cursor column."""
        return self._cursor.x

    @cursor.setter
    def cursor(self, cursor: int):
        """After setting cursor position, move textbox so that cursor is visible."""
        self._cursor.x = cursor
        if self._line_length == 0 and self._placeholder:
            self._placeholder_gadget.is_enabled = True
        else:
            self._placeholder_gadget.is_enabled = False

        max_x = self.width - 1
        rel_x = cursor + self._box.x
        if rel_x > max_x:
            self._box.x -= rel_x - max_x
        elif rel_x < 0:
            self._box.x -= rel_x

        if self.is_selecting:
            self._selection_end = self.cursor

        self._highlight_selection()

    def _highlight_selection(self):
        colors = self._box.colors
        colors[:] = self._box.default_color_pair

        if self._selection_start != self._selection_end:
            if self._selection_start > self._selection_end:
                start = self._selection_end
                end = self._selection_start
            else:
                start = self._selection_start
                end = self._selection_end

            colors[0, start:end] = self.color_theme.textbox_selection_highlight

    @property
    def is_selecting(self) -> bool:
        """Whether there is a selection."""
        return self._selection_start is not None and self._selection_end is not None

    @property
    def has_nonempty_selection(self) -> bool:
        """Whether selection is non-empty."""
        return self.is_selecting and self._selection_start != self._selection_end

    def select(self):
        """Start a new selection at cursor if none."""
        if not self.is_selecting:
            self._selection_start = self._selection_end = self.cursor

    def unselect(self):
        """Unselect current selection."""
        self._selection_start = self._selection_end = None

    def delete_selection(self):
        """Delete current selection."""
        if self.has_nonempty_selection:
            return self._del_text(self._selection_start, self._selection_end)

    def _del_text(self, start: int, end: int):
        if start > end:
            start, end = end, start

        if end > self._line_length:
            # ! If we ended up here, something went wrong.
            end = self._line_length

        contents = "".join(self._box.canvas["char"][0, start:end])
        selection_start = self._selection_start
        selection_end = self._selection_end
        cursor = self.cursor

        len_end = self._line_length - end
        self._line_length = start + len_end

        box = self._box
        box.canvas[0, start : self._line_length] = box.canvas[0, end : end + len_end]
        box.canvas[0, self._line_length :] = box.default_char

        self.unselect()
        self.cursor = start

        return self._add_text, [start, contents], selection_start, selection_end, cursor

    def _add_text(self, x: int, text: str):
        selection_start = self._selection_start
        selection_end = self._selection_end
        cursor = self.cursor

        text = text.replace("\n", " ")
        box = self._box
        box_text = (
            f"{''.join(box.canvas['char'][0, :x])}"
            f"{text}"
            f"{''.join(box.canvas['char'][0, x : self._line_length])}"
        )[: self.max_chars]

        box_width = self._line_length = wcswidth(box_text)
        if box_width >= box.width:
            box.width = box_width + 1

        box.add_str(box_text)
        box.canvas[0, box_width:] = box.default_char

        self.cursor = min(box_width, x + wcswidth(text))
        return self._del_text, [x, self.cursor], selection_start, selection_end, cursor

    def move_cursor_left(self, n: int = 1):
        """Move cursor left `n` characters."""
        text_before_cursor = "".join(self._box.canvas["char"][0, : self.cursor])
        nchars_before_cursor = len(text_before_cursor)
        if n <= nchars_before_cursor:
            self.cursor = wcswidth(text_before_cursor[:-n])
        else:
            self.cursor = 0

    def move_cursor_right(self, n: int = 1):
        """Move cursor right `n` characters."""
        text_after_cursor = "".join(
            self._box.canvas["char"][0, self.cursor : self._line_length]
        )
        nchars_after_cursor = len(text_after_cursor)
        if n <= nchars_after_cursor:
            self.cursor += wcswidth(text_after_cursor[:n])
        else:
            self.cursor = self._line_length

    def move_word_left(self):
        """Move cursor a word left."""
        last_x = self.cursor
        first_char_found = False
        while True:
            self.move_cursor_left()
            if self.cursor == last_x:
                break

            last_x = self.cursor

            current_char = self._box.canvas[0, self.cursor]["char"]
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
        last_x = self.cursor
        first_char_found = False
        while True:
            self.move_cursor_right()
            if self.cursor == last_x:
                break

            last_x = self.cursor

            current_char = self._box.canvas[0, self.cursor]["char"]
            if not first_char_found:
                if not current_char.isspace():
                    first_char_found = True
                    char_is_word_char = is_word_char(current_char)
            elif current_char.isspace() or char_is_word_char != is_word_char(
                current_char
            ):
                break

    def _enter(self):
        if self.enter_callback is not None:
            self.enter_callback(self)

    def _backspace(self):
        if self.has_nonempty_selection:
            self._move_undo_buffer_to_stack("del")
            self._undo_buffer.append(self.delete_selection())
        else:
            if self._undo_buffer_type != "del":
                self._move_undo_buffer_to_stack("del")

            end = self.cursor
            self.move_cursor_left()
            start = self.cursor
            self.cursor = end
            if start != end:
                self._undo_buffer.append(self._del_text(start, end))

    def _delete(self):
        if self.has_nonempty_selection:
            self._move_undo_buffer_to_stack("del")
            self._undo_buffer.append(self.delete_selection())
        else:
            if self._undo_buffer_type != "del":
                self._move_undo_buffer_to_stack("del")

            start = self.cursor
            self.move_cursor_right()
            end = self.cursor
            self.cursor = start
            if start != end:
                self._undo_buffer.append(self._del_text(start, end))

    def _left(self):
        if self.has_nonempty_selection:
            select_start = min(self._selection_start, self._selection_end)
            self.unselect()
            self.cursor = select_start
        else:
            self.unselect()
            self.move_cursor_left()

    def _right(self):
        if self.has_nonempty_selection:
            select_end = max(self._selection_start, self._selection_end)
            self.unselect()
            self.cursor = select_end
        else:
            self.unselect()
            self.move_cursor_right()

    def _ctrl_left(self):
        self.unselect()
        self.move_word_left()

    def _ctrl_right(self):
        self.unselect()
        self.move_word_right()

    def _ctrl_a(self):
        """Select all."""
        self._selection_start = 0
        self._selection_end = self._line_length
        self.cursor = self._line_length

    def _ctrl_d(self):
        """Select word."""
        self.unselect()
        last_x = self.cursor
        while True:
            self.move_cursor_left()
            if last_x == self.cursor:
                break
            if not is_word_char(self._box.canvas[0, self.cursor]["char"]):
                self.move_cursor_right()
                break
            last_x = self.cursor

        self.select()
        last_x = self.cursor
        while True:
            if not is_word_char(self._box.canvas[0, self.cursor]["char"]):
                break
            self.move_cursor_right()
            if last_x == self.cursor:
                break
            last_x = self.cursor

    def _home(self):
        self.unselect()
        self.cursor = 0

    def _end(self):
        self.unselect()
        self.cursor = self._line_length

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

    def _shift_home(self):
        self.select()
        self.cursor = 0

    def _shift_end(self):
        self.select()
        self.cursor = self._line_length

    def _escape(self):
        if self.has_nonempty_selection:
            self.unselect()
            self._highlight_selection()
        else:
            self.unselect()
            self.blur()

    def _ascii(self, key):
        if self.has_nonempty_selection:
            self._move_undo_buffer_to_stack("add")
            self._undo_buffer.append(self.delete_selection())

        if (
            self.max_chars is None
            or (self._box.canvas["char"][0, : self._line_length] != "").sum()
            < self.max_chars
        ):
            if self._undo_buffer_type != "add":
                self._move_undo_buffer_to_stack("add")
            self._undo_buffer.append(self._add_text(self.cursor, key))

    __HANDLERS = {
        (Key.Enter, Mods.NO_MODS): _enter,
        (Key.Backspace, Mods.NO_MODS): _backspace,
        (Key.Delete, Mods.NO_MODS): _delete,
        (Key.Left, Mods.NO_MODS): _left,
        (Key.Right, Mods.NO_MODS): _right,
        (Key.Left, Mods(False, True, False)): _ctrl_left,
        (Key.Right, Mods(False, True, False)): _ctrl_right,
        (Key.Home, Mods.NO_MODS): _home,
        (Key.End, Mods.NO_MODS): _end,
        (Key.Left, Mods(False, False, True)): _shift_left,
        (Key.Right, Mods(False, False, True)): _shift_right,
        (Key.Left, Mods(False, True, True)): _shift_ctrl_left,
        (Key.Right, Mods(False, True, True)): _shift_ctrl_right,
        (Key.Home, Mods(False, False, True)): _shift_home,
        (Key.End, Mods(False, False, True)): _shift_end,
        (Key.Escape, Mods.NO_MODS): _escape,
        ("z", Mods(False, True, False)): undo,
        ("z", Mods(False, True, True)): redo,
        ("r", Mods(False, True, False)): redo,
        ("a", Mods(False, True, False)): _ctrl_a,
        ("d", Mods(False, True, False)): _ctrl_d,
    }

    def on_key(self, key_event: KeyEvent) -> bool | None:
        """Process key press."""
        if not self.is_focused:
            return super().on_key(key_event)

        if key_event.mods == Mods.NO_MODS and len(key_event.key) == 1:
            self._ascii(key_event.key)
        elif handler := self.__HANDLERS.get(key_event):
            handler(self)
        else:
            return super().on_key(key_event)

        return True

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        """Add paste to textbox."""
        if not self.is_focused:
            return

        self._move_undo_buffer_to_stack()
        undos = []
        if undo := self.delete_selection():
            undos.append(undo)
        undos.append(self._add_text(self.cursor, paste_event.paste))
        self._undo_stack.append(undos)
        self._redo_stack.clear()

        return True

    def grab(self, mouse_event):
        """Start selection on grab."""
        if mouse_event.button is MouseButton.LEFT and self._box.collides_point(
            mouse_event.position
        ):
            super().grab(mouse_event)

            _, x = self._box.to_local(mouse_event.position)

            if not mouse_event.mods.shift:
                self.unselect()

            self.cursor = min(x, self._line_length)
            self.select()  # Need at least an empty selection for `grab_update`.

    def grab_update(self, mouse_event: MouseEvent):
        """Update selection on grab update."""
        if self._box.collides_point(mouse_event.position):
            _, x = self._box.to_local(mouse_event.position)
            self.cursor = min(x, self._line_length)
        else:
            _, x = self.to_local(mouse_event.position)

            if x < 0:
                self.move_cursor_left()
            elif x >= self.width:
                self.move_cursor_right()

    def ungrab(self, mouse_event):
        """Clear an empty selection on ungrab."""
        super().ungrab(mouse_event)
        if self._selection_start == self._selection_end:
            self.unselect()
