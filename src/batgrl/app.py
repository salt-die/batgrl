"""Base for creating terminal applications."""

import asyncio
import sys
from abc import ABC, abstractmethod
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from time import perf_counter
from typing import Any, Final

from .colors import DEFAULT_COLOR_THEME, Color, ColorTheme
from .gadgets._root import _Root
from .gadgets.behaviors.focusable import Focusable
from .gadgets.behaviors.themable import Themable
from .gadgets.gadget import Gadget
from .geometry import Point, Size
from .rendering import render_root
from .terminal import Vt100Terminal, app_mode, get_platform_terminal
from .terminal.events import (
    ColorReportEvent,
    CursorPositionResponseEvent,
    DeviceAttributesReportEvent,
    Event,
    FocusEvent,
    KeyEvent,
    MouseButton,
    MouseEvent,
    PasteEvent,
    ResizeEvent,
)

__all__ = ["App", "run_gadget_as_app"]

_CTRL_C: Final = KeyEvent("c", ctrl=True)
"""Keybind for exiting the app."""
_TAB: Final = KeyEvent("tab")
"""Keybind for focusing next focusable."""
_SHIFT_TAB: Final = KeyEvent("tab", shift=True)
"""Keybind for focusing previous focusable."""


class App(ABC):
    r"""
    Base for creating terminal applications.

    Parameters
    ----------
    fg_color : Color | None, default: None
        Foreground color of app. If not given, try to use terminal foreground.
    bg_color : Color | None, default: None
        Background color of app. If not given, try to use terminal background.
    title : str | None, default: None
        The terminal's title.
    inline : bool, default: False
        Whether to render app inline or in the alternate screen.
    inline_height :int, default: 10
        Height of app if rendered inline.
    color_theme : ColorTheme, default: DEFAULT_COLOR_THEME
        Color theme for :class:`batgrl.gadgets.behaviors.themable.Themable` gadgets.
    double_click_timeout : float, default: 0.5
        Max duration of a double-click.
    render_interval : float, default: 0.0
        Duration in seconds between consecutive frame renders.
    redirect_stderr : Path | None, default: None
        If provided, stderr is written to this path.

    Attributes
    ----------
    fg_color : Color | None
        Foreground color of app.
    bg_color : Color
        Background color of app.
    title : str | None
        The terminal's title.
    inline : bool
        Whether to render app inline or in the alternate screen buffer.
    inline_height :int
        Height of app if rendered inline.
    color_theme : ColorTheme
        Color theme for :class:`batgrl.gadgets.behaviors.themable.Themable` gadgets.
    double_click_timeout : float
        Max duration of a double-click.
    render_interval : float
        Duration in seconds between consecutive frame renders.
    redirect_stderr : Path | None
        Path where stderr is saved.
    root : _Root | None
        Root of gadget tree.
    children : list[Gadget]
        Alias for :attr:`root.children`.

    Methods
    -------
    on_start()
        Coroutine scheduled when app is run.
    run()
        Run the app.
    exit(exit_value)
        Exit the app.
    add_gadget(gadget)
        Alias for :attr:`root.add_gadget`.
    add_gadgets(\*gadgets)
        Alias for :attr:`root.add_gadgets`.
    """

    def __init__(
        self,
        *,
        fg_color: Color | None = None,
        bg_color: Color | None = None,
        title: str | None = None,
        inline: bool = False,
        inline_height: int = 10,
        color_theme: ColorTheme = DEFAULT_COLOR_THEME,
        double_click_timeout: float = 0.5,
        render_interval: float = 0.0,
        redirect_stderr: Path | None = None,
    ):
        self.root: _Root | None = None
        """Root of gadget tree (only set while app is running)."""
        self.fg_color = fg_color
        """Foreground color of app."""
        self.bg_color = bg_color
        """Background color of app."""
        self.title = title
        """The terminal's title."""
        self._inline = inline
        """Whether to render app inline or in the alternate screen buffer."""
        self.inline_height = inline_height
        """Height of app if rendered inline."""
        self.color_theme = color_theme
        """Color theme for Themable gadgets."""
        self.double_click_timeout = double_click_timeout
        """Max duration of a double-click."""
        self.render_interval = render_interval
        """Duration in seconds between consecutive frame renders."""
        self.redirect_stderr = redirect_stderr
        """Path where stderr is saved."""
        self._terminal: Vt100Terminal | None = None
        """Platform-specific terminal (only set while app is running)."""
        self._exit_value: Any = None
        """Value set by ``exit(exit_value)`` and returned by ``run()``."""
        self._sixel_support: bool = False
        """Whether terminal has sixel support."""

    def __repr__(self):
        return (
            f"{type(self).__name__}(\n"
            f"    bg_color={(*self.bg_color,)},\n"
            f"    title={self.title!r},\n"
            f"    inline={self.inline},\n"
            f"    inline_height={self.inline_height},\n"
            f"    double_click_timeout={self.double_click_timeout},\n"
            f"    render_interval={self.render_interval},\n"
            f"    redirect_stderr={self.redirect_stderr},\n"
            ")"
        )

    @property
    def is_running(self) -> bool:
        """Whether app is running."""
        return self.root is not None

    @property
    def inline(self) -> bool:
        """Whether to render app inline or in the alternate screen buffer."""
        return self._inline

    @inline.setter
    def inline(self, inline: bool):
        if inline == self._inline:
            return

        self._inline = inline
        if self._terminal is None:
            return

        if inline:
            self._terminal.exit_alternate_screen()
            self._scroll_inline()
        else:
            self._terminal.erase_in_display()
            self._terminal.enter_alternate_screen()
            self.root.pos = Point(0, 0)
            self.root.size = self._terminal.get_size()

    def _scroll_inline(self) -> None:
        """Ensure inline mode has enought vertical space in terminal."""
        if self._terminal is None:
            return

        height = min(self.inline_height, self._terminal.get_size().height)
        self._terminal._out_buffer.append("\x0a" * height)  # Feed lines (may scroll).
        self._terminal._out_buffer.append(f"\x1b[{height}F")  # Move cursor back up.
        self._terminal.request_cursor_position_report()

    @property
    def inline_height(self) -> int:
        """
        Height of app if rendered inline.

        ``inline_height`` will be clipped to terminal height if too great.
        """
        return self._inline_height

    @inline_height.setter
    def inline_height(self, inline_height: int):
        self._inline_height = inline_height
        if self.inline and self.root is not None:
            height, _ = self._terminal.get_size()
            self.root.height = min(inline_height, height)

    @property
    def color_theme(self) -> ColorTheme:
        """Color theme for themable gadgets."""
        return self._color_theme

    @color_theme.setter
    def color_theme(self, color_theme: ColorTheme):
        self._color_theme = color_theme
        Themable.set_theme(color_theme)

        if self.root is not None:
            for gadget in self.root.walk():
                if isinstance(gadget, Themable):
                    gadget.update_theme()

    @property
    def fg_color(self) -> Color | None:
        """
        Foreground color of app.

        If set to ``None``, the terminal foreground color will be queried. If the
        terminal reports the foreground color, then :attr:``fg_color`` will be updated
        to the terminal's foreground color.
        """
        return self._fg_color

    @fg_color.setter
    def fg_color(self, fg_color: Color | None):
        self._fg_color = fg_color

        if self.root is None:
            return

        if fg_color is None:
            self._terminal.request_foreground_color()
        else:
            self.root._cell["fg_color"] = fg_color

    @property
    def bg_color(self) -> Color | None:
        """
        Background color of app.

        If set to ``None``, the terminal background color will be queried. If the
        terminal reports the background color, then :attr:``bg_color`` will be updated
        to the terminal's background color.
        """
        return self._bg_color

    @bg_color.setter
    def bg_color(self, bg_color: Color | None):
        self._bg_color = bg_color
        if self.root is None:
            return

        if bg_color is None:
            self._terminal.request_background_color()
        else:
            self.root._cell["bg_color"] = bg_color

    @abstractmethod
    async def on_start(self):
        """Coroutine scheduled when app is run."""

    def run(self) -> Any:
        """Run the app."""
        try:
            with redirect_stderr(StringIO()) as defer_stderr:
                asyncio.run(self._run_async())
        except asyncio.CancelledError:
            pass
        finally:
            error_output = defer_stderr.getvalue()
            if self.redirect_stderr:
                with open(self.redirect_stderr, "w") as error_file:
                    print(error_output, file=error_file, end="")
            else:
                print(error_output, file=sys.stderr, end="")

        exit_value = self._exit_value
        self._exit_value = None
        return exit_value

    def exit(self, exit_value: Any = None) -> None:
        """
        Exit the app.

        Parameters
        ----------
        exit_value : Any, default: None
            Value returned by ``run()``.
        """
        self._exit_value = exit_value
        if self.root is not None:
            self.root.destroy()
            self.root = None
        self._terminal = None

        try:
            tasks = asyncio.all_tasks()
        except RuntimeError:
            pass
        else:
            for task in tasks:
                task.cancel()

    async def _run_async(self):
        """Build environment, create root, and schedule app-specific tasks."""
        terminal = self._terminal = get_platform_terminal()
        last_size: Size = terminal.get_size()
        self.root = root = _Root(app=self, size=last_size)

        last_mouse_button: MouseButton = "no_button"
        last_mouse_time = perf_counter()
        last_mouse_nclicks = 0

        def determine_nclicks(mouse_event: MouseEvent) -> None:
            """Determine number of consecutive clicks for a `MouseEvent`."""
            nonlocal last_mouse_button, last_mouse_time, last_mouse_nclicks
            current_time = perf_counter()

            if mouse_event.event_type != "mouse_down":
                return

            if (
                last_mouse_button != mouse_event.button
                or current_time - last_mouse_time > self.double_click_timeout
            ):
                mouse_event.nclicks = 1
            else:
                mouse_event.nclicks = last_mouse_nclicks % 3 + 1

            last_mouse_button = mouse_event.button
            last_mouse_nclicks = mouse_event.nclicks
            last_mouse_time = current_time

        def event_handler(events: list[Event]) -> None:
            """Handle input events."""
            for event in events:
                if isinstance(event, KeyEvent):
                    if event == _CTRL_C:
                        self.exit()
                        return
                    if not root.dispatch_key(event):
                        if event == _TAB:
                            Focusable.focus_next()
                        elif event == _SHIFT_TAB:
                            Focusable.focus_previous()
                elif isinstance(event, MouseEvent):
                    determine_nclicks(event)
                    root.dispatch_mouse(event)
                elif isinstance(event, PasteEvent):
                    root.dispatch_paste(event)
                elif isinstance(event, FocusEvent):
                    root.dispatch_terminal_focus(event)
                elif isinstance(event, ResizeEvent):
                    nonlocal last_size
                    if event.size == last_size:
                        # Sometimes spurious resize events can appear such as when a
                        # terminal first enables VT100 processing or when
                        # entering/exiting the alternate screen buffer.
                        continue
                    last_size = event.size
                    if self.inline:
                        terminal.erase_in_display()
                        self._scroll_inline()
                    else:
                        root.size = event.size
                elif isinstance(event, CursorPositionResponseEvent):
                    if self.inline:
                        height, width = last_size
                        root.size = Size(
                            min(self.inline_height, height), width - event.pos.x
                        )
                        root.pos = event.pos
                elif isinstance(event, ColorReportEvent):
                    if event.kind == "fg":
                        self.fg_color = event.color
                    else:
                        self.bg_color = event.color
                elif isinstance(event, DeviceAttributesReportEvent):
                    self._sixel_support = 4 in event.device_attributes

        async def auto_render():
            """Render screen every :attr:`render_interval` seconds."""
            while True:
                render_root(root, terminal)
                await asyncio.sleep(self.render_interval)

        with app_mode(terminal, event_handler):
            terminal.request_device_attributes()

            if self.title is not None:
                terminal.set_title(self.title)

            if self.fg_color is None:
                terminal.request_foreground_color()
            else:
                self.root._cell["fg_color"] = self.fg_color

            if self.bg_color is None:
                terminal.request_background_color()
            else:
                self.root._cell["bg_color"] = self.bg_color

            if self.inline:
                self._scroll_inline()
            else:
                terminal.enter_alternate_screen()

            await asyncio.gather(self.on_start(), auto_render())

    def add_gadget(self, gadget: Gadget) -> None:
        """
        Alias for :attr:`root.add_gadget`.

        Parameters
        ----------
        gadget : Gadget
            A gadget to add as a child to the root gadget.
        """
        self.root.add_gadget(gadget)

    def add_gadgets(self, *gadgets: Gadget) -> None:
        r"""
        Alias for :attr:`root.add_gadgets`.

        Parameters
        ----------
        \*gadgets : Gadget
            Gadgets to add as children to the root gadget.
        """
        self.root.add_gadgets(*gadgets)

    @property
    def children(self) -> list[Gadget] | None:
        """Alias for :attr:`root.children`."""
        if self.root is not None:
            return self.root.children


