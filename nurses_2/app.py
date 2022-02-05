import asyncio
from abc import ABC, abstractmethod

from .colors import BLACK_ON_BLACK
from .io import KeyPressEvent, MouseEvent, PasteEvent, io
from .widgets._root import _Root
from .widgets._widget_base import _WidgetBase

__all__ = "App", "run_widget_as_app"

RESIZE_POLL_INTERVAL = 0.5   # Seconds between polling for resize events.
RENDER_INTERVAL      = 0     # Seconds between screen renders.


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
    """
    def __init__(
        self,
        *,
        exit_key=KeyPressEvent.ESCAPE,
        default_char=" ",
        default_color_pair=BLACK_ON_BLACK,
        title=None
    ):
        self.exit_key = exit_key
        self.default_char = default_char
        self.default_color_pair = default_color_pair
        self.title = title

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
            dispatch_paste = root.dispatch_paste

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
                        case KeyPressEvent():
                            dispatch_press(key)
                        case PasteEvent():
                            dispatch_paste(key)

            async def poll_size():
                """
                Poll terminal size every `RESIZE_POLL_INTERVAL` seconds.
                """
                size = env_out.get_size()
                resize = root.resize

                while True:
                    await asyncio.sleep(RESIZE_POLL_INTERVAL)

                    new_size = env_out.get_size()
                    if size != new_size:
                        resize(new_size)
                        size = new_size

            async def auto_render():
                """
                Render screen every `RENDER_INTERVAL` seconds.
                """
                render = root.render

                while True:
                    await asyncio.sleep(RENDER_INTERVAL)
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


def run_widget_as_app(widget: type[_WidgetBase], *args, **kwargs):
    """
    Run a widget as a full-screen app.

    Parameters
    ----------
    widget : type[_WidgetBase]
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
