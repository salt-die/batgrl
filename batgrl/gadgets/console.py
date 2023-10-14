"""
An interactive python console gadget.
"""
import asyncio
import builtins
import sys
import time
from code import InteractiveInterpreter
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from wcwidth import wcswidth

from ..colors import Color, ColorPair
from ..io import Key, KeyEvent, Mods
from .behaviors.focusable import Focusable
from .behaviors.themable import Themable
from .gadget import Gadget, Point, PosHint, PosHintDict, Size, SizeHint, SizeHintDict
from .scroll_view import (
    DEFAULT_INDICATOR_HOVER,
    DEFAULT_INDICATOR_NORMAL,
    DEFAULT_INDICATOR_PRESS,
    DEFAULT_SCROLLBAR_COLOR,
    ScrollView,
)
from .text import Text
from .textbox import Textbox

__all__ = ["Console"]

PROMPT_1 = ">>> "
PROMPT_2 = "... "


class _InteractiveConsole(InteractiveInterpreter):
    """
    An interactive interpreter that execs to a separate thread and redirects stderr and
    stdout. Also, temporarily replaces `builtins.input` and hides stdin while executing.
    """

    # This probably looks insane, but there are a couple of issues this interactive
    # interpreter needs to handle:
    # 1) Running arbitray code in an interactive console could easily block the event
    #    loop. To prevent this, code is executed in a separate thread.
    # 2) Reading stdin and writing to stdout and stderr will ruin batgrl's io. To this
    #    end, the most common function for reading stdin, `input`, is replaced
    #    temporarily while executing code and stdin itself is replaced with an object
    #    that will raise an error if readline is called. Further, stderr and stdout are
    #    always redirected while executing or trying to compile code.

    def __init__(self, console_gadget):
        super().__init__()
        self.filename = "<batgrl console>"
        self.buffer = []
        self.console_gadget: "Console" = console_gadget
        self._input = None
        self._output = StringIO()
        self._loop: asyncio.AbstractEventLoop
        """batgrl's event loop. Set by `console_gadget.on_add`"""

    def _write_output(self):
        text = self._output.getvalue()
        self._output.truncate(0)
        self.console_gadget._add_text_to_output(text)

    def push(self, line):
        self.buffer.append(line)
        source = "\n".join(self.buffer)

        with redirect_stdout(self._output), redirect_stderr(self._output):
            more = self.runsource(source)

        if not more:
            self.buffer.clear()
            self.console_gadget._prompt.set_text(PROMPT_1)
        else:
            self.console_gadget._prompt.set_text(PROMPT_2)

        self._write_output()

    def _fake_input(self, prompt=""):
        """
        This method replaces `builtins.input` when the interpreter executes code.

        Warnings
        --------
        This method blocks indefinitely, so don't call unless in a separate thread.
        """
        try:
            *lines, last_line = str(prompt).split("\n")
            self._output.write("\n".join(lines))
            self._loop.call_soon_threadsafe(self._write_output)
            self._loop.call_soon_threadsafe(
                lambda: self.console_gadget._prompt.set_text(last_line)
            )
            self.console_gadget._input_mode = True

            # Blocking
            while self._input is None:
                time.sleep(0.01)

            result = self._input
        finally:
            self._loop.call_soon_threadsafe(
                lambda: self.console_gadget._prompt.set_text(PROMPT_1)
            )
            self.console_gadget._input_mode = False
            self._input = None
        return result

    def _exec_in_thread(self, code):
        old_input = builtins.input
        old_stdin = sys.stdin

        class _FileLike:
            def readline(self):
                raise IOError("Can't read stdin")

        try:
            builtins.input = self._fake_input
            sys.stdin = _FileLike()
            with redirect_stdout(self._output), redirect_stderr(self._output):
                try:
                    exec(code, self.locals)
                except SystemExit:
                    raise
                except:  # noqa
                    self.showtraceback()
            self._loop.call_soon_threadsafe(self._write_output)
        finally:
            builtins.input = old_input
            sys.stdin = old_stdin

    def runcode(self, code):
        self._loop.run_in_executor(None, lambda: self._exec_in_thread(code))


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

        rel_cursor = console._prompt.width + cursor
        rel_x = console._container.x + rel_cursor

        if rel_x < 0:
            console._scroll_view._scroll_right(rel_x)
        elif console.width <= rel_x:
            console._scroll_view._scroll_right(rel_x - console.width + 1)

        # If it's possible to show prompt and cursor, do it:
        if console._container.x < 0 and rel_cursor < console.width:
            console._scroll_view.horizontal_proportion = 0

        if self.is_selecting:
            self._selection_end = self.cursor

        self._highlight_selection()

    def on_size(self):
        console: Console = self.parent.parent.parent
        offset = console._prompt.width
        if self.width + offset >= console._min_line_length:
            console._container.width = self.width + offset
        else:
            console._container.width = console._min_line_length
        console._update_bars()
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

    def on_focus(self):
        pass

    def on_blur(self):
        # A hack to prevent textbox from losing focus when console is clicked:
        if self.parent:
            console: Console = self.parent.parent.parent
            if console.is_focused:
                self.focus()


