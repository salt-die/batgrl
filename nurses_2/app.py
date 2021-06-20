from abc import ABC, abstractmethod
import asyncio
from contextlib import contextmanager

from prompt_toolkit.key_binding.key_bindings import Binding
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyProcessor
from prompt_toolkit.input import create_input
from prompt_toolkit.output import create_output

from .widgets import Widget

ESCAPE_TIMEOUT = .05  # Seconds before we flush an escape character in the input queue.
POLL_INTERVAL = .5  # Seconds between polling for resize events.
REFRESH_INTERVAL = 0  # Seconds between screen redraws.


class App(ABC):
    """Base for creating terminal applications.
    """
    @abstractmethod
    def build(self):
        """Build and return the root widget for the app.
        """

    @abstractmethod
    async def on_start(self):
        """Main coroutine. Event loop starts here.
        """

    def run(self):
        """Run the app.
        """
        try:
            asyncio.run(self._run_async())
        except asyncio.CancelledError:
            pass

    def exit(self):
        for task in asyncio.all_tasks():
            task.cancel()

    def _on_resize(self):
        """Adjust widget geometry and redraw the screen.
        """
        # self.root.update_geometry()  # TODO: Uncomment once widgets are implemented.
        self._refresh()

    def _refresh(self):
        """Redraw the screen.
        """

    async def _run_async(self):
        """Create root widget and schedule input reading, size polling, auto-refreshing, and finally, `on_start`.
        """
        with create_environment() as (env_out, env_in):
            self.env_out = env_out
            self.env_in = env_in

            self.kb = kb = KeyBindings()
            self.key_processor = key_processor = KeyProcessor(kb)

            loop = asyncio.get_event_loop()
            flush_timer = asyncio.TimerHandle(0, lambda: None, (), loop)  # dummy handle; this so we can avoid a conditional in `read_from_input`

            self.root = self.build()
            # assert isinstance(self.root, Widget), f"expected Widget, got {type(self.root).__name__}"  # TODO: Uncomment once widgets are implemented.

            def read_from_input():
                """Read and process input.
                """
                keys = env_in.read_keys()

                key_processor.feed_multiple(keys)
                key_processor.process_keys()

                nonlocal flush_timer
                flush_timer.cancel()
                flush_timer = loop.call_later(ESCAPE_TIMEOUT, flush_input)

            def flush_input():
                """Flush input.
                """
                keys = env_in.flush_keys()

                key_processor.feed_multiple(keys)
                key_processor.process_keys()

            async def poll_size():
                """Poll terminal dimensions every `POLL_INTERVAL` seconds and resize if dimensions have changed.
                """
                size = env_out.get_size()
                on_resize = self._on_resize

                while True:
                    await asyncio.sleep(POLL_INTERVAL)

                    new_size = env_out.get_size()
                    if size != new_size:
                        on_resize()
                        size = new_size

            async def auto_refresh():
                """Redraw the screen every `REFRESH_INTERVAL` seconds.
                """
                refresh = self._refresh

                while True:
                    await asyncio.sleep(REFRESH_INTERVAL)
                    refresh()

            with env_in.raw_mode(), env_in.attach(read_from_input):
                await asyncio.gather(
                    poll_size(),
                    auto_refresh(),
                    self.on_start(),
                )


################################################# W ###
# A hack to avoid prompt-toolkit's `App` class. # A ###
def call(self, event):                          # R ###
    if result := self.handler(event):           # N ###
        asyncio.create_task(result)             # I ###
                                                # N ###
Binding.call = call                             # G ###
################################################# ! ###

@contextmanager
def create_environment():
    """Platform specific output/input. Restores output and closes/flushes input on exit.
    """
    env_out = create_output()
    env_out.enter_alternate_screen()
    env_out.hide_cursor()
    env_out.flush()

    env_in = create_input()
    env_in.flush_keys()  # Ignoring type-ahead

    try:
        yield env_out, env_in
    finally:
        env_in.flush_keys()
        env_in.close()

        env_out.scroll_buffer_to_prompt()
        env_out.quit_alternate_screen()
        env_out.flush()
