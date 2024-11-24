"""An interactive python console gadget."""

from __future__ import annotations

import asyncio
import builtins
import sys
import time
from code import InteractiveInterpreter
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import Self

from ..terminal.events import KeyEvent, PasteEvent
from .behaviors.focusable import Focusable
from .behaviors.themable import Themable
from .gadget import Gadget, Point, PosHint, Size, SizeHint
from .pane import Pane
from .scroll_view import ScrollView
from .text import Text, str_width
from .textbox import Textbox

__all__ = ["Console", "Point", "Size"]

PROMPT_1 = ">>> "
PROMPT_2 = "... "
DEFAULT_BANNER = f"""\
Welcome to the batgrl interactive console!
The root gadget is "root" and the running app is "app".
Python {sys.version} on {sys.platform}
Type "help", "copyright", "credits" or "license" for more information."""


class _InteractiveConsole(InteractiveInterpreter):
    """An custom interactive interpreter."""

    def __init__(self, console_gadget):
        super().__init__()
        self.filename = "<batgrl console>"
        self.src_buffer = []
        self.console_gadget: Console = console_gadget
        self.input_buffer = None
        """Result of replaced stdin.read or stdin.readline."""
        self.output_buffer = StringIO()
        """Replaces stdout while executing code."""
        self.exec_in_thread: bool = False
        """Whether code is executed in a separate thread."""

        def read(size=-1):
            return self.input()

        self.stdin = type("stdin", (), {"read": read, "readline": read})()
        """Replaces sys.stdin while executing code."""

    def flush(self):
        """Write the output buffer to console gadget's output."""
        text = self.output_buffer.getvalue()
        self.output_buffer.truncate(0)
        self.console_gadget._add_text_to_output(text)

    def input(self, prompt=""):
        """Replace `builtins.input` while executing code."""
        if not self.exec_in_thread:
            print("set `exec_in_thread` to True to enable `input`")

        *lines, last_line = str(prompt).split("\n")
        self.output_buffer.write("\n".join(lines))
        self.flush()

        if not self.exec_in_thread:
            print(last_line)
            return ""

        self.console_gadget._input_mode = True
        self.console_gadget._prompt.set_text(last_line)

        try:
            # Blocking
            while self.input_buffer is None:
                time.sleep(0.01)
            return self.input_buffer
        finally:
            self.input_buffer = None
            self.console_gadget._input_mode = False
            self.console_gadget._prompt.set_text(PROMPT_1)

    def exec(self, code):
        old_input, builtins.input = builtins.input, self.input
        old_stdin, sys.stdin = sys.stdin, self.stdin

        with (
            redirect_stdout(self.output_buffer),
            redirect_stderr(self.output_buffer),
        ):
            try:
                exec(code, self.locals)
            except SystemExit:
                raise
            except:  # noqa
                self.showtraceback()
            finally:
                builtins.input = old_input
                sys.stdin = old_stdin
                self.flush()

    def runcode(self, code):
        if self.exec_in_thread:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, self.exec, code)
        else:
            self.exec(code)

    def push(self, line):
        self.src_buffer.append(line)
        source = "\n".join(self.src_buffer)

        with redirect_stderr(self.output_buffer):
            more = self.runsource(source)

        self.flush()

        if not more:
            self.src_buffer.clear()
            self.console_gadget._prompt.set_text(PROMPT_1)
        else:
            self.console_gadget._prompt.set_text(PROMPT_2)