class Console(Themable, Focusable, Gadget):
    """
    An interactive python console gadget.

    Warnings
    --------
    Code is executed in a separate thread. Modifying the running app or its gadget tree
    may not be threadsafe; if executed code will modify the gadget tree, its safest to
    wrap the code with `loop.call_soon_threadsafe`.

    Parameters
    ----------
    banner : str | None, default: None
        The banner to print in the console before first interaction. If not provided, a
        default banner is printed.
    scrollbar_color : Color, default: DEFAULT_SCROLLBAR_COLOR
        Background color of scrollbar.
    indicator_normal_color : Color, default: DEFAULT_INDICATOR_NORMAL
        Scrollbar indicator normal color.
    indicator_hover_color : Color, default: DEFAULT_INDICATOR_HOVER
        Scrollbar indicator hover color.
    indicator_press_color : Color, default: DEFAULT_INDICATOR_PRESS
        Scrollbar indicator press color.
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
    scrollbar_color : Color
        Background color of scrollbar.
    indicator_normal_color : Color
        Scrollbar indicator normal color.
    indicator_hover_color : Color
        Scrollbar indicator hover color.
    indicator_press_color : Color
        Scrollbar indicator press color.
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
        Called when gadget is focused.
    on_blur():
        Called when gadget loses focus.
    on_size():
        Called when gadget is resized.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        True if point collides with an uncovered portion of gadget.
    collides_gadget(other):
        True if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\\*gadgets):
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
        Called after a gadget is added to gadget tree.
    on_remove():
        Called before gadget is removed from gadget tree.
    prolicide():
        Recursively remove all children.
    destroy():
        Destroy this gadget and all descendents.
    """

    def __init__(
        self,
        banner: str | None = None,
        scrollbar_color: Color = DEFAULT_SCROLLBAR_COLOR,
        indicator_normal_color: Color = DEFAULT_INDICATOR_NORMAL,
        indicator_hover_color: Color = DEFAULT_INDICATOR_HOVER,
        indicator_press_color: Color = DEFAULT_INDICATOR_PRESS,
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
        self._output = Text(
            size_hint={"height_hint": 1.0, "width_hint": 1.0, "height_offset": -1},
            pos_hint={"y_hint": 1.0, "anchor": "bottom", "y_offset": -1},
            is_visible=False,
            size=(1, 1),
        )
        self._prompt = Text(pos_hint={"y_hint": 1.0, "anchor": "bottom"})
        self._prompt.set_text(PROMPT_1)
        self._min_line_length = self._prompt.width + 1
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
                or self._history_index != 0
                and text != self._history[self._history_index]
            ):
                self._history_index = 0

            if text and (len(self._history) == 0 or self._history[-1] != text):
                self._history.append(text)
                if self._history_index != 0:
                    self._history_index -= 0.5

            if self._input_mode:
                self._console._input = text
            else:
                self._console.push(text)

        self._input = _ConsoleTextbox(
            size=(1, 1),
            pos_hint={"y_hint": 1.0, "anchor": "bottom"},
            enter_callback=enter_callback,
        )

        def fix_pos():
            self._input.left = self._prompt.right

        self._input.subscribe(self._prompt, "size", fix_pos)

        self._container = Gadget(size=(1, self._min_line_length))
        self._container.add_gadgets(self._output, self._prompt, self._input)
        self._scroll_view = ScrollView(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            arrow_keys_enabled=False,
        )
        self._scroll_view.view = self._container
        self.add_gadget(self._scroll_view)

        self.scrollbar_color = scrollbar_color
        self.indicator_normal_color = indicator_normal_color
        self.indicator_hover_color = indicator_hover_color
        self.indicator_press_color = indicator_press_color
        self._update_bars()

        if banner is None:
            self._add_text_to_output(
                "Welcome to the batgrl interactive console!\n"
                'The root gadget is "root", the running app is "app" and event loop '
                'is "loop".\n'
                "(Code that modifies the gadget tree should probably be wrapped with "
                '"loop.call_soon_threadsafe".)\n'
                f"Python {sys.version} on {sys.platform}\n"
                'Type "help", "copyright", "credits" or "license" for more information.'
            )
        else:
            self._add_text_to_output(str(banner))

    @property
    def scrollbar_color(self) -> Color:
        return self._scroll_view.scrollbar_color

    @scrollbar_color.setter
    def scrollbar_color(self, color: Color):
        self._scroll_view.scrollbar_color = color

    @property
    def indicator_normal_color(self) -> Color:
        return self._scroll_view.indicator_normal_color

    @indicator_normal_color.setter
    def indicator_normal_color(self, color: Color):
        self._scroll_view.indicator_normal_color = color

    @property
    def indicator_hover_color(self) -> Color:
        return self._scroll_view.indicator_hover_color

    @indicator_hover_color.setter
    def indicator_hover_color(self, color: Color):
        self._scroll_view.indicator_hover_color = color

    @property
    def indicator_press_color(self) -> Color:
        return self._scroll_view.indicator_press_color

    @indicator_press_color.setter
    def indicator_press_color(self, color: Color):
        self._scroll_view.indicator_press_color = color

    def _update_bars(self):
        self._scroll_view.show_vertical_bar = self._container.height > self.height
        self._scroll_view.show_horizontal_bar = self._container.width > self.width

    def _add_text_to_output(self, text: str, with_prompt: bool = False):
        if with_prompt:
            prompt = "\n".join("".join(line) for line in self._prompt.canvas["char"])
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

        self._update_bars()
        self._scroll_view.horizontal_proportion = 0.0
        self._scroll_view.vertical_proportion = 1.0

    def on_size(self):
        self._update_bars()

    def update_theme(self):
        primary = self.color_theme.primary
        self._scroll_view.background_color_pair = primary
        self._container.background_color_pair = primary
        self._prompt.colors[:] = primary
        self._prompt.default_color_pair = primary
        self._output.colors[:] = primary
        self._output.default_color_pair = primary
        self._input._box.colors[:] = primary
        self._input._box.default_color_pair = primary
        self._input._cursor.background_color_pair = primary.reversed()

    def on_add(self):
        super().on_add()
        self._console.locals["app"] = self.app
        self._console.locals["root"] = self.root
        self._console._loop = self._console.locals["loop"] = asyncio.get_event_loop()

    def on_focus(self):
        self._input.focus()
        self._input._cursor.is_enabled = True

    def on_blur(self):
        self._input._cursor.is_enabled = False

    def on_key(self, key_event: KeyEvent) -> bool | None:
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
