"""A textbox gadget for single-line editable text."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import astuple, dataclass
from typing import cast

from ugrapheme import graphemes
from uwcwidth import wcswidth

from ..geometry import rect_slice
from ..logging import get_logger
from ..terminal.events import KeyEvent, MouseButton, MouseEvent, PasteEvent
from ..text_tools import canvas_as_text, egc_chr, egc_ord, is_word_char
from .behaviors.focusable import Focusable
from .behaviors.grabbable import Grabbable
from .behaviors.themable import Themable
from .cursor import Cursor
from .gadget import (
    Gadget,
    Point,
    Pointlike,
    PosHint,
    Region,
    Size,
    SizeHint,
    Sizelike,
)
from .text import Text

__all__ = ["Point", "Size", "Textbox"]

logger = get_logger(__name__)


@dataclass
class _TextSelection:
    start: int
    end: int


@dataclass
class _TextEdit:
    cursor: int
    selection: _TextSelection | None
    start: int
    end: int
    text: str

    @property
    def first(self) -> int:
        return min(self.start, self.end)

    @first.setter
    def first(self, first: int):
        if self.start <= self.end:
            self.start = first
        else:
            self.end = first

    @property
    def last(self) -> int:
        return max(self.start, self.end)

    @last.setter
    def last(self, last: int):
        if self.end >= self.start:
            self.end = last
        else:
            self.start = last

    def end_of_content(self) -> int:
        return self.first + wcswidth(self.text)

    def join(self, other: _TextEdit) -> bool:
        if other.end_of_content() == self.first:
            width = self.last - self.first
            self.first = other.first
            self.last = other.last + width
            self.text = other.text + self.text
            return True

        if self.last == other.first:
            self.last = other.last
            self.text += other.text
            return True

        return False


class _Box(Text):
    def _render(self, cells, graphics, kind):
        super()._render(cells, graphics, kind)
        textbox = cast(Textbox, self.parent)
        if textbox.hide_input:
            hider_rect = Region.from_rect(self.absolute_pos, (1, textbox._line_width))
            hider_region = self._region & hider_rect
            for pos, size in hider_region.rects():
                cells["ord"][rect_slice(pos, size)] = textbox._hide_char_ord


class Textbox(Themable, Focusable, Grabbable, Gadget):
    r"""
    A textbox gadget for single-line editable text.

    Supports pasting, mouse selection, and cursor navigation.

    Parameters
    ----------
    enter_callback : Callable[[Textbox], None] | None, default: None
        Called when textbox has focus and `enter` is pressed.
    placeholder : str, default: ""
        Placeholder text for textbox.
    hide_input : bool, default: False
        Whether input is hidden with :attr:`hide_char`.
    hide_char : str, default: "*"
        Character to hide input when :attr:`hide_input` is true.
    max_chars : int | None, default: None
        Maximum allowed number of characters in textbox.
    alpha : float, default: 1.0
        Transparency of gadget.
    is_grabbable : bool, default: True
        Whether grabbable behavior is enabled.
    ptf_on_grab : bool, default: False
        Whether the gadget will be pulled to front when grabbed.
    mouse_button : MouseButton, default: "left"
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
    enter_callback : Callable[[Textbox], None] | None
        Called when textbox has focus and `enter` is pressed.
    placeholder : str
        Placeholder text for textbox.
    hide_input : bool
        Whether input is hidden with :attr:`hide_char`.
    hide_char : str
        Character to hide input when :attr:`hide_input` is true.
    max_chars : int | None
        Maximum allowed number of characters in textbox.
    alpha : float
        Transparency of gadget.
    text : str
        The textbox's text.
    cursor : int
        The cursor column.
    is_selecting : bool
        Whether there is a selection.
    has_nonempty_selection : bool
        Whether selection is non-empty.
    is_focused : bool
        Whether gadget has focus.
    any_focused : bool
        Whether any gadget has focus.
    is_grabbable : bool
        Whether grabbable behavior is enabled.
    ptf_on_grab : bool
        Whether the gadget will be pulled to front when grabbed.
    mouse_button : MouseButton
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
        enter_callback: Callable[[Textbox], None] | None = None,
        placeholder: str = "",
        hide_input: bool = False,
        hide_char: str = "*",
        max_chars: int | None = None,
        is_grabbable: bool = True,
        ptf_on_grab: bool = False,
        mouse_button: MouseButton = "left",
        alpha: float = 1.0,
        size: Sizelike = Size(10, 10),
        pos: Pointlike = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._placeholder_gadget = Text(alpha=0.0, is_transparent=is_transparent)
        self._placeholder_gadget.set_text(placeholder)
        self._cursor = Cursor(reverse=False)
        self._box = _Box(size=size, is_transparent=is_transparent)
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

        self._selection: _TextSelection | None = None
        self._line_width = 0
        self._replace_text_to_undo_stack: bool = True
        """Whether ``replace_text`` uses the undo or redo stack."""
        self._replace_text_clears_redo: bool = True
        """Whether ``replace_text`` clears the redo stack."""
        self._undo_stack: list[_TextEdit] = []
        self._redo_stack: list[_TextEdit] = []

        self._box.add_gadgets(self._placeholder_gadget, self._cursor)
        self.add_gadgets(self._box)

        self.enter_callback = enter_callback
        """Called when textbox has focus and `enter` is pressed."""
        self.placeholder = placeholder
        """Placeholder text for textbox."""
        self.hide_input = hide_input
        """Whether input is hidden with :attr:`hide_char`."""
        self._hide_char_ord: int = 0
        """``hide_char``'s ordinal representation."""
        self.hide_char = hide_char
        """Character to hide input if :attr:`hide_input` is true."""
        self.max_chars = max_chars
        """Maximum allowed number of characters in textbox."""
        self.alpha = alpha

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._box.alpha

    @alpha.setter
    def alpha(self, alpha: float) -> None:
        self._box.alpha = alpha

    @property
    def hide_char(self) -> str:
        """
        Character to hide input when :attr:`hide_input` is true.

        If ``hide_char`` cell width is not 1 it will default to ``"*"``.
        """
        return egc_chr(self._hide_char_ord)

    @hide_char.setter
    def hide_char(self, char: str) -> None:
        self._hide_char_ord = egc_ord(char)
        if wcswidth(egc_chr(self._hide_char_ord)) != 1:
            logger.info(
                f"hide_char ({char}) cell width greater than 1, using default hide_char"
            )
            self._hide_char_ord = ord("*")

    @property
    def placeholder(self) -> str:
        """Placeholder text for textbox."""
        return self._placeholder

    @placeholder.setter
    def placeholder(self, placeholder: str):
        self._placeholder = placeholder
        self._placeholder_gadget.set_text(placeholder)
        self._placeholder_gadget.is_enabled = self._line_width == 0 and bool(
            placeholder
        )

    @property
    def text(self) -> str:
        """The textbox's text."""
        return canvas_as_text(self._box.canvas[0, : self._line_width])

    @text.setter
    def text(self, text: str) -> None:
        self._selection = None
        text = graphemes(text.replace("\n", " "))[: self.max_chars]
        self.replace_text(0, self._line_width, text)
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.cursor = self._line_width

    @property
    def cursor(self) -> int:
        """The cursor column."""
        return self._cursor.x

    @cursor.setter
    def cursor(self, cursor: int):
        """After setting cursor position, move textbox so that cursor is visible."""
        self._cursor.x = cursor
        self._placeholder_gadget.is_enabled = self._line_width == 0 and bool(
            self._placeholder
        )

        max_x = self.width - 1
        rel_x = cursor + self._box.x
        if rel_x > max_x:
            self._box.x -= rel_x - max_x
        elif rel_x < 0:
            self._box.x -= rel_x

        if self._selection is not None:
            self._selection.end = self.cursor
        self._highlight_selection()

    def replace_text(self, start: int, end: int, content: str) -> None:
        """
        Replace text from ``start`` to ``end`` with ``content``.

        Parameters
        ----------
        start : int
            The start of text to replace.
        end : int
            The end of text to replace.
        content : str
            The replacement text.
        """
        if start > end:
            start, end = end, start

        if end > self._line_width:
            logger.debug("End of delete greater than line length.")
            end = self._line_width

        prev_selection = self._selection
        prev_cursor = self.cursor
        text = canvas_as_text(self._box.canvas[0, start:end])

        self._selection = None

        len_end = self._line_width - end
        line_width = start + len_end

        box = self._box
        box.canvas[0, start:line_width] = box.canvas[0, end : end + len_end]
        box.canvas[0, line_width:] = box.default_cell

        content = content.replace("\n", " ")

        box_text = graphemes(
            canvas_as_text(box.canvas[0, :start])
            + content
            + canvas_as_text(box.canvas[0, start:line_width])
        )[: self.max_chars]

        box_width = self._line_width = wcswidth(box_text)
        if box_width >= box.width:
            box.width = box_width + 1

        box.add_str(box_text)
        box.canvas[0, box_width:] = box.default_cell

        self.cursor = start + wcswidth(content)

        inverse_edit = _TextEdit(prev_cursor, prev_selection, start, self.cursor, text)
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
        fg = self._box.canvas["fg_color"]
        bg = self._box.canvas["bg_color"]
        fg[:] = self._box.default_fg_color
        bg[:] = self._box.default_bg_color
        if self._selection is not None and self._selection.start != self._selection.end:
            start, end = self._selection.start, self._selection.end
            if start > end:
                start, end = end, start
            fg[0, start:end] = self.get_color("textbox_selection_highlight_fg")
            bg[0, start:end] = self.get_color("textbox_selection_highlight_bg")

    def move_cursor_left(self, n: int = 1):
        """Move cursor left `n` characters."""
        text_before_cursor = canvas_as_text(self._box.canvas[0, : self.cursor])
        egcs = graphemes(text_before_cursor)
        if n <= len(egcs):
            self.cursor = wcswidth(egcs[:-n])
        else:
            self.cursor = 0

    def move_cursor_right(self, n: int = 1):
        """Move cursor right `n` characters."""
        text_after_cursor = canvas_as_text(
            self._box.canvas[0, self.cursor : self._line_width]
        )
        egcs = graphemes(text_after_cursor)
        if n <= len(egcs):
            self.cursor += wcswidth(egcs[:n])
        else:
            self.cursor = self._line_width

    def move_word_left(self):
        """Move cursor a word left."""
        last_x = self.cursor
        first_char_found = char_is_word_char = False
        while True:
            self.move_cursor_left()
            if self.cursor == last_x:
                break

            last_x = self.cursor

            current_char = egc_chr(self._box.canvas[0, self.cursor]["ord"])
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
        first_char_found = char_is_word_char = False
        while True:
            self.move_cursor_right()
            if self.cursor == last_x:
                break

            last_x = self.cursor

            current_char = egc_chr(self._box.canvas[0, self.cursor]["ord"])
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
        self._selection = _TextSelection(0, self._line_width)
        self.cursor = self._line_width

    def _ctrl_d(self):
        """Select word."""
        self._selection = None
        last_x = self.cursor
        while True:
            self.move_cursor_left()
            if last_x == self.cursor:
                break
            if not is_word_char(egc_chr(self._box.canvas[0, self.cursor]["ord"])):
                self.move_cursor_right()
                break
            last_x = self.cursor

        self._selection = _TextSelection(self.cursor, self.cursor)
        last_x = self.cursor
        while True:
            if not is_word_char(egc_chr(self._box.canvas[0, self.cursor]["ord"])):
                break
            self.move_cursor_right()
            if last_x == self.cursor:
                break
            last_x = self.cursor

    def _home(self):
        self._selection = None
        self.cursor = 0

    def _end(self):
        self._selection = None
        self.cursor = self._line_width

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

    def _shift_home(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.cursor = 0

    def _shift_end(self):
        if self._selection is None:
            self._selection = _TextSelection(self.cursor, self.cursor)
        self.cursor = self._line_width

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
        ("backspace", False, False, False): _backspace,
        ("delete", False, False, False): _delete,
        ("left", False, False, False): _left,
        ("right", False, False, False): _right,
        ("left", False, True, False): _ctrl_left,
        ("right", False, True, False): _ctrl_right,
        ("home", False, False, False): _home,
        ("end", False, False, False): _end,
        ("left", False, False, True): _shift_left,
        ("right", False, False, True): _shift_right,
        ("left", False, True, True): _shift_ctrl_left,
        ("right", False, True, True): _shift_ctrl_right,
        ("home", False, False, True): _shift_home,
        ("end", False, False, True): _shift_end,
        ("escape", False, False, False): _escape,
        ("z", False, True, False): undo,
        ("z", False, True, True): redo,
        ("y", False, True, False): redo,  # ctrl + shift + z won't work on linux
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
        elif handler := self.__HANDLERS.get(astuple(key_event)):
            handler(self)
        else:
            return super().on_key(key_event)

        return True

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        """Add paste to textbox."""
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
        if mouse_event.button == "left" and self._box.collides_point(mouse_event.pos):
            super().grab(mouse_event)

            _, x = self._box.to_local(mouse_event.pos)
            cursor = min(x, self._line_width)

            if not mouse_event.shift or self._selection is None:
                self._selection = _TextSelection(cursor, cursor)

            self.cursor = cursor

    def grab_update(self, mouse_event: MouseEvent):
        """Update selection on grab update."""
        if self._box.collides_point(mouse_event.pos):
            _, x = self._box.to_local(mouse_event.pos)
            self.cursor = min(x, self._line_width)
        else:
            _, x = self.to_local(mouse_event.pos)

            if x < 0:
                self.move_cursor_left()
            elif x >= self.width:
                self.move_cursor_right()

    def ungrab(self, mouse_event):
        """Clear an empty selection on ungrab."""
        super().ungrab(mouse_event)
        if self._selection is not None and self._selection.start == self._selection.end:
            self._selection = None

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._box.is_transparent = self.is_transparent
        self._placeholder_gadget.is_transparent = self.is_transparent

    def update_theme(self) -> None:
        """Paint the gadget with current theme."""
        primary_fg = self.get_color("textbox_primary_fg")
        primary_bg = self.get_color("textbox_primary_bg")
        self._box.canvas["fg_color"] = self._box.default_fg_color = primary_fg
        self._box.canvas["bg_color"] = self._box.default_bg_color = primary_bg
        self._cursor.fg_color = primary_bg
        self._cursor.bg_color = primary_fg

        placeholder_fg = self.get_color("textbox_placeholder_fg")
        placeholder_bg = self.get_color("textbox_placeholder_bg")
        self._placeholder_gadget.default_fg_color = placeholder_fg
        self._placeholder_gadget.default_bg_color = placeholder_bg
        self._placeholder_gadget.canvas["fg_color"] = placeholder_fg
        self._placeholder_gadget.canvas["bg_color"] = placeholder_bg

        self._highlight_selection()

    def on_size(self):
        """Resize and reposition children on resize."""
        self._box.width = max(self.width, self._line_width + 1)
        if self._box.x + self._line_width < self.width:
            self._box.x = min(0, self.width - self._line_width)
        self.cursor = self.cursor

    def on_focus(self):
        """Show cursor and select all text on focus."""
        self._cursor.is_enabled = True
        if self._line_width > 0:
            self._ctrl_a()

    def on_blur(self):
        """Hide cursor on blur."""
        self._cursor.is_enabled = False
