import asyncio

from nurses_2.app import App
from nurses_2.colors import BLUE, GREEN, WHITE, ColorPair
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.widget import Widget

FIELD_HEIGHT = 25
FIELD_WIDTH = 100
WHITE_ON_GREEN = ColorPair.from_colors(WHITE, GREEN)

PADDLE_HEIGHT = 5
PADDLE_WIDTH = 1
WHITE_ON_BLUE = ColorPair.from_colors(WHITE, BLUE)


class Paddle(Widget):
    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player

    def on_key(self, key_event):
        if self.player == 1:
            if key_event.key == "w":
                self.y -= 1
            elif key_event.key == "s":
                self.y += 1
        elif self.player == 2:
            if key_event.key == "up":
                self.y -= 1
            elif key_event.key == "down":
                self.y += 1

        if self.y < 0:
            self.y = 0
        elif self.y > FIELD_HEIGHT - PADDLE_HEIGHT:
            self.y = FIELD_HEIGHT - PADDLE_HEIGHT


class Ball(Widget):
    def __init__(self, left_paddle, right_paddle, left_label, right_label, **kwargs):
        super().__init__(**kwargs)
        self.left_paddle = left_paddle
        self.right_paddle = right_paddle
        self.left_label = left_label
        self.right_label = right_label

    def on_add(self):
        super().on_add()
        self._update_task = asyncio.create_task(self.update())

    def reset(self):
        self.y_pos = FIELD_HEIGHT / 2
        self.x_pos = FIELD_WIDTH / 2 - 1
        self.y_velocity = 0.0
        self.x_velocity = 1.0
        self.speed = 0.04

    def bounce_paddle(self, paddle: Widget):
        self.x_pos -= 2 * self.x_velocity
        x_sgn = 1 if self.x_velocity > 0 else -1

        center_y = paddle.height // 2
        intersect = max(min(paddle.y + center_y - self.y, 0.95), -0.95)
        normalized = intersect / center_y
        self.y_velocity = -normalized
        self.x_velocity = -x_sgn * (1 - normalized**2) ** 0.5

        self.speed = max(0, self.speed - 0.001)

    async def update(self):
        self.reset()
        left_score = right_score = 0
        self.left_label.add_str(f"{0:^5}")
        self.right_label.add_str(f"{0:^5}")

        while True:
            # Update ball position.
            self.y_pos += self.y_velocity
            self.x_pos += self.x_velocity

            # Does ball collide with a paddle?
            if self.collides_widget(self.left_paddle):
                self.bounce_paddle(self.left_paddle)
            elif self.collides_widget(self.right_paddle):
                self.bounce_paddle(self.right_paddle)

            # Bounce off the top or bottom of the play field.
            if self.y_pos < 0 or self.y_pos >= FIELD_HEIGHT:
                self.y_velocity *= -1
                self.y_pos += 2 * self.y_velocity

            # If out of bounds, update the score.
            if self.x_pos < 0:
                self.reset()
                right_score += 1
                self.right_label.add_str(f"{right_score:^5}")
            elif self.x_pos >= FIELD_WIDTH:
                self.reset()
                left_score += 1
                self.left_label.add_str(f"{left_score:^5}")

            self.y = int(self.y_pos)
            self.x = int(self.x_pos)

            await asyncio.sleep(self.speed)


class Pong(App):
    async def on_start(self):
        game_field = Widget(
            size=(FIELD_HEIGHT, FIELD_WIDTH),
            background_color_pair=WHITE_ON_GREEN,
        )

        vertical_center = FIELD_HEIGHT // 2 - PADDLE_HEIGHT // 2

        left_paddle = Paddle(
            player=1,
            size=(PADDLE_HEIGHT, PADDLE_WIDTH),
            pos=(vertical_center, 1),
            background_color_pair=WHITE_ON_BLUE,
        )

        right_paddle = Paddle(
            player=2,
            size=(PADDLE_HEIGHT, PADDLE_WIDTH),
            pos=(vertical_center, FIELD_WIDTH - 2),
            background_color_pair=WHITE_ON_BLUE,
        )

        divider = Widget(
            size=(1, 1),
            size_hint={"height_hint": 1.0},
            pos_hint={"x_hint": 0.5, "anchor": "center"},
            background_color_pair=WHITE_ON_BLUE,
        )

        left_score_label = TextWidget(
            size=(1, 5),
            pos=(1, 1),
            pos_hint={"x_hint": 0.25, "anchor": "center"},
        )

        right_score_label = TextWidget(
            size=(1, 5),
            pos=(1, 1),
            pos_hint={"x_hint": 0.75, "anchor": "center"},
        )

        ball = Ball(
            left_paddle,
            right_paddle,
            left_score_label,
            right_score_label,
            size=(1, 2),
            background_color_pair=WHITE_ON_BLUE,
        )

        game_field.add_widgets(
            left_paddle,
            right_paddle,
            divider,
            left_score_label,
            right_score_label,
            ball,
        )
        self.add_widget(game_field)


if __name__ == "__main__":
    Pong(title="Pong").run()