class _ConsoleTextbox(Textbox):
    """A custom textbox that grows and shrinks with its input."""

    @property
    def console(self) -> Self:
        return self.parent.parent.parent

    @property
    def cursor(self) -> int:
        return self._cursor.x

    @cursor.setter
    def cursor(self, cursor: int):
        self._cursor.x = cursor

        if self.parent is None:
            return

        y, x = self.pos
        self.console._scroll_view.scroll_to_rect((y, cursor + x))

        if self.is_selecting:
            self._selection_end = self.cursor

        self._highlight_selection()

    def on_size(self):
        if self.right >= self.console._min_line_length:
            self.console._container.width = self.right
        else:
            self.console._container.width = self.console._min_line_length
        # self.cursor = self.cursor

    def _del_text(self, start: int, end: int):
        result = super()._del_text(start, end)
        self.width = self._box.width = self._line_length + 1
        return result

    def _add_text(self, x: int, text: str):
        result = super()._add_text(x, text)
        self.width = self._box.width = self._line_length + 1
        return result

    def _tab(self):
        self._move_undo_buffer_to_stack()
        undos = []
        if undo := self.delete_selection():
            undos.append(undo)
        undos.append(self._add_text(self.cursor, "    "))
        self._undo_stack.append(undos)
        self._redo_stack.clear()

    def on_key(self, key_event: KeyEvent) -> bool | None:
        if (
            key_event.key == "tab"
            and not key_event.alt
            and not key_event.ctrl
            and not key_event.shift
        ):
            self._tab()
            return True
        if (
            key_event.key == "left"
            and not key_event.alt
            and not key_event.ctrl
            and not key_event.shift
            and self.cursor == 0
        ):
            self.console._scroll_view.horizontal_proportion = 0
            return True
        return super().on_key(key_event)

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        *lines, last = paste_event.paste.split("\n")
        for line in lines:
            super().on_paste(PasteEvent(line))
            self.enter_callback(self)
        super().on_paste(PasteEvent(last))
        return True

    def on_focus(self):
        pass

    def on_blur(self):
        # A hack to prevent textbox from losing focus when console is clicked:
        if self.parent and self.console.is_focused:
            self.focus()


def _enter_callback(textbox: Textbox):
    """Add input to history then push input on enter for _ConsoleTextbox."""
    text = textbox.text.rstrip()
    textbox.text = ""
    textbox.width = 1
    console: Console = textbox.parent.parent.parent
    console._add_text_to_output(text, with_prompt=True)

    if (
        isinstance(console._history_index, float)
        or console._history_index >= -1
        or text != console._history[console._history_index]
    ):
        console._history_index = 0

    if text and (len(console._history) == 0 or console._history[-1] != text):
        console._history.append(text)
        console._history_index -= 0.5
    elif console._history_index < 0:
        console._history_index += 0.5

    if console._input_mode:
        console._console.input_buffer = text
    else:
        console._console.push(text)


class _Prompt(Text):
    def set_text(self, text: str, **kwargs):
        self._text = text
        super().set_text(text, **kwargs)


class _AlmostPane(Pane):
    def _render(self, canvas):
        console: Console = self.parent.parent
        self._region -= console._input._region
        super()._render(canvas)


