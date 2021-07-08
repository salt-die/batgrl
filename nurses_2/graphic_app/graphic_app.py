import asyncio

from ..app import (
    App as _App,
    create_environment,
    ESCAPE_TIMEOUT,
    POLL_INTERVAL,
    REFRESH_INTERVAL,
    MOUSE_EVENTS,
)
from ..colors import BLACK
from ..mouse import create_mouse_event

from .widgets._root import _GraphicRoot


class GraphicApp(_App):
    def __init__(self, *, exit_key="escape", default_color=BLACK):
        self.exit_key = exit_key
        self.default_color = default_color

    async def _run_async(self):
        """
        Build environment, create root, and schedule app-specific tasks.
        """
        with create_environment() as (env_out, env_in):
            exit_key = self.exit_key

            self.root = root = _GraphicRoot(
                app=self,
                env_out=env_out,
                default_color=self.default_color,
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

                    if key.key in MOUSE_EVENTS:
                        dispatch_click(create_mouse_event(key))
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
