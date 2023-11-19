"""An interactive python console gadget."""
import asyncio
import builtins
import sys
import time
from code import InteractiveInterpreter
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from wcwidth import wcswidth

from ..io import Key, KeyEvent, Mods, PasteEvent
from .behaviors.focusable import Focusable
from .behaviors.themable import Themable
from .gadget import Gadget
from .gadget_base import (
    GadgetBase,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)
from .scroll_view import ScrollView
from .text import Text
from .textbox import Textbox

__all__ = ["Console"]

PROMPT_1 = ">>> "
PROMPT_2 = "... "
DEFAULT_BANNER = (
    "Welcome to the batgrl interactive console!\n"
    'The root gadget is "root" and the running app is "app".\n'
    f"Python {sys.version} on {sys.platform}\n"
    'Type "help", "copyright", "credits" or "license" for more information.'
)


class _InteractiveConsole(InteractiveInterpreter):
    """
    An interactive interpreter that redirects stdin, stderr, and stdout while executing
    code in a separate thread.
    """

    # TODO: Add a custom ttypager (see: pydoc.ttypager) or interactive help.
    # TODO: Add a getch (sys.stdin.read(1)).
    # ? Console maybe should wait on the future in runcode before allowing more input.

    def __init__(self, console_gadget):
        super().__init__()
        self.filename = "<batgrl console>"
        self.src_buffer = []
        self.console_gadget: "Console" = console_gadget
        self.input_buffer = None
        """Result of replaced stdin.read or stdin.readline."""
        self.output_buffer = StringIO()
        """Replaces stdout while executing code."""

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
        *lines, last_line = str(prompt).split("\n")
        self.output_buffer.write("\n".join(lines))
        self.flush()
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
        asyncio.get_event_loop().run_in_executor(None, self.exec, code)

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
    def cursor(self) -> int:
        return self._cursor.x

    @cursor.setter
    def cursor(self, cursor: int):
        self._cursor.x = cursor

        if self.parent is None:
            return

        console: Console = self.parent.parent.parent
        rel_x = console._container.x + console._prompt.width + cursor
        port_width = console._scroll_view.port_width

        if cursor == 0:
            console._scroll_view.horizontal_proportion = 0
        elif rel_x < 0:
            console._scroll_view._scroll_right(rel_x)
        elif rel_x >= port_width:
            console._scroll_view._scroll_right(rel_x - port_width + 1)

        if self.is_selecting:
            self._selection_end = self.cursor

        self._highlight_selection()

    def on_size(self):
        console: Console = self.parent.parent.parent
        offset = console._prompt.right
        if self.width + offset >= console._min_line_length:
            console._container.width = self.width + offset
        else:
            console._container.width = console._min_line_length
        self.cursor = self.cursor

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
        if key_event == KeyEvent(Key.Tab, Mods.NO_MODS):
            self._tab()
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
        if self.parent:
            console: Console = self.parent.parent.parent
            if console.is_focused:
                self.focus()


class _Prompt(Text):
    def set_text(self, text: str, **kwargs):
        # To fake a 0-width prompt move the prompt offscreen when text is empty.
        self._text = text
        if len(text) == 0:
            self.left = -1
        else:
            self.left = 0
        super().set_text(text, **kwargs)


