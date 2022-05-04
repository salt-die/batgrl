import asyncio
import random

from nurses_2.app import App
from nurses_2.colors import GREEN, BLUE, WHITE, ColorPair
from nurses_2.widgets.widget import Widget

FIELD_HEIGHT = 25
FIELD_WIDTH = 100
FIELD_COLOR_PAIR = ColorPair.from_colors(WHITE, GREEN)

PADDLE_HEIGHT = 5
PADDLE_WIDTH = 1
PADDLE_COLOR_PAIR = ColorPair.from_colors(WHITE, BLUE)


class Paddle(Widget):
    def __init__(self, player, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player = player

    def on_press(self, key_press_event):
        if self.player == 1:
            if key_press_event.key == "w":
                self.y -= 1
            elif key_press_event.key == "s":
                self.y += 1
        elif self.player == 2:
            if key_press_event.key == "up":
                self.y -= 1
            elif key_press_event.key == "down":
                self.y += 1

        if self.y < 0:
            self.y = 0
        elif self.y > FIELD_HEIGHT - PADDLE_HEIGHT:
            self.y = FIELD_HEIGHT - PADDLE_HEIGHT


class Ball(Widget):
    def __init__(self, left_paddle, right_paddle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.left_paddle = left_paddle
        self.right_paddle = right_paddle
        asyncio.create_task(self.update())

    def reset(self):
        self.y_pos = FIELD_HEIGHT / 2
        self.x_pos = FIELD_WIDTH / 2 - 1
        self.y_velocity = 0.0
        self.x_velocity = 1.0
        self.speed = 1.0

    def bounce_paddle(self, paddle):
        self.x_velocity *= -1
        self.x_pos += 2 * self.x_velocity
        paddle_middle = (paddle.bottom + paddle.top) // 2
        self.y_velocity += (self.y - paddle_middle) / 5 + random.random() / 20
        self.speed *= 1.1

    def normalize_speed(self):
        current_speed = (self.y_velocity**2 + self.x_velocity**2)**.5
        if current_speed > self.speed:
            self.x_velocity *= self.speed / current_speed
            self.y_velocity *= self.speed / current_speed

    async def update(self):
        self.reset()

        while True:
            self.y_pos += self.y_velocity
            self.x_pos += self.x_velocity

            if self.collides_widget(self.left_paddle):
                self.bounce_paddle(self.left_paddle)
            elif self.collides_widget(self.right_paddle):
                self.bounce_paddle(self.right_paddle)

            if self.y_pos < 0 or self.y_pos >= FIELD_HEIGHT:
                self.y_velocity *= -1
                self.y_pos += 2 * self.y_velocity

            if self.x_pos < 0 or self.x_pos >= FIELD_WIDTH:
                self.reset()

            self.normalize_speed()

            self.y = int(self.y_pos)
            self.x = int(self.x_pos)

            await asyncio.sleep(.04)


class Pong(App):
    async def on_start(self):
        game_field = Widget(
            size=(FIELD_HEIGHT, FIELD_WIDTH),
            background_color_pair=FIELD_COLOR_PAIR,
        )

        vertical_center = FIELD_HEIGHT // 2 - PADDLE_HEIGHT // 2

        left_paddle = Paddle(
            player=1,
            size=(PADDLE_HEIGHT, PADDLE_WIDTH),
            pos=(vertical_center, 1),
            background_color_pair=PADDLE_COLOR_PAIR,
        )

        right_paddle = Paddle(
            player=2,
            size=(PADDLE_HEIGHT, PADDLE_WIDTH),
            pos=(vertical_center, FIELD_WIDTH - 2),
            background_color_pair=PADDLE_COLOR_PAIR,
        )

        divider = Widget(
            size=(1, 1),
            size_hint=(1.0, None),
            pos_hint=(None, .5),
            background_color_pair=PADDLE_COLOR_PAIR,
        )

        ball = Ball(
            left_paddle,
            right_paddle,
            size=(1, 2),
            background_color_pair=PADDLE_COLOR_PAIR,
        )

        game_field.add_widgets(left_paddle, right_paddle, divider, ball)
        self.add_widget(game_field)


if __name__ == "__main__":
    Pong().run()
