from abc import ABC, abstractmethod
import asyncio
from contextlib import contextmanager

from .colors import BLACK_ON_BLACK
from .io import create_io, PasteEvent, MouseEvent
from .widgets._root import _Root

FLUSH_TIMEOUT        = 0.05  # Seconds before we flush an escape character in the input queue.
RESIZE_POLL_INTERVAL = 0.5   # Seconds between polling for resize events.
RENDER_INTERVAL      = 0     # Seconds between screen renders.


class App(ABC):
    """
    Base for creating terminal applications.

    Parameters
    ----------
    exit_key : Optional[str], default: "escape"
        Quit the app when this key is pressed. Use None to disable exit_key (not recommended).
        If the exit key is modified while the app is running, the app will still use the old key
        until it exits.
    default_char : str, default: " "
        Default background character for root widget.
    default_color_pair : ColorPair, default: BLACK_ON_BLACK
        Default background color pair for root widget.
    title : Optional[str], default: None
        Set terminal title if supported.

    Notes
    -----
    To create an app, inherit this class and implement the async method `on_start`. Typical
    use would be to add widgets to `self.root` (the root of the widget tree) and schedule those widgets'
    coroutines. `on_start` is scheduled concurrently so it may run indefinitely if needed.

    Example
    -------
    ```py
    class MyApp(App):
        async def on_start(self):
            widget_1 = BouncingWidget(size=(20, 20))
            widget_2 = BouncingWidget(size=(10, 30))

            self.root.add_widgets(widget_1, widget_2)

            widget_1.start(velocity=1 + 1j, roll_axis=0)
            widget_2.start(velocity=-1 - 1j, roll_axis=1)

    MyApp().run()
    ```
    """
    def __init__(self, *, exit_key="escape", default_char=" ", default_color_pair=BLACK_ON_BLACK, title=None):
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
        with create_environment(self.title) as (env_out, env_in):
            exit_key = self.exit_key

            self.root = root = _Root(
                app=self,
                env_out=env_out,
                default_char=self.default_char,
                default_color_pair=self.default_color_pair,
            )
            dispatch_press = root.dispatch_press
            dispatch_click = root.dispatch_click

            loop = asyncio.get_event_loop()
            flush_timer = asyncio.TimerHandle(0, lambda: None, (), loop)  # dummy handle

            def read_from_input():
                """
                Read and process input.
                """
                for key in env_in.read_keys():
                    if key == exit_key:
                        return self.exit()

                    if isinstance(key, MouseEvent):
                        dispatch_click(key)
                    elif isinstance(key, PasteEvent):
                        pass  # TODO: Add a Widget method to handle pastes.
                    else:
                        dispatch_press(key)

                nonlocal flush_timer
                flush_timer.cancel()
                flush_timer = loop.call_later(FLUSH_TIMEOUT, flush_input)

            def flush_input():
                """
                Flush input.
                """
                for key in env_in.flush_keys():
                    if key == exit_key:
                        return self.exit()

                    if isinstance(key, MouseEvent):
                        dispatch_click(key)
                    elif isinstance(key, PasteEvent):
                        pass  # TODO: Add a Widget method to handle pastes.
                    else:
                        dispatch_press(key)

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


@contextmanager
def create_environment(title):
    """
    Enter alternate screen and create platform specific input. Restore screen and close input on exit.
    """
    env_in, env_out = create_io()

    try:
        env_out.enable_mouse_support()
        env_out.enter_alternate_screen()
        if title is not None:
            env_out.set_title(title)
        env_out.flush()

        env_in.flush_keys()  # Ignoring type-ahead

        yield env_out, env_in
    finally:
        env_in.flush_keys()

        env_out.quit_alternate_screen()
        env_out.reset_attributes()
        env_out.disable_mouse_support()
        env_out.flush()
        env_out.restore_console()
