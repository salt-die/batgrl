import asyncio
from abc import ABC, abstractmethod
from time import monotonic

from nurses_2.io.input.events import MouseButton

from .colors import BLACK_ON_BLACK, DEFAULT_COLOR_THEME, ColorPair, ColorTheme
from .io import KeyPressEvent, MouseButton, MouseEvent, MouseEventType, PasteEvent, io
from .widgets._root import _Root
from .widgets.behaviors.themable import Themable
from .widgets.widget_base import WidgetBase

__all__ = "App", "run_widget_as_app"


class App(ABC):
    """
    Base for creating terminal applications.

    Parameters
    ----------
    exit_key : KeyPressEvent | None, default: KeyPressEvent.ESCAPE
        Quit the app when this key is pressed.
    default_char : str, default: " "
        Default background character for root widget.
    default_color_pair : ColorPair, default: BLACK_ON_BLACK
        Default background color pair for root widget.
    title : str | None, default: None
        Set terminal title (if supported).
    double_click_timeout : float, default: 0.5
        Max duration of a double-click. Max duration of a triple-click
        is double this value.
    resize_poll_interval : float, default: 0.5
        Seconds between polling for resize events.
    render_interval : float, default: 0.0
        Seconds between screen renders.
    color_theme : ColorTheme, default: DEFAULT_COLOR_THEME
        Color theme used for `Themable` widgets.
    """
    def __init__(
        self,
        *,
        exit_key: KeyPressEvent | None=KeyPressEvent.ESCAPE,
        default_char: str=" ",
        default_color_pair: ColorPair=BLACK_ON_BLACK,
        title: str | None=None,
        double_click_timeout: float=0.5,
        resize_poll_interval: float=0.5,
        render_interval: float=0.0,
        color_theme: ColorTheme=DEFAULT_COLOR_THEME,
    ):
        self.root = None

        self.exit_key = exit_key
        self.default_char = default_char
        self.default_color_pair = default_color_pair
        self.title = title
        self.double_click_timeout = double_click_timeout
        self.resize_poll_interval = resize_poll_interval
        self.render_interval = render_interval
        self.color_theme = color_theme

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
            asyncio.run(self._run_async())
        except asyncio.CancelledError:
            pass

    def exit(self):
        for task in asyncio.all_tasks():
            task.cancel()

    async def _run_async(self):
        """
        Build environment, create root, and schedule app-specific tasks.
        """
        with io() as (env_in, env_out):
            self.root = root = _Root(
                app=self,
                env_out=env_out,
                default_char=self.default_char,
                default_color_pair=self.default_color_pair,
            )

            if self.title:
                env_out.set_title(self.title)

            dispatch_press = root.dispatch_press
            dispatch_click = root.dispatch_click
            dispatch_double_click = root.dispatch_double_click
            dispatch_triple_click = root.dispatch_triple_click
            dispatch_paste = root.dispatch_paste

            last_click_info = MouseEvent(None, None, MouseButton.NO_BUTTON, None), monotonic(), 0  # last key, timestamp, total clicks

            def determine_click_dispatch(key):
                """
                Determine if a click is a double-click or a triple-click.
                """
                nonlocal last_click_info
                last_event, timestamp, nclicks = last_click_info

                current_time = monotonic()

                if (
                    last_event.button is not key.button
                    or current_time - timestamp > self.double_click_timeout
                    or nclicks == 0
                ):
                    last_click_info = key, current_time, 1
                elif nclicks == 1:
                    dispatch_double_click(key)
                    last_click_info = key, current_time, 2
                elif nclicks == 2:
                    dispatch_triple_click(key)
                    last_click_info = key, current_time, 0  # Reset click count

            def read_from_input():
                """
                Read and process input.
                """
                for key in env_in.read_keys():
                    match key:
                        case self.exit_key:
                            return self.exit()
                        case MouseEvent():
                            dispatch_click(key)
                            if key.event_type is MouseEventType.MOUSE_DOWN:
                                determine_click_dispatch(key)
                        case KeyPressEvent():
                            dispatch_press(key)
                        case PasteEvent():
                            dispatch_paste(key)

            async def poll_size():
                """
                Poll terminal size every `resize_poll_interval` seconds.
                """
                size = env_out.get_size()
                resize = root.resize

                while True:
                    await asyncio.sleep(self.resize_poll_interval)

                    new_size = env_out.get_size()
                    if size != new_size:
                        resize(new_size)
                        size = new_size

            async def auto_render():
                """
                Render screen every `render_interval` seconds.
                """
                render = root.render

                while True:
                    await asyncio.sleep(self.render_interval)
                    render()

            with env_in.raw_mode(), env_in.attach(read_from_input):
                await asyncio.gather(
                    poll_size(),
                    auto_render(),
                    self.on_start(),
                )

    def add_widget(self, widget):
        self.root.add_widget(widget)

    def add_widgets(self, *widgets):
        self.root.add_widgets(*widgets)

    @property
    def children(self):
        return self.root.children


def run_widget_as_app(widget: type[WidgetBase], *args, **kwargs):
    """
    Run a widget as a full-screen app.

    Parameters
    ----------
    widget : type[WidgetBase]
        Widget type to be instantiated and run as an app.

    *args
        Positional arguments for widget instantiation.

    **kwargs
        Keyword arguments for widget instantiation.

    Notes
    -----
    This is a convenience function provided to reduce boilerplate
    for the simplest case of an App. The widget type is provided
    instead of an instance to cover cases where the widget schedules
    tasks on instantiation as no event loop exists before the App is
    created.
    """
    class _DefaultApp(App):
        async def on_start(self):
            self.add_widget(widget(*args, **kwargs))

    _DefaultApp().run()