def run_gadget_as_app(
    gadget: Gadget,
    *,
    fg_color: Color | None = None,
    bg_color: Color | None = None,
    title: str | None = None,
    inline: bool = False,
    inline_height: int = 10,
    color_theme: ColorTheme = DEFAULT_COLOR_THEME,
    double_click_timeout: float = 0.5,
    render_interval: float = 0.0,
    redirect_stderr: Path | None = None,
) -> Any:
    """
    Run a gadget as an app.

    This convenience function provided for cases when the app would only have a single
    gadget.

    Parameters
    ----------
    gadget : Gadget
        A gadget to run as an app.
    fg_color : Color | None, default: None
        Foreground color of app.
    bg_color : Color | None, default: None
        Background color of app.
    title : str | None, default: None
        The terminal's title.
    inline : bool, default: False
        Whether to render app inline or in the alternate screen.
    inline_height :int, default: 10
        Height of app if rendered inline.
    color_theme : ColorTheme, default: DEFAULT_COLOR_THEME
        Color theme for :class:`batgrl.gadgets.behaviors.themable.Themable` gadgets.
    double_click_timeout : float, default: 0.5
        Max duration of a double-click.
    render_interval : float, default: 0.0
        Duration in seconds between consecutive frame renders.
    redirect_stderr : Path | None, default: None
        If provided, stderr is written to this path.
    """

    class _DefaultApp(App):
        async def on_start(self):
            self.add_gadget(gadget)

    return _DefaultApp(
        fg_color=fg_color,
        bg_color=bg_color,
        title=title,
        inline=inline,
        inline_height=inline_height,
        color_theme=color_theme,
        double_click_timeout=double_click_timeout,
        render_interval=render_interval,
        redirect_stderr=redirect_stderr,
    ).run()
