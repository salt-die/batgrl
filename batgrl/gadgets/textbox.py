"""
A textbox gadget for single-line editable text.
"""
from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray
from wcwidth import wcswidth

from ..colors import ColorPair
from ..io import Key, KeyEvent, Mods, MouseButton, MouseEvent, PasteEvent
from .behaviors.focusable import Focusable
from .behaviors.grabbable import Grabbable
from .behaviors.themable import Themable
from .gadget import (
    Char,
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Region,
    Size,
    SizeHint,
    SizeHintDict,
)
from .text import Text, style_char

__all__ = [
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "Textbox",
]

WORD_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_")


class Textbox(Themable, Focusable, Grabbable, Gadget):
    """
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
    hide_char : str, default: "*"
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
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the gadget if the gadget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the gadget if the gadget is not transparent.

    Attributes
    ----------
    text : str
        The textbox's text.
    placeholder : str
        Placeholder text for textbox.
    hide_input : bool
        If true, input is hidden with :attr:`hide_char`.
    hide_char : str
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
    background_char : str | None
        The background character of the gadget if the gadget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Gadget | None
        Parent gadget.
    children : list[Gadget]
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
    update_theme:
        Paint the gadget with current theme.
    focus:
        Focus gadget.
    blur:
        Un-focus gadget.
    focus_next:
        Focus next focusable gadget.
    focus_previous:
        Focus previous focusable gadget.
    on_focus:
        Called when gadget is focused.
    on_blur:
        Called when gadget loses focus.
    grab:
        Grab the gadget.
    ungrab:
        Ungrab the gadget.
    grab_update:
        Update gadget with incoming mouse events while grabbed.
    on_size:
        Called when gadget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of gadget.
    collides_gadget:
        True if other is within gadget's bounding box.
    add_gadget:
        Add a child gadget.
    add_gadgets:
        Add multiple child gadgets.
    remove_gadget:
        Remove a child gadget.
    pull_to_front:
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root:
        Yield all descendents of root gadget.
    walk:
        Yield all descendents (or ancestors if `reverse` is True).
    subscribe:
        Subscribe to a gadget property.
    unsubscribe:
        Unsubscribe to a gadget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a gadget property over time.
    on_add:
        Called after a gadget is added to gadget tree.
    on_remove:
        Called before gadget is removed from gadget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this gadget and all descendents.
    """

    def __init__(
        self,
        *,
        enter_callback: Callable[["Textbox"], None] | None = None,
        placeholder: str = "",
        hide_input: bool = False,
        hide_char: str = "*",
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
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
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
            background_char=background_char,
            background_color_pair=background_color_pair,
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
        self._box = Text(size=self._placeholder_gadget.size)
        self._box.add_gadgets(self._placeholder_gadget, self._cursor)

        self.add_gadgets(self._box)

        self.enter_callback = enter_callback
        self.placeholder = placeholder
        self.hide_input = hide_input
        self.hide_char = hide_char
        self.max_chars = max_chars

    def update_theme(self):
        primary = self.color_theme.textbox_primary

        self.background_color_pair = primary
        self._placeholder_gadget.colors[:] = self.color_theme.textbox_placeholder
        self._box.colors[:] = primary
        self._box.default_color_pair = primary
        self._cursor.background_color_pair = primary.reversed()

        self._highlight_selection()

    def on_size(self):
        self._input_hider.size = self.size

        if self.width > self._box.width:
            self._box.width = self.width
        elif self.width < self._box.width:
            self._box.width = max(self.width, self._line_length + 1)
        self._highlight_selection()

    def on_focus(self):
        self._cursor.is_enabled = True

    def on_blur(self):
        self._cursor.is_enabled = False

    def render(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        super().render(canvas, colors)
        if self.hide_input:
            hider_region = self._box.region & Region.from_rect(
                self._box.absolute_pos, (1, self._line_length)
            )
            for rect in hider_region.rects():
                canvas[rect.to_slices()] = style_char(self.hide_char)

    @property
    def placeholder(self) -> str:
        return self._placeholder

    @placeholder.setter
    def placeholder(self, placeholder: str):
        self._placeholder = placeholder
        self._placeholder_gadget.set_text(placeholder)
        self._placeholder_gadget.colors[:] = self.color_theme.textbox_placeholder
        if self._line_length == 0 and placeholder:
            self._placeholder_gadget.is_enabled = True
        else:
            self._placeholder_gadget.is_enabled = False

    def _move_undo_buffer_to_stack(self, buffer_type=None):
        self._undo_buffer_type = buffer_type
        if self._undo_buffer:
            self._undo_stack.append(self._undo_buffer)
            self._undo_buffer = []
            self._redo_stack.clear()

    def undo(self):
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
        return "".join(self._box.canvas["char"][0, : self._line_length])

    @text.setter
    def text(self, text: str):
        self._redo_stack.clear()
        self._undo_stack.clear()
        self._undo_buffer.clear()
        self.unselect()
        text = text.replace("\n", " ")[: self.max_chars]
        self._line_length = wcswidth(text)

        self._box.canvas[:] = style_char(" ")
        self._box.width = max(self._line_length + 1, self.width)
        self._box.add_str(text)
        if self._line_length == 0 and self._placeholder:
            self._placeholder_gadget.is_enabled = True
        self.cursor = self._line_length

    @property
    def cursor(self) -> int:
        return self._cursor.x

    @cursor.setter
    def cursor(self, cursor: int):
        """
        After setting cursor position, move textbox so that cursor is visible.
        """
        self._cursor.x = cursor
        if self._line_length == 0 and self._placeholder:
            self._placeholder_gadget.is_enabled = True
        else:
            self._placeholder_gadget.is_enabled = False

        max_x = self.width - 1
        if (rel_x := cursor + self._box.x) > max_x:
            self._box.x += max_x - rel_x
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
        return self._selection_start is not None and self._selection_end is not None

    @property
    def has_nonempty_selection(self) -> bool:
        return self.is_selecting and self._selection_start != self._selection_end

    def select(self):
        if not self.is_selecting:
            self._selection_start = self._selection_end = self.cursor

    def unselect(self):
        self._selection_start = self._selection_end = None

    def delete_selection(self):
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
        box.canvas[0, self._line_length :] = style_char(box.default_char)

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
        box.canvas[0, box_width:] = style_char(box.default_char)

        self.cursor = min(box_width, x + wcswidth(text))
        return self._del_text, [x, self.cursor], selection_start, selection_end, cursor

    def move_cursor_left(self, n: int = 1):
        text_before_cursor = "".join(self._box.canvas["char"][0, : self.cursor])
        nchars_before_cursor = len(text_before_cursor)
        if n <= nchars_before_cursor:
            self.cursor = wcswidth(text_before_cursor[:-n])
        else:
            self.cursor = 0

    def move_cursor_right(self, n: int = 1):
        text_after_cursor = "".join(
            self._box.canvas["char"][0, self.cursor : self._line_length]
        )
        nchars_after_cursor = len(text_after_cursor)
        if n <= nchars_after_cursor:
            self.cursor += wcswidth(text_after_cursor[:n])
        else:
            self.cursor = self._line_length

    def move_word_left(self):
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
                    is_word_char = current_char in WORD_CHARS
            elif current_char.isspace() or is_word_char != (current_char in WORD_CHARS):
                self.move_cursor_right()
                break

    def move_word_right(self):
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
                    is_word_char = current_char in WORD_CHARS
            elif current_char.isspace() or is_word_char != (current_char in WORD_CHARS):
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
            self._box.canvas["char"][0, : self._line_length] != ""
        ).sum() < self.max_chars:
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

        self._move_undo_buffer_to_stack()
        undos = []
        if undo := self.delete_selection():
            undos.append(undo)
        undos.append(self._add_text(self.cursor, paste_event.paste))
        self._undo_stack.append(undos)
        self._redo_stack.clear()

        return True

    def grab(self, mouse_event):
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
        super().ungrab(mouse_event)
        if self._selection_start == self._selection_end:
            self.unselect()