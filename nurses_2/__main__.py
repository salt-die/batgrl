"""
For temporary testing.  This file will be removed.

`esc` to exit.

"""
import asyncio
from itertools import cycle, product

from .app import App


class MyApp(App):
    def build(self):
        self.kb.add('escape')(lambda event: self.exit())

        # No widgets yet :(

    async def on_start(self):
        env_out = self.env_out
        rows, columns = env_out.get_size()
        some_text = cycle('NURSES!')

        while True:
            for y, x in product(range(rows), range(columns)):
                env_out.cursor_goto(y, x)
                env_out.write(next(some_text))

            next(some_text)

            env_out.flush()

            await asyncio.sleep(.05)

MyApp().run()
