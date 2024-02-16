import asyncio
from random import choice, random, randrange
from time import monotonic

from batgrl.app import run_gadget_as_app
from batgrl.gadgets.text import Text

CURVY = {
    0: "╷",
    1: "╴",
    2: "╵",
    3: "╶",
    (0, 0): "│",
    (0, 1): "╭",
    (0, 3): "╮",
    (1, 0): "╯",
    (1, 1): "─",
    (1, 2): "╮",
    (2, 1): "╰",
    (2, 2): "│",
    (2, 3): "╯",
    (3, 0): "╰",
    (3, 2): "╭",
    (3, 3): "─",
}

HEAVY = {
    0: "╻",
    1: "╸",
    2: "╹",
    3: "╺",
    (0, 0): "┃",
    (0, 1): "┏",
    (0, 3): "┓",
    (1, 0): "┛",
    (1, 1): "━",
    (1, 2): "┓",
    (2, 1): "┗",
    (2, 2): "┃",
    (2, 3): "┛",
    (3, 0): "┗",
    (3, 2): "┏",
    (3, 3): "━",
}


class Pipes(Text):
    def __init__(self, npipes: int = 5, **kwargs):
        super().__init__(**kwargs)
        self._npipes = npipes

    def reset_pipes(self):
        if self.root:
            self._pipe_task.cancel()
            self._pipe_task = asyncio.create_task(self.run_pipes())

    @property
    def npipes(self) -> int:
        return self._npipes

    @npipes.setter
    def npipes(self, value: int):
        self._npipes = value
        self.reset_pipes()

    def on_size(self):
        super().on_size()
        self.reset_pipes()

    def on_add(self):
        self._pipe_task = asyncio.create_task(self.run_pipes())
        super().on_add()

    def on_remove(self):
        self._pipe_task.cancel()
        super().on_remove()

    async def run_pipes(self):
        while True:
            self.canvas[:] = self.default_cell
            await asyncio.gather(*(self.pipe() for _ in range(self.npipes)))

    async def pipe(self):
        end = monotonic() + 10
        sleep = 0.02 + random() * 0.05
        color = randrange(255), randrange(255), randrange(255)
        y, x = randrange(self.height), randrange(self.width)
        last_dir = randrange(4)
        pipe_chars = choice([HEAVY, CURVY])

        while monotonic() < end:
            self.canvas[y, x]["char"] = pipe_chars[last_dir]
            self.canvas["fg_color"][y, x] = color
            await asyncio.sleep(sleep)

            current_dir = (last_dir + randrange(-1, 2)) % 4
            self.canvas[y, x]["char"] = pipe_chars[last_dir, current_dir]
            self.canvas["fg_color"][y, x] = color

            match current_dir:
                case 0:
                    y = (y - 1) % self.height
                case 1:
                    x = (x + 1) % self.width
                case 2:
                    y = (y + 1) % self.height
                case 3:
                    x = (x - 1) % self.width

            await asyncio.sleep(sleep)
            last_dir = current_dir


if __name__ == "__main__":
    run_gadget_as_app(
        Pipes(npipes=5, size_hint={"height_hint": 1.0, "width_hint": 1.0})
    )
