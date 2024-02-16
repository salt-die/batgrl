######################
A Proper Pong Preamble
######################

This is a tutorial for creating a simple Pong clone. The completed source of this tutorial lives
`here <https://github.com/salt-die/batgrl/blob/main/examples/advanced/pong.py>`_.


Getting Started
---------------

Let's just get a basic app up and running. Create a new file named `pong.py`.

.. code-block:: python

    from batgrl.app import App


    class Pong(App):
        async def on_start(self):
            pass


    if __name__ == "__main__":
        Pong().run()

If you run this file, you should just see a blank terminal. To exit, press `ctrl+c`. The `on_start` method
is where you add gadgets to and schedule tasks for your app. Note that `on_start` is an async method.

Simple Graphics
---------------
Gadgets are interactive UI elements that make up your app. In fact, the app is just a tree of gadgets.
However, the base `Gadget` is little more than a container for other gadgets and can't render anything
on its own. To create a green play field, we need a gadget with a background color. Luckily, there is such
a gadget, `Pane`.

Create a green play field by creating a new `Pane` and setting its background color to green.
Colors and related functions live in their own module, `colors`.

.. code-block:: python

    from batgrl.app import App
    from batgrl.colors import GREEN
    from batgrl.gadgets.pane import Pane

    FIELD_HEIGHT = 25
    FIELD_WIDTH = 100


    class Pong(App):
        async def on_start(self):
            game_field = Pane(size=(FIELD_HEIGHT, FIELD_WIDTH), bg_color=GREEN)

            self.add_gadget(game_field)


    if __name__ == "__main__":
        Pong().run()

The app's `add_gadget()` method adds a gadget to the root gadget in the gadget tree. The root gadget always
has a size that is equal to your terminal's current size.

If you run the app now, you should see a green rectangle.


Responding to Input
-------------------
For paddles, let's use pane again. For the paddles to respond to key presses, you must subclass `Pane` and
implement the `on_key` method.

.. code-block:: python

    from batgrl.app import App
    from batgrl.colors import BLUE, GREEN
    from batgrl.gadgets.pane import Pane

    FIELD_HEIGHT = 25
    FIELD_WIDTH = 100
    PADDLE_HEIGHT = 5
    PADDLE_WIDTH = 1


    class Paddle(Pane):
        def __init__(self, up, down, **kwargs):
            self.up = up
            self.down = down
            super().__init__(**kwargs)

        def on_key(self, key_event):
            if key_event.key == self.up:
                self.y -= 1
            elif key_event.key == self.down:
                self.y += 1

            if self.y < 0:
                self.y = 0
            elif self.y > FIELD_HEIGHT - PADDLE_HEIGHT:
                self.y = FIELD_HEIGHT - PADDLE_HEIGHT


    class Pong(App):
        async def on_start(self):
            game_field = Pane(size=(FIELD_HEIGHT, FIELD_WIDTH), bg_color=GREEN)
            center = FIELD_HEIGHT // 2 - PADDLE_HEIGHT // 2
            left_paddle = Paddle(
                up="w",
                down="s",
                size=(PADDLE_HEIGHT, PADDLE_WIDTH),
                pos=(center, 1),
                bg_color=BLUE,
            )
            right_paddle = Paddle(
                up="up",
                down="down",
                size=(PADDLE_HEIGHT, PADDLE_WIDTH),
                pos=(center, FIELD_WIDTH - 2),
                bg_color=BLUE,
            )

            game_field.add_gadgets(left_paddle, right_paddle)
            self.add_gadget(game_field)


    if __name__ == "__main__":
        Pong().run()

Because the paddles were added to the game_field and not the root gadget, the position of the paddles
will be relative to the game field. Multiple gadgets can be added at once with the `add_gadgets()`
(note the plural) method.

Try out the app now and you should be able to move the paddles up and down with `w`, `s`, `up` and `down` keys.

Size and Pos Hints
------------------
Size and position hints are used to place or size a gadget as some proportion of its parent. If the
parent gadget is resized, the gadget will automatically reposition or resize itself using hints.
This allows us to easily place a divider in the middle of the play field, and to add two score labels
in the middle of each half of the play field. We'll need a new gadget for our scores, `Text`.

.. code-block:: python

    from batgrl.app import App
    from batgrl.colors import BLUE, GREEN
    from batgrl.gadgets.pane import Pane
    from batgrl.gadgets.text import Text

    FIELD_HEIGHT = 25
    FIELD_WIDTH = 100
    PADDLE_HEIGHT = 5
    PADDLE_WIDTH = 1


    class Paddle(Pane):
        def __init__(self, up, down, **kwargs):
            self.up = up
            self.down = down
            super().__init__(**kwargs)

        def on_key(self, key_event):
            if key_event.key == self.up:
                self.y -= 1
            elif key_event.key == self.down:
                self.y += 1

            if self.y < 0:
                self.y = 0
            elif self.y > FIELD_HEIGHT - PADDLE_HEIGHT:
                self.y = FIELD_HEIGHT - PADDLE_HEIGHT


    class Pong(App):
        async def on_start(self):
            game_field = Pane(size=(FIELD_HEIGHT, FIELD_WIDTH), bg_color=GREEN)
            center = FIELD_HEIGHT // 2 - PADDLE_HEIGHT // 2
            left_paddle = Paddle(
                up="w",
                down="s",
                size=(PADDLE_HEIGHT, PADDLE_WIDTH),
                pos=(center, 1),
                bg_color=BLUE,
            )
            right_paddle = Paddle(
                up="up",
                down="down",
                size=(PADDLE_HEIGHT, PADDLE_WIDTH),
                pos=(center, FIELD_WIDTH - 2),
                bg_color=BLUE,
            )
            divider = Pane(
                size=(1, 1),
                size_hint={"height_hint": 1.0},
                pos_hint={"x_hint": 0.5},
                bg_color=BLUE,
            )
            left_score_label = Text(
                size=(1, 5),
                pos=(1, 1),
                pos_hint={"x_hint": 0.25},
            )
            right_score_label = Text(
                size=(1, 5),
                pos=(1, 1),
                pos_hint={"x_hint": 0.75},
            )

            game_field.add_gadgets(
                left_paddle,
                right_paddle,
                divider,
                left_score_label,
                right_score_label,
            )
            self.add_gadget(game_field)


    if __name__ == "__main__":
        Pong().run()