class Console(Themable, Focusable, GadgetBase):
    r"""
    An interactive python console gadget.

    Parameters
    ----------
    banner : str | None, default: None
        The banner to print in the console before first interaction. If not provided, a
        default banner is printed.
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
    is_focused : bool
        True if gadget has focus.
    any_focused : bool
        True if any gadget has focus.
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

    # TODO: Add a max output lines option.
    # TODO: Add a max input history option.
    # ? Maybe add some shell commands.

    def __init__(
        self,
        banner: str | None = None,
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
        self._output = Text(
            size_hint={"height_hint": 1.0, "width_hint": 1.0, "height_offset": -1},
            pos_hint={"y_hint": 1.0, "anchor": "bottom", "y_offset": -1},
            is_visible=False,
            size=(1, 1),
        )
        self._prompt = _Prompt(pos_hint={"y_hint": 1.0, "anchor": "bottom"})
        self._prompt.set_text(PROMPT_1)
        self._min_line_length = self._prompt.right + 1
        self._input_mode: bool = False
        self._console = _InteractiveConsole(self)
        self._history = []
        self._history_index: float | int = 0
        """
        Current index into history. If this value is a float then it is halfway between
        two integer indices and an up or down key press will move it to one of them.
        """

        def enter_callback(textbox: Textbox):
            text = textbox.text.rstrip()
            textbox.text = ""
            textbox.width = 1
            self._add_text_to_output(text, with_prompt=True)

            if (
                isinstance(self._history_index, float)
                or self._history_index >= -1
                or text != self._history[self._history_index]
            ):
                self._history_index = 0

            if text and (len(self._history) == 0 or self._history[-1] != text):
                self._history.append(text)
                self._history_index -= 0.5
            elif self._history_index < 0:
                self._history_index += 0.5

            if self._input_mode:
                self._console.input_buffer = text
            else:
                self._console.push(text)

        self._input = _ConsoleTextbox(
            size=(1, 1),
            pos_hint={"y_hint": 1.0, "anchor": "bottom"},
            enter_callback=enter_callback,
        )

        def fix_input_pos():
            self._input.left = self._prompt.right

        self._input.subscribe(self._prompt, "size", fix_input_pos)
        self._input.subscribe(self._prompt, "pos", fix_input_pos)

        self._container = Gadget(size=(1, self._min_line_length), background_char=" ")
        self._container.add_gadgets(self._output, self._prompt, self._input)
        self._scroll_view = ScrollView(
            size_hint={"height_hint": 1.0, "width_hint": 1.0}, arrow_keys_enabled=False
        )
        self._scroll_view.view = self._container
        self.add_gadget(self._scroll_view)

        if banner is None:
            self._add_text_to_output(DEFAULT_BANNER)
        else:
            self._add_text_to_output(str(banner))

        self.subscribe(self._container, "size", self._update_bars)
        self.subscribe(self._scroll_view, "size", self._update_bars)

    def _update_bars(self):
        self._scroll_view.show_vertical_bar = (
            self._container.height > self._scroll_view.port_height
        )
        self._scroll_view.show_horizontal_bar = (
            self._container.width > self._scroll_view.port_width
        )

    def _add_text_to_output(self, text: str, with_prompt: bool = False):
        if with_prompt:
            prompt = self._prompt._text
            text = f"{prompt}{text}"
        else:
            text = text.rstrip("\n")
            if not text:
                return

        lines = text.split("\n")
        line_number = self._output.height
        if not self._output.is_visible:
            self._output.is_visible = True
            line_number -= 1
        self._container.height += len(lines)

        self._container.width = self._min_line_length
        for i, line in enumerate(lines):
            line_width = wcswidth(line)
            if line_width > self._container.width:
                self._min_line_length = line_width
                self._container.width = line_width
            self._output.add_str(line, (line_number + i, 0))

        self._scroll_view.horizontal_proportion = 0.0
        self._scroll_view.vertical_proportion = 1.0

    def update_theme(self):
        """Paint the gadget with current theme."""
        primary = self.color_theme.primary
        self._container.background_color_pair = primary
        self._prompt.colors[:] = primary
        self._prompt.default_color_pair = primary
        self._output.colors[:] = primary
        self._output.default_color_pair = primary
        self._input._box.colors[:] = primary
        self._input._box.default_color_pair = primary
        self._input._cursor.background_color_pair = primary.reversed()

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
        if key_event == KeyEvent(Key.Up, Mods.NO_MODS):
            if isinstance(self._history_index, float):
                if len(self._history) + self._history_index - 0.5 >= 0:
                    self._history_index = int(self._history_index - 0.5)
                    self._input.text = self._history[self._history_index]
            elif len(self._history) + self._history_index - 1 >= 0:
                self._history_index -= 1
                self._input.text = self._history[self._history_index]
        elif key_event == KeyEvent(Key.Down, Mods.NO_MODS):
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
