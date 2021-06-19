"""
For temporary testing.  This file will be removed.

`esc` to exit.

"""
import asyncio
from itertools import cycle

from .app import App


class MyApp(App):
    def build(self):
        self.kb.add('escape')(lambda event: self.exit())

        # No widgets yet :(

    async def on_start(self):
        env_out = self.env_out
        some_text = cycle('NURSES!')

        while True:
            rows, columns = env_out.get_size()
            # This loop will be the basis for our screen's `addstr` method.
            for y in range(rows):
                env_out.cursor_goto(y, 0)

                for x in range(columns):
                    # env_out.write_raw("escape sequence")
                    env_out.write(next(some_text))

            next(some_text)

            env_out.flush()

            await asyncio.sleep(.05)

MyApp().run()
