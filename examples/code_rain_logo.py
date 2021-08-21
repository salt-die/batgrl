"""
Credit for ascii art logo to Matthew Barber (https://ascii.matthewbarber.io/art/python/)
"""
import asyncio

import numpy as np
from numpy.random import default_rng

from nurses_2.app import App
from nurses_2.colors import (
    Color,
    color_pair,
    gradient,
    BLACK,
    GREEN,
    WHITE,
    WHITE_ON_BLACK,
    BLACK_ON_BLACK,
)
from nurses_2.widgets import Widget

LOGO = """
                   _.gj8888888lkoz.,_
                d888888888888888888888b,
               j88P""V8888888888888888888
               888    8888888888888888888
               888baed8888888888888888888
               88888888888888888888888888
                            8888888888888
    ,ad8888888888888888888888888888888888  888888be,
   d8888888888888888888888888888888888888  888888888b,
  d88888888888888888888888888888888888888  8888888888b,
 j888888888888888888888888888888888888888  88888888888p,
j888888888888888888888888888888888888888'  8888888888888
8888888888888888888888888888888888888^"   ,8888888888888
88888888888888^'                        .d88888888888888
8888888888888"   .a8888888888888888888888888888888888888
8888888888888  ,888888888888888888888888888888888888888^
^888888888888  888888888888888888888888888888888888888^
 V88888888888  88888888888888888888888888888888888888Y
  V8888888888  8888888888888888888888888888888888888Y
   `"^8888888  8888888888888888888888888888888888^"'
               8888888888888
               88888888888888888888888888
               8888888888888888888P""V888
               8888888888888888888    888
               8888888888888888888baed88V
                `^888888888888888888888^
                  `'"^^V888888888V^^'
"""
SIZE = 28, 56           # Size of LOGO
CODE_RAIN_HEIGHT = 8    # The height of the trail of the code rain + 1,  this should be divisible by 2
LAST_RAINFALL = 25      # Number of seconds until the last rain drops.
FALL_TIME = .2          # Seconds until rain falls another row
RANDOM_CHARACTERS = list('=^74xt2ZI508')

# Colors
GREEN_ON_BLACK = color_pair(GREEN, BLACK)

BLUE = Color(48, 105, 152)
BLUE_ON_BLACK = color_pair(BLUE, BLACK)
WHITE_TO_BLUE = gradient(25, WHITE_ON_BLACK, BLUE_ON_BLACK)

YELLOW = Color(255, 212, 59)
YELLOW_ON_BLACK = color_pair(YELLOW, BLACK)
WHITE_TO_YELLOW = gradient(25, WHITE_ON_BLACK, YELLOW_ON_BLACK)

def generate_delays():
    rng = default_rng()
    random = rng.laplace(size=SIZE)
    scale = random.max() - random.min()
    random = 1 - (random - random.min()) / scale
    random *= LAST_RAINFALL
    return np.sort(random, axis=0)[::-1]


class CodeRain(Widget):
    GRADIENT = (
        gradient(CODE_RAIN_HEIGHT // 2, BLACK_ON_BLACK, GREEN_ON_BLACK)
        + gradient(CODE_RAIN_HEIGHT // 2, GREEN_ON_BLACK, WHITE_ON_BLACK)
    )

    drops_falling= 0

    def __init__(self, column, target_row, character, gradient, delay, **kwargs):
        kwargs.pop('is_transparent', None)

        super().__init__(
            size=(CODE_RAIN_HEIGHT, 1),
            pos=(-CODE_RAIN_HEIGHT, column),
            is_transparent=True,
            **kwargs,
        )

        self.colors[:, 0] = self.GRADIENT

        self.target_row = target_row
        self.character = character
        self.gradient = gradient
        self.delay = delay

    def start(self):
        self._random_char_task = asyncio.create_task(self.random_char())
        asyncio.create_task(self.fall())

        CodeRain.drops_falling += 1

    async def random_char(self):
        """
        Select a random character.
        """
        while True:
            self.canvas[-1, 0] = np.random.choice(RANDOM_CHARACTERS)

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

    async def fall(self):
        """
        Fall down the screen.
        """
        await asyncio.sleep(self.delay)

        self.parent.pull_to_front(self)

        for _ in range(self.target_row + 1):
            self.canvas[:-1] = self.canvas[1:]
            self.top += 1
            await asyncio.sleep(FALL_TIME)

        # Fade trail to black
        for i in range(CODE_RAIN_HEIGHT - 1):
            self.colors[1: -1] = self.colors[: -2]
            self.canvas[i, 0] = " "
            await asyncio.sleep(FALL_TIME)

        CodeRain.drops_falling -= 1

    async def fade(self):
        """
        Fade to last color and character.
        """
        for color in self.gradient:
            self.colors[-1, 0] = color
            await asyncio.sleep(0)

        await asyncio.sleep(self.delay / 8)
        self._random_char_task.cancel()
        self.canvas[-1, 0] = self.character


class MyApp(App):
    async def on_start(self):
        # Ending colors of logo:  True: Blue, False: Yellow
        colors = np.ones(SIZE, dtype=bool)
        colors[-7:] = colors[-13: -7, -41:] = False
        colors[-14, -17:] = colors[-20: -14, -15:] = False

        delays = generate_delays()

        # Create a CodeRain for each non-space character in the logo
        for y, row in enumerate(LOGO.splitlines()):
            for x, char in enumerate(row):
                if char != " ":
                    self.root.add_widget(
                        CodeRain(
                            target_row=y,
                            column=x,
                            character=char,
                            gradient=WHITE_TO_BLUE if colors[y, x] else WHITE_TO_YELLOW,
                            delay=delays[y, x],
                        )
                    )

        for code_rain in self.root.children:
            code_rain.start()

        while CodeRain.drops_falling:
            await asyncio.sleep(FALL_TIME)

        for code_rain in self.root.children:
            asyncio.create_task(code_rain.fade())


MyApp().run()