Async
-----
Pong isn't complete without a ball. One more `Pane` can be used to represent the ball. Because `on_start()` is async,
we can constantly update the ball and then await to allow the rest of the event loop to run.

.. code-block:: python

    import asyncio

    from batgrl.app import App
    from batgrl.colors import BLUE, GREEN
    from batgrl.gadgets.pane import Pane
    from batgrl.gadgets.text import Text

    FIELD_HEIGHT = 25
    FIELD_WIDTH = 100
    PADDLE_HEIGHT = 5
    PADDLE_WIDTH = 1


    class Paddle(Pane):
        def __init__(self, up, down, **kwargs):
            self.up = up
            self.down = down
            super().__init__(**kwargs)

        def on_key(self, key_event):
            if key_event.key == self.up:
                self.y -= 1
            elif key_event.key == self.down:
                self.y += 1

            if self.y < 0:
                self.y = 0
            elif self.y > FIELD_HEIGHT - PADDLE_HEIGHT:
                self.y = FIELD_HEIGHT - PADDLE_HEIGHT


    class Pong(App):
        async def on_start(self):
            game_field = Pane(size=(FIELD_HEIGHT, FIELD_WIDTH), bg_color=GREEN)
            center = FIELD_HEIGHT // 2 - PADDLE_HEIGHT // 2
            left_paddle = Paddle(
                up="w",
                down="s",
                size=(PADDLE_HEIGHT, PADDLE_WIDTH),
                pos=(center, 1),
                bg_color=BLUE,
            )
            right_paddle = Paddle(
                up="up",
                down="down",
                size=(PADDLE_HEIGHT, PADDLE_WIDTH),
                pos=(center, FIELD_WIDTH - 2),
                bg_color=BLUE,
            )
            divider = Pane(
                size=(1, 1),
                size_hint={"height_hint": 1.0},
                pos_hint={"x_hint": 0.5},
                bg_color=BLUE,
            )
            left_score_label = Text(
                size=(1, 5),
                pos=(1, 1),
                pos_hint={"x_hint": 0.25},
            )
            right_score_label = Text(
                size=(1, 5),
                pos=(1, 1),
                pos_hint={"x_hint": 0.75},
            )
            ball = Pane(size=(1, 2), bg_color=BLUE)

            game_field.add_gadgets(
                left_paddle,
                right_paddle,
                divider,
                left_score_label,
                right_score_label,
                ball,
            )
            self.add_gadget(game_field)

            left_score = right_score = 0
            y_pos = FIELD_HEIGHT / 2
            x_pos = FIELD_WIDTH / 2 - 1
            y_vel = 0.0
            x_vel = 1.0
            speed = 0.04

            def reset():
                nonlocal y_pos, x_pos, y_vel, x_vel, speed
                y_pos = FIELD_HEIGHT / 2
                x_pos = FIELD_WIDTH / 2 - 1
                y_vel = 0.0
                x_vel = 1.0
                speed = 0.04
                left_score_label.add_str(f"{left_score:^5}")
                right_score_label.add_str(f"{right_score:^5}")

            def bounce_paddle(paddle):
                nonlocal x_pos, y_vel, x_vel, speed
                x_pos -= 2 * x_vel
                x_sgn = 1 if x_vel > 0 else -1
                center_y = paddle.height // 2
                intersect = max(min(paddle.y + center_y - ball.y, 0.95), -0.95)
                normalized = intersect / center_y
                y_vel = -normalized
                x_vel = -x_sgn * (1 - normalized**2) ** 0.5
                speed = max(0, speed - 0.001)

            reset()
            while True:
                # Update ball position.
                y_pos += y_vel
                x_pos += x_vel

                # Does ball collide with a paddle?
                if ball.collides_gadget(left_paddle):
                    bounce_paddle(left_paddle)
                elif ball.collides_gadget(right_paddle):
                    bounce_paddle(right_paddle)

                # Bounce off the top or bottom of the play field.
                if y_pos < 0 or y_pos >= FIELD_HEIGHT:
                    y_vel *= -1
                    y_pos += 2 * y_vel

                # If out of bounds, update the score.
                if x_pos < 0:
                    right_score += 1
                    reset()
                elif x_pos >= FIELD_WIDTH:
                    left_score += 1
                    reset()

                ball.y = int(y_pos)
                ball.x = int(x_pos)

                await asyncio.sleep(speed)


    if __name__ == "__main__":
        Pong().run()


Running the file now should give a complete pong game! Nice!

Now What?
---------
This is only scraping the surface of batgrl! For future improvements, you could:

* Use images or animations for the game field, paddles, or ball.
* Trigger an animation or graphical effect when the ball collides with the paddle or goes out of bounds.
* Move the paddles with the mouse.
* Add blocks to break.
