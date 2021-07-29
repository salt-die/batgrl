from abc import ABC, abstractmethod
import asyncio
from contextlib import contextmanager

from prompt_toolkit.input import create_input
from prompt_toolkit.output import create_output
from prompt_toolkit.utils import is_windows, is_conemu_ansi
from prompt_toolkit.keys import Keys

from .colors import BLACK_ON_BLACK
from .mouse.handler import create_vt100_mouse_event
from .widgets._root import _Root

ESCAPE_TIMEOUT = .05  # Seconds before we flush an escape character in the input queue.
POLL_INTERVAL = .5  # Seconds between polling for resize events.
REFRESH_INTERVAL = 0  # Seconds between screen redraws.


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

    Notes
    -----
    To create an app, inherit this class and implement the async method `on_start`. Typical
    use would be to add widgets to `self.root` and schedule those widgets' coroutines.

    Example
    -------
    ```py
    class MyApp(App):
        async def on_start(self):
            widget_1 = BouncingWidget(dim=(20, 20))
            widget_2 = BouncingWidget(dim=(10, 30))

            self.root.add_widgets(widget_1, widget_2)

            widget_1.start(velocity=1 + 1j, roll_axis=0)
            widget_2.start(velocity=-1 - 1j, roll_axis=1)

    MyApp().run()
    ```
    """
    def __init__(self, *, exit_key="escape", default_char=" ", default_color_pair=BLACK_ON_BLACK):
        self.exit_key = exit_key
        self.default_char = default_char
        self.default_color_pair = default_color_pair

    @abstractmethod
    async def on_start(self):
        """
        Coroutine scheduled when app is run.
        """

    def run(self):
        """
        Run the app.
        """
        if is_windows():
            from prompt_toolkit.output.windows10 import is_win_vt100_enabled

            if not is_win_vt100_enabled() and not is_conemu_ansi():
                raise RuntimeError("nurses not supported on non-vt100 enabled terminals")

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
        with create_environment() as (env_out, env_in):
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
                    if key.key == exit_key:
                        return self.exit()

                    if key.key == Keys.WindowsMouseEvent:
                        dispatch_click(key.data)
                    elif key.key == Keys.Vt100MouseEvent:
                        dispatch_click(create_vt100_mouse_event(key.data))
                    else:
                        dispatch_press(key)

                nonlocal flush_timer
                flush_timer.cancel()
                flush_timer = loop.call_later(ESCAPE_TIMEOUT, flush_input)

            def flush_input():
                """
                Flush input.
                """
                for key in env_in.flush_keys():
                    if key.key == exit_key:
                        return self.exit()

                    if key.key in MOUSE_EVENTS:
                        dispatch_click(create_mouse_event(key))
                    else:
                        dispatch_press(key)

            async def poll_size():
                """
                Poll terminal dimensions every `POLL_INTERVAL` seconds. Resize if dimensions have changed.
                """
                size = env_out.get_size()
                resize = root.resize

                while True:
                    await asyncio.sleep(POLL_INTERVAL)

                    new_size = env_out.get_size()
                    if size != new_size:
                        resize(new_size)
                        size = new_size

            async def auto_render():
                """
                Render screen every `REFRESH_INTERVAL` seconds.
                """
                render = root.render

                while True:
                    await asyncio.sleep(REFRESH_INTERVAL)
                    render()

            with env_in.raw_mode(), env_in.attach(read_from_input):
                await asyncio.gather(
                    poll_size(),
                    auto_render(),
                    self.on_start(),
                )


@contextmanager
def create_environment():
    """
    Enter alternate screen and create platform specific input. Restore screen and close input on exit.
    """
    env_out = create_output()

    env_out.enable_mouse_support()
    env_out.enter_alternate_screen()
    env_out.flush()

    env_in = create_input()
    if is_windows():
        from .mouse.patch_win32_input import patch_win32_input
        patch_win32_input(env_in)  # Better mouse handling patched in.
    env_in.flush_keys()  # Ignoring type-ahead

    try:
        yield env_out, env_in
    finally:
        env_in.flush_keys()
        env_in.close()

        env_out.quit_alternate_screen()
        env_out.reset_attributes()
        env_out.disable_mouse_support()
        env_out.flush()
