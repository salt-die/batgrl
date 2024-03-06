"""Base for creating terminal applications."""
import asyncio
import platform
import sys
from abc import ABC, abstractmethod
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from time import monotonic
from types import ModuleType
from typing import Literal

from .colors import BLACK, DEFAULT_COLOR_THEME, Color, ColorTheme
from .gadgets._root import _Root
from .gadgets.behaviors.focusable import Focusable
from .gadgets.behaviors.themable import Themable
from .gadgets.gadget import Gadget, Size
from .io import (
    Key,
    KeyEvent,
    MouseButton,
    MouseEvent,
    MouseEventType,
    PasteEvent,
    _PartialMouseEvent,
)
from .io.output.vt100 import Vt100_Output

__all__ = ["App", "run_gadget_as_app"]


class App(ABC):
    r"""
    Base for creating terminal applications.

    Parameters
    ----------
    bg_color : Color, default: BLACK
        Background color of app.
    title : str | None, default: None
        Set terminal title (if supported).
    double_click_timeout : float, default: 0.5
        Max duration of a double-click. Max duration of a triple-click
        is double this value.
    render_interval : float, default: 0.0
        Seconds between screen renders.
    color_theme : ColorTheme, default: DEFAULT_COLOR_THEME
        Color theme used for :class:`batgrl.gadgets.behaviors.themable.Themable`
        gadgets.
    asciicast_path : Path | None, default: None
        Record the terminal in asciicast v2 file format if a path is provided.
        Resizing the terminal while recording isn't currently supported by
        the asciicast format -- doing so will corrupt the recording.
    redirect_stderr : Path | None, default: None
        If provided, stderr is written to this path.
    render_mode : Literal["regions", "painter"], default: "regions"
        Determines how the gadget tree is rendered. "painter" fully paints every gadget
        back-to-front. "regions" only paints the visible portion of each gadget.
        "painter" may be more efficient for a large number of non-overlapping gadgets.

    Attributes
    ----------
    bg_color : Color
        Background color of app.
    title : str | None
        The terminal's title (if supported).
    double_click_timeout : float
        Max duration of a double-click. Max duration of a triple-click
        is double this value.
    render_interval : float
        Seconds between screen renders.
    color_theme : ColorTheme
        Color theme used for :class:`batgrl.gadgets.behaviors.themable.Themable`
        gadgets.
    asciicast_path : Path | None
        Path where asciicast recording will be saved.
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
    exit()
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
        double_click_timeout: float = 0.5,
        render_interval: float = 0.0,
        color_theme: ColorTheme = DEFAULT_COLOR_THEME,
        asciicast_path: Path | None = None,
        redirect_stderr: Path | None = None,
        render_mode: Literal["regions", "painter"] = "regions",
    ):
        self.root = None

        self.bg_color = bg_color
        self.title = title
        self.double_click_timeout = double_click_timeout
        self.render_interval = render_interval
        self.color_theme = color_theme
        self.asciicast_path = asciicast_path
        self.redirect_stderr = redirect_stderr
        self.render_mode = render_mode

    def __repr__(self):
        return (
            f"{type(self).__name__}(\n"
            f"    bg_color={(*self.bg_color,)},\n"
            f"    title={self.title!r},\n"
            f"    double_click_timeout={self.double_click_timeout},\n"
            f"    render_interval={self.render_interval},\n"
            f"    asciicast_path={self.asciicast_path},\n"
            f"    redirect_stderr={self.redirect_stderr},\n"
            f"    render_mode={self.render_mode!r},\n"
            ")"
        )

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

    def run(self):
        """Run the app."""
        try:
            with redirect_stderr(StringIO()) as defer_stderr:
                asyncio.run(self._run_async())
        except asyncio.CancelledError:
            pass
        finally:
            if self.redirect_stderr:
                with open(self.redirect_stderr, "w") as errors:
                    print(defer_stderr.getvalue(), file=errors, end="")
            else:
                print(defer_stderr.getvalue(), file=sys.stderr, end="")

    def exit(self):
        """Exit the app."""
        if self.root is not None:
            self.root.destroy()
            self.root = None

        try:
            tasks = asyncio.all_tasks()
        except RuntimeError:
            pass
        else:
            for task in tasks:
                task.cancel()

    def _create_io(self) -> tuple[ModuleType, Vt100_Output]:
        """Return platform specific io."""
        if not sys.stdin.isatty():
            raise RuntimeError("Interactive terminal required.")

        if platform.system() == "Windows":
            from .io.output.windows import WindowsOutput, is_vt100_enabled

            if not is_vt100_enabled():
                raise RuntimeError(
                    "batgrl not supported on non-vt100 enabled terminals"
                )

            from .io.input.win32 import win32_input

            return win32_input, WindowsOutput(self.asciicast_path)

        else:
            from .io.input.vt100 import vt100_input
            from .io.output.vt100 import Vt100_Output

            return vt100_input, Vt100_Output(self.asciicast_path)

    async def _run_async(self):
        """Build environment, create root, and schedule app-specific tasks."""
        env_in, env_out = self._create_io()
        with env_out:
            self.root = root = _Root(
                app=self,
                render_mode=self.render_mode,
                bg_color=self.bg_color,
                size=env_out.get_size(),
            )

            if self.title:
                env_out.set_title(self.title)

            dispatch_key = root.dispatch_key
            dispatch_mouse = root.dispatch_mouse
            dispatch_paste = root.dispatch_paste

            last_mouse_button = MouseButton.NO_BUTTON
            last_mouse_time = monotonic()
            last_mouse_nclicks = 0

            def determine_nclicks(
                partial_mouse_event: _PartialMouseEvent,
            ) -> MouseEvent:
                """
                Determine number of consecutive clicks for a :class:`_PartialMouseEvent`
                and create a :class:`MouseEvent`.
                """
                nonlocal last_mouse_button, last_mouse_time, last_mouse_nclicks
                current_time = monotonic()

                if partial_mouse_event.event_type is not MouseEventType.MOUSE_DOWN:
                    return MouseEvent(*partial_mouse_event, 0)

                if (
                    last_mouse_button is not partial_mouse_event.button
                    or current_time - last_mouse_time > self.double_click_timeout
                ):
                    last_mouse_button = partial_mouse_event.button
                    last_mouse_nclicks = 1
                else:
                    last_mouse_nclicks = last_mouse_nclicks % 3 + 1

                last_mouse_time = current_time
                return MouseEvent(*partial_mouse_event, last_mouse_nclicks)

            def read_from_input():
                """Read and process input."""
                for event in env_in.events():
                    match event:
                        case KeyEvent.CTRL_C:
                            self.exit()
                            return
                        case KeyEvent():
                            if not dispatch_key(event) and event.key is Key.Tab:
                                if event.mods.shift:
                                    Focusable.focus_previous()
                                else:
                                    Focusable.focus_next()
                        case _PartialMouseEvent():
                            mouse_event = determine_nclicks(event)
                            dispatch_mouse(mouse_event)
                        case PasteEvent():
                            dispatch_paste(event)
                        case Size():
                            root.size = event

            async def auto_render():
                """Render screen every :attr:`render_interval` seconds."""
                while True:
                    root._render()
                    env_out.render_frame(root)
                    await asyncio.sleep(self.render_interval)

            with env_in.raw_mode(), env_in.attach(read_from_input):
                await asyncio.gather(self.on_start(), auto_render())

    def add_gadget(self, gadget: Gadget):
        """
        Alias for :attr:`root.add_gadget`.

        Parameters
        ----------
        gadget : Gadget
            A gadget to add as a child to the root gadget.
        """
        self.root.add_gadget(gadget)

    def add_gadgets(self, *gadgets: Gadget):
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


def run_gadget_as_app(gadget: Gadget):
    """
    Run a gadget as a full-screen app.

    Parameters
    ----------
    gadget : Gadget
        A gadget to run as a full screen app.
    """

    class _DefaultApp(App):
        async def on_start(self):
            self.add_gadget(gadget)

    _DefaultApp(title=type(gadget).__name__).run()
