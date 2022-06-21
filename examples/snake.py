"""
Classic snake game.

Move snake with arrow keys. Pause with `space`.
"""
import asyncio
from collections import deque
from enum import Enum
from itertools import product
from pathlib import Path
from random import choice

from nurses_2.app import App
from nurses_2.colors import AGREEN, ARED
from nurses_2.widgets.graphic_widget import GraphicWidget
from nurses_2.widgets.image import Image

PATH_TO_LOGO_FULL = Path("images") / "python_discord_logo.png"
HEIGHT, WIDTH = 20, 20
SNAKE_START = HEIGHT // 2, WIDTH // 2
TICK_DURATION = .12

def inbounds(pos):
    y, x = pos
    return 0 <= y < HEIGHT and 0 <= x < WIDTH


class Directions(Enum):
    UP = (-1, 0)
    RIGHT = (0 , 1)
    DOWN = (1, 0)
    LEFT = (0, -1)


class Snake(GraphicWidget):
    def __init__(self, snake_color=AGREEN, apple_color=ARED, **kwargs):
        super().__init__(**kwargs)
        self.snake_color = snake_color
        self.apple_color = apple_color
        self.reset()
        self._update_task = asyncio.create_task(self._update())

    def on_size(self):
        super().on_size()
        self.reset()

    def reset(self):
        # Empty positions allow us to easily find a place for an apple.
        self.texture[:] = self.default_color

        self.empty_positions = list(product(range(HEIGHT), range(WIDTH)))
        self.empty_positions.remove(SNAKE_START)

        self.snake_is_moving = False
        self.snake = deque([SNAKE_START])
        self.texture[SNAKE_START] = self.snake_color

        self.apple = choice(self.empty_positions)
        self.texture[self.apple] = self.apple_color

        self.current_direction = Directions.RIGHT

    def move_snake(self):
        dy, dx = self.current_direction.value
        y, x = self.snake[0]
        head = y + dy, x + dx

        if inbounds(head) and head not in self.snake:
            self.empty_positions.remove(head)
            self.snake.appendleft(head)
            self.texture[head] = self.snake_color

            if head == self.apple:
                self.apple = choice(self.empty_positions)
                self.texture[self.apple] = self.apple_color
            else:
                tail = self.snake.pop()
                self.empty_positions.append(tail)
                self.texture[tail] = self.default_color

        else:
            self.reset()

    def on_press(self, key_press_event):
        if not self.snake_is_moving:
            self.snake_is_moving = True

        match key_press_event.key:
            case "up":
                self.current_direction = Directions.UP
            case "left":
                self.current_direction = Directions.LEFT
            case "right":
                self.current_direction = Directions.RIGHT
            case "down":
                self.current_direction = Directions.DOWN
            case " ":
                self.snake_is_moving = False

    async def _update(self):
        while True:
            if self.snake_is_moving:
                self.move_snake()

            await asyncio.sleep(TICK_DURATION)


class SnakeApp(App):
    async def on_start(self):
        kwargs = dict(
            size=(HEIGHT // 2, WIDTH),
            pos_hint=(.5, .5),
            anchor="center",
        )

        background = Image(path=PATH_TO_LOGO_FULL, alpha=.33, **kwargs)
        snake = Snake(**kwargs)

        self.add_widgets(background, snake)

SnakeApp().run()