class Console(Themable, Focusable, Gadget):
    r"""
    An interactive python console gadget.

    Parameters
    ----------
    banner : str | None, default: None
        The banner to print in the console before first interaction. If not provided, a
        default banner is printed.
    exec_in_thread : bool, default: False
        Whether code is executed in a separate thread. Code not executed in a separated
        thread can block the event loop.
    size : Size, default: Size(10, 10)
        Size of gadget.
    alpha : float, default: 1.0
        Transparency of gadget.
    pos : Point, default: Point(0, 0)
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
    exec_in_thread : bool
        Whether code is executed in a separate thread.
    alpha : float
        Transparency of gadget.
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
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
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
    app : App
        The running app.

    Methods
    -------
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
    add_gadgets(\*gadgets)
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

    # TODO: Add a max output lines option.
    # TODO: Add a max input history option.
    # ? Maybe add some shell commands.

    def __init__(
        self,
        banner: str | None = None,
        exec_in_thread: bool = False,
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._output = Text(
            pos=(-1, 0), size=(1, 1), alpha=0, is_visible=False, is_transparent=True
        )
        self._prompt = _Prompt(alpha=0, is_transparent=True)
        self._input = _ConsoleTextbox(
            size=(1, 1), enter_callback=_enter_callback, is_transparent=is_transparent
        )
        self._container = Gadget(size=(1, 1), is_transparent=True)

        self._scroll_view = ScrollView(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            dynamic_bars=True,
            arrow_keys_enabled=False,
            is_transparent=is_transparent,
        )
        # Replace scroll view background with a pane that doesn't paint under _input.
        self._scroll_view.remove_gadget(self._scroll_view._background)
        self._scroll_view._background = _AlmostPane(
            size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        self._scroll_view.add_gadget(self._scroll_view._background)
        self._scroll_view.children.insert(0, self._scroll_view.children.pop())
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self._console = _InteractiveConsole(self)
        self._input_mode: bool = False
        self._history = []
        self._history_index: float | int = 0
        """
        Current index into history.

        If this value is a float then it is halfway between two integer indices and an
        up or down key press will move it to one of them.
        """
        self._min_line_length = str_width(PROMPT_1) + 1
        self.exec_in_thread = exec_in_thread
        self.alpha = alpha

        def fix_input_pos():
            self._input.left = self._prompt.right

        def update_cursor():
            self._input.cursor = self._input.cursor

        self._prompt.bind("size", fix_input_pos)
        self._prompt.bind("pos", fix_input_pos)
        self._scroll_view.bind("show_horizontal_bar", update_cursor)
        self._scroll_view.bind("show_vertical_bar", update_cursor)

        self._prompt.set_text(PROMPT_1)
        self._container.add_gadgets(self._output, self._prompt, self._input)

        self._scroll_view.view = self._container
        self.add_gadget(self._scroll_view)

        if banner is None:
            self._add_text_to_output(DEFAULT_BANNER)
        else:
            self._add_text_to_output(str(banner))

    def _add_text_to_output(self, text: str, with_prompt: bool = False):
        if with_prompt:
            text = f"{self._prompt._text}{text}"
        else:
            text = text.rstrip("\n")
            if not text:
                return

        lines = text.split("\n")
        max_line_length = max(str_width(line) for line in lines)

        if self._min_line_length < max_line_length:
            self._min_line_length = max_line_length

        if self._output.is_visible:
            line_number = self._output.height
            self._output.height += len(lines)
        else:
            self._output.is_visible = True
            self._output.y = 0
            line_number = 0
            self._output.height = len(lines)

        self._container.height += len(lines)
        self._container.width = self._min_line_length
        self._output.width = self._min_line_length
        for i, line in enumerate(lines):
            self._output.add_str(line, pos=(line_number + i, 0))
        self._prompt.top = self._output.bottom
        self._input.top = self._output.bottom

        self._scroll_view.horizontal_proportion = 0.0
        self._scroll_view.vertical_proportion = 1.0

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._scroll_view.alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._scroll_view.alpha = alpha
        self._input.alpha = alpha

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._scroll_view.is_transparent = self.is_transparent
        self._input.is_transparent = self.is_transparent

    @property
    def exec_in_thread(self) -> bool:
        """
        Whether code is executed in a separate thread. Code not executed in a separated
        thread can block the event loop.
        """
        return self._console.exec_in_thread

    @exec_in_thread.setter
    def exec_in_thread(self, exec_in_thread: bool):
        self._console.exec_in_thread = exec_in_thread

    def update_theme(self):
        """Paint the gadget with current theme."""
        primary = self.color_theme.primary
        self._prompt.default_fg_color = self._prompt.canvas["fg_color"] = primary.fg
        self._prompt.default_bg_color = self._prompt.canvas["bg_color"] = primary.bg
        self._output.default_fg_color = self._output.canvas["fg_color"] = primary.fg
        self._output.default_bg_color = self._output.canvas["bg_color"] = primary.bg
        self._input._box.canvas["fg_color"] = primary.fg
        self._input._box.default_fg_color = primary.fg
        self._input._box.canvas["bg_color"] = primary.bg
        self._input._box.default_bg_color = primary.bg
        self._input._cursor.fg_color = primary.bg
        self._input._cursor.bg_color = primary.fg

    def on_add(self):
        """Add running app and root gadget to console's locals."""
        super().on_add()
        self._console.locals["app"] = self.app
        self._console.locals["root"] = self.root

    def on_focus(self):
        """Enable cursor."""
        self._input.focus()
        self._input._cursor.is_enabled = True

    def on_blur(self):
        """Disable cursor."""
        self._input._cursor.is_enabled = False

    def on_key(self, key_event: KeyEvent) -> bool | None:
        """Get previous inputs on up/down."""
        if (
            key_event.key == "up"
            and not key_event.alt
            and not key_event.ctrl
            and not key_event.shift
        ):
            if isinstance(self._history_index, float):
                if len(self._history) + self._history_index - 0.5 >= 0:
                    self._history_index = int(self._history_index - 0.5)
                    self._input.text = self._history[self._history_index]
            elif len(self._history) + self._history_index - 1 >= 0:
                self._history_index -= 1
                self._input.text = self._history[self._history_index]
        elif (
            key_event.key == "down"
            and not key_event.alt
            and not key_event.ctrl
            and not key_event.shift
        ):
            if isinstance(self._history_index, float):
                if self._history_index + 0.5 < 0:
                    self._history_index = int(self._history_index + 0.5)
                    self._input.text = self._history[self._history_index]
            elif self._history_index + 1 < 0:
                self._history_index += 1
                self._input.text = self._history[self._history_index]
        else:
            return super().on_key(key_event)

        return True
