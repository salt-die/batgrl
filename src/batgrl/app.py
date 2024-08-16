"""Base for creating terminal applications."""

import asyncio
import sys
from abc import ABC, abstractmethod
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from time import monotonic
from typing import Any, Literal

from .colors import BLACK, DEFAULT_COLOR_THEME, Color, ColorTheme
from .gadgets._root import _Root
from .gadgets.behaviors.focusable import Focusable
from .gadgets.behaviors.themable import Themable
from .gadgets.gadget import Gadget
from .geometry import Point, Size
from .rendering import render_root
from .terminal import Vt100Terminal, app_mode, get_platform_terminal
from .terminal.events import (
    Event,
    FocusEvent,
    KeyEvent,
    MouseButton,
    MouseEvent,
    PasteEvent,
    ResizeEvent,
)

__all__ = ["App", "run_gadget_as_app"]


class App(ABC):
    r"""
    Base for creating terminal applications.

    Parameters
    ----------
    bg_color : Color, default: BLACK
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
    render_mode : Literal["regions", "painter"], default: "regions"
        Determines how the gadget tree is rendered. ``"painter"`` fully paints every
        gadget back-to-front. ``"regions"`` only paints the visible portion of each
        gadget. ``"painter"`` may be more efficient for a large number of
        non-overlapping gadgets.

    Attributes
    ----------
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
    render_mode : Literal["regions", "painter"]
        Determines how the gadget tree is rendered.
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
        bg_color: Color = BLACK,
        title: str | None = None,
        inline: bool = False,
        inline_height: int = 10,
        color_theme: ColorTheme = DEFAULT_COLOR_THEME,
        double_click_timeout: float = 0.5,
        render_interval: float = 0.0,
        redirect_stderr: Path | None = None,
        render_mode: Literal["regions", "painter"] = "regions",
    ):
        self.root: _Root | None = None
        """Root of gadget tree (only set while app is running)."""
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
        self.render_mode = render_mode
        """Determines how the gadget tree is rendered."""
        self._inline_needs_clear: bool = False
        """Whether to clear terminal when switching to inline mode."""
        self._terminal: Vt100Terminal | None = None
        """Platform-specific terminal (only set while app is running)."""
        self._exit_value: Any = None
        """Value set by ``exit(exit_value)`` and returned by ``run()``."""

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
            f"    render_mode={self.render_mode!r},\n"
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
            height, _ = self._terminal.get_size()
            self.root.height = min(self.inline_height, height)
            if self._inline_needs_clear:
                self._terminal.move_cursor(Point(0, 0))
                self._terminal.erase_in_display()
                self._terminal.request_cursor_position_report()
            else:
                self._terminal.move_cursor()
        else:
            self.root.size = self._terminal.get_size()
            self._terminal.enter_alternate_screen()

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
    def bg_color(self) -> Color:
        """Background color of app."""
        return self._bg_color

    @bg_color.setter
    def bg_color(self, bg_color: Color):
        self._bg_color = bg_color
        if self.root is not None:
            self.root.bg_color = bg_color

    @property
    def render_mode(self) -> Literal["regions", "painter"]:
        """Render mode of app."""
        return self._render_mode

    @render_mode.setter
    def render_mode(self, render_mode: Literal["regions", "painter"]):
        self._render_mode = render_mode
        if self.root is not None:
            self.root.render_mode = render_mode

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
        self._inline_needs_clear = False
        terminal = self._terminal = get_platform_terminal()
        last_size: Size = terminal.get_size()
        self.root = root = _Root(
            app=self,
            render_mode=self.render_mode,
            bg_color=self.bg_color,
            size=last_size,
        )
        if self.inline:
            root.height = min(self.inline_height, last_size.height)

        last_mouse_button: MouseButton = "no_button"
        last_mouse_time = monotonic()
        last_mouse_nclicks = 0

        def determine_nclicks(mouse_event: MouseEvent) -> None:
            """Determine number of consecutive clicks for a `MouseEvent`."""
            nonlocal last_mouse_button, last_mouse_time, last_mouse_nclicks
            current_time = monotonic()

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
                    if (
                        event.key == "c"
                        and event.ctrl
                        and not event.alt
                        and not event.shift
                    ):
                        self.exit()
                        return
                    if (
                        not root.dispatch_key(event)
                        and event.key == "tab"
                        and not event.alt
                        and not event.ctrl
                    ):
                        if event.shift:
                            Focusable.focus_previous()
                        else:
                            Focusable.focus_next()
                elif isinstance(event, MouseEvent):
                    determine_nclicks(event)
                    if self.inline:
                        event.pos -= terminal.last_cursor_position_response
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
                        terminal.move_cursor(Point(0, 0))
                        terminal.erase_in_display()
                        terminal.request_cursor_position_report()
                        height, width = last_size
                        root.size = min(self.inline_height, height), width
                    else:
                        self._inline_needs_clear = True
                        root.size = event.size

        async def auto_render():
            """Render screen every :attr:`render_interval` seconds."""
            while True:
                root._render()
                render_root(root, terminal)
                await asyncio.sleep(self.render_interval)

        with app_mode(terminal, event_handler):
            terminal.request_cursor_position_report()
            if self.title:
                terminal.set_title(self.title)
            if not self.inline:
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
    bg_color: Color = BLACK,
    title: str | None = None,
    inline: bool = False,
    inline_height: int = 10,
    color_theme: ColorTheme = DEFAULT_COLOR_THEME,
    double_click_timeout: float = 0.5,
    render_interval: float = 0.0,
    redirect_stderr: Path | None = None,
    render_mode: Literal["regions", "painter"] = "regions",
) -> Any:
    """
    Run a gadget as an app.

    This convenience function provided for cases when the app would only have a single
    gadget.

    Parameters
    ----------
    gadget : Gadget
        A gadget to run as an app.
    bg_color : Color, default: BLACK
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
    render_mode : Literal["regions", "painter"], default: "regions"
        Determines how the gadget tree is rendered. ``"painter"`` fully paints every
        gadget back-to-front. ``"regions"`` only paints the visible portion of each
        gadget. ``"painter"`` may be more efficient for a large number of
        non-overlapping gadgets.
    """

    class _DefaultApp(App):
        async def on_start(self):
            self.add_gadget(gadget)

    return _DefaultApp(
        bg_color=bg_color,
        title=title,
        inline=inline,
        inline_height=inline_height,
        color_theme=color_theme,
        double_click_timeout=double_click_timeout,
        render_interval=render_interval,
        redirect_stderr=redirect_stderr,
        render_mode=render_mode,
    ).run()
