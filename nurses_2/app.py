"""
Base for creating terminal applications.
"""
import asyncio
import sys
from abc import ABC, abstractmethod
from io import StringIO
from contextlib import redirect_stderr
from pathlib import Path
from time import monotonic

from .colors import BLACK_ON_BLACK, DEFAULT_COLOR_THEME, ColorPair, ColorTheme
from .io import (
    _PartialMouseEvent,
    KeyEvent,
    MouseButton,
    MouseEvent,
    MouseEventType,
    PasteEvent,
    io,
)
from .widgets._root import _Root
from .widgets.behaviors.themable import Themable
from .widgets.widget import Widget, Size

__all__ = "App", "run_widget_as_app"


class App(ABC):
    """
    Base for creating terminal applications.

    Parameters
    ----------
    background_char : str, default: " "
        Background character for root widget.
    background_color_pair : ColorPair, default: BLACK_ON_BLACK
        Background color pair for root widget.
    title : str | None, default: None
        Set terminal title (if supported).
    double_click_timeout : float, default: 0.5
        Max duration of a double-click. Max duration of a triple-click
        is double this value.
    render_interval : float, default: 0.0
        Seconds between screen renders.
    color_theme : ColorTheme, default: DEFAULT_COLOR_THEME
        Color theme used for :class:`nurses_2.widgets.behaviors.themable.Themable` widgets.
    asciicast_path : Path | None, default: None
        Record the terminal in asciicast v2 file format if a path is provided.
        Resizing the terminal while recording isn't currently supported by
        the asciicast format -- doing so will corrupt the recording.

    Attributes
    ----------
    background_char : str
        Background character for root widget.
    background_color_pair : ColorPair
        Background color pair for root widget.
    title : str | None
        The terminal's title (if supported).
    double_click_timeout : float
        Max duration of a double-click. Max duration of a triple-click
        is double this value.
    render_interval : float
        Seconds between screen renders.
    color_theme : ColorTheme
        Color theme used for :class:`nurses_2.widgets.behaviors.themable.Themable` widgets.
    asciicast_path : Path | None
        Path where asciicast recording will be saved.
    root : _Root | None
        Root of widget tree.
    children : list[Widget]
        Alias for :attr:`root.children`.

    Methods
    -------
    on_start:
        Coroutine scheduled when app is run.
    run:
        Run the app.
    exit:
        Exit the app.
    add_widget:
        Alias for :attr:`root.add_widget`.
    add_widgets:
        Alias for :attr:`root.add_widgets`.

    """
    def __init__(
        self,
        *,
        background_char: str=" ",
        background_color_pair: ColorPair=BLACK_ON_BLACK,
        title: str | None=None,
        double_click_timeout: float=0.5,
        render_interval: float=0.0,
        color_theme: ColorTheme=DEFAULT_COLOR_THEME,
        asciicast_path: Path | None=None,
    ):
        self.root = None

        self.background_char = background_char
        self.background_color_pair = background_color_pair
        self.title = title
        self.double_click_timeout = double_click_timeout
        self.render_interval = render_interval
        self.color_theme = color_theme
        self.asciicast_path = asciicast_path

    @property
    def color_theme(self) -> ColorTheme:
        return Themable.color_theme

    @color_theme.setter
    def color_theme(self, color_theme: ColorTheme):
        Themable.color_theme = color_theme

        if self.root is not None:
            for widget in self.root.walk():
                if isinstance(widget, Themable):
                    widget.update_theme()

    @abstractmethod
    async def on_start(self):
        """
        Coroutine scheduled when app is run.
        """

    def run(self):
        """
        Run the app.
        """
        try:
            with redirect_stderr(StringIO()) as defer_stderr:
                asyncio.run(self._run_async())
        except asyncio.CancelledError:
            pass
        finally:
            print(defer_stderr.getvalue(), file=sys.stderr, end="")

    def exit(self):
        """
        Exit the app.
        """
        self.root.destroy()
        for task in asyncio.all_tasks():
            task.cancel()

    async def _run_async(self):
        """
        Build environment, create root, and schedule app-specific tasks.
        """
        with io(self.asciicast_path) as (env_in, env_out):
            self.root = root = _Root(
                app=self,
                env_out=env_out,
                background_char=self.background_char,
                background_color_pair=self.background_color_pair,
            )

            if self.title:
                env_out.set_title(self.title)

            dispatch_key = root.dispatch_key
            dispatch_mouse = root.dispatch_mouse
            dispatch_paste = root.dispatch_paste

            last_mouse_button = MouseButton.NO_BUTTON
            last_mouse_time = monotonic()
            last_mouse_nclicks = 0

            def determine_nclicks(partial_mouse_event: _PartialMouseEvent) -> MouseEvent:
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
                """
                Read and process input.
                """
                for event in env_in.events():
                    match event:
                        case KeyEvent.CTRL_C:
                            self.exit()
                            return
                        case KeyEvent():
                            dispatch_key(event)
                        case _PartialMouseEvent():
                            mouse_event = determine_nclicks(event)
                            dispatch_mouse(mouse_event)
                        case PasteEvent():
                            dispatch_paste(event)
                        case Size():
                            root.size = event

            async def auto_render():
                """
                Render screen every :attr:`render_interval` seconds.
                """
                render = root.render

                while True:
                    await asyncio.sleep(self.render_interval)
                    render()

            with env_in.raw_mode(), env_in.attach(read_from_input):
                await asyncio.gather(auto_render(), self.on_start())

    def add_widget(self, widget):
        """
        Alias for :attr:`root.add_widget`.
        """
        self.root.add_widget(widget)

    def add_widgets(self, *widgets):
        """
        Alias for :attr:`root.add_widgets`.
        """
        self.root.add_widgets(*widgets)

    @property
    def children(self):
        """
        Alias for :attr:`root.children`.
        """
        return self.root.children


def run_widget_as_app(widget: Widget):
    """
    Run a widget as a full-screen app.

    Parameters
    ----------
    widget : Widget
        A widget to run as a full screen app.
    """
    class _DefaultApp(App):
        async def on_start(self):
            self.add_widget(widget)

    _DefaultApp(title=type(widget).__name__).run()
