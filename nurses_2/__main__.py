"""
For temporary testing.  This file will be removed.

`esc` to exit.

"""
import asyncio
from itertools import cycle

from prompt_toolkit.styles import Attrs

from .app import App

RED = Attrs(color='ff0000', bgcolor='', bold=False, underline=False, italic=False, blink=False, reverse=False, hidden=False)
BLUE = Attrs(color='0000ff', bgcolor='', bold=False, underline=False, italic=False, blink=False, reverse=False, hidden=False)


class MyApp(App):
    def build(self):
        self.kb.add('escape')(lambda event: self.exit())

        # No widgets yet :(

    async def on_start(self):
        env_out = self.env_out
        depth = env_out.get_default_color_depth()

        some_text = cycle('NURSES!')
        colors = cycle((RED, BLUE))

        while True:
            rows, columns = env_out.get_size()
            # This loop will be the basis for our screen's `addstr` method.
            for y in range(rows):
                env_out.cursor_goto(y, 0)

                for x in range(columns):
                    env_out.set_attributes(next(colors), depth)
                    env_out.write(next(some_text))

            next(some_text)

            env_out.flush()

            await asyncio.sleep(0)

MyApp().run()
