"""
Classic snake game.

Move snake with arrow keys. Pause with `space`.
"""

import asyncio
from collections import deque
from itertools import cycle, product
from pathlib import Path
from random import choice

from batgrl.app import App
from batgrl.colors import ARED, AWHITE, gradient, rainbow_gradient
from batgrl.gadgets.graphics import Graphics
from batgrl.gadgets.video import Video

ASSETS = Path(__file__).parent.parent / "assets"
SPINNER = ASSETS / "spinner.gif"
HEIGHT, WIDTH = 20, 20
SNAKE_START = HEIGHT // 2, WIDTH // 2
SNAKE_START_2 = HEIGHT // 2 + 1, WIDTH // 2
TICK_DURATION = 0.12
RAINBOW_GRADIENT = rainbow_gradient(40, alpha=255)
APPLE_GRADIENT = cycle(gradient(ARED, AWHITE, 5) + gradient(AWHITE, ARED, 20))


def inbounds(pos):
    y, x = pos
    return 0 <= y < HEIGHT and 0 <= x < WIDTH


class Snake(Graphics):
    def on_add(self):
        super().on_add()
        self.reset()
        self._update_task = asyncio.create_task(self._update())
        self._apple_task = asyncio.create_task(self._paint_apple())

    def on_remove(self):
        super().on_remove()
        self._update_task.cancel()
        self._apple_task.cancel()

    def on_size(self):
        super().on_size()
        self.reset()

    def reset(self):
        self.clear()

        # Keep track of empty positions to quickly find a place for an apple.
        self.empty_positions = list(product(range(HEIGHT), range(WIDTH)))
        self.empty_positions.remove(SNAKE_START)
        self.empty_positions.remove(SNAKE_START_2)

        self.snake_is_moving = False
        self.snake = deque([SNAKE_START, SNAKE_START_2])
        self.texture[SNAKE_START] = RAINBOW_GRADIENT[0]
        self.texture[SNAKE_START_2] = RAINBOW_GRADIENT[1]

        self.apple = choice(self.empty_positions)

        self.current_direction = -1, 0

    def _check_neck(self, dy, dx):
        """Prevent head from turning 180 degrees."""
        y, x = self.snake[0]
        if (dy + y, dx + x) == self.snake[1]:
            return self.current_direction

        return dy, dx

    def on_key(self, key_event):
        if not self.snake_is_moving:
            self.snake_is_moving = True

        if key_event.key == "up":
            self.current_direction = self._check_neck(-1, 0)
        elif key_event.key == "left":
            self.current_direction = self._check_neck(0, -1)
        elif key_event.key == "right":
            self.current_direction = self._check_neck(0, 1)
        elif key_event.key == "down":
            self.current_direction = self._check_neck(1, 0)
        elif key_event.key == " ":
            self.snake_is_moving = False
        else:
            return False

        return True

    async def _paint_apple(self):
        while True:
            self.texture[self.apple] = next(APPLE_GRADIENT)

            await asyncio.sleep(TICK_DURATION / 2)

    async def _update(self):
        while True:
            if self.snake_is_moving:
                dy, dx = self.current_direction
                y, x = self.snake[0]
                head = y + dy, x + dx

                if inbounds(head) and head not in self.snake:
                    self.empty_positions.remove(head)
                    self.snake.appendleft(head)

                    if head == self.apple:
                        self.apple = choice(self.empty_positions)
                    else:
                        tail = self.snake.pop()
                        self.empty_positions.append(tail)
                        self.texture[tail] = self.default_color

                    for point, color in zip(self.snake, cycle(RAINBOW_GRADIENT)):
                        self.texture[point] = color
                else:
                    self.reset()

            await asyncio.sleep(TICK_DURATION)


class SnakeApp(App):
    async def on_start(self):
        kwargs = dict(
            size=(HEIGHT // 2, WIDTH), pos_hint={"y_hint": 0.5, "x_hint": 0.5}
        )
        background = Video(source=SPINNER, alpha=0.5, is_transparent=True, **kwargs)
        background.play()
        snake = Snake(**kwargs)

        self.add_gadgets(background, snake)


if __name__ == "__main__":
    SnakeApp().run()
