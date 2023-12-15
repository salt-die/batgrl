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
You can create a green play field by adding a new gadget with a background color pair with green background.
A `ColorPair` includes a foreground color and a background color for text. In this case, the foreground
color is not used.

.. code-block:: python

    import asyncio

    from batgrl.app import App
    from batgrl.colors import GREEN, BLUE, WHITE, ColorPair
    from batgrl.gadgets.text import Text
    from batgrl.gadgets.gadget import Gadget

    FIELD_HEIGHT = 25
    FIELD_WIDTH = 100
    WHITE_ON_GREEN = ColorPair.from_colors(WHITE, GREEN)


    class Pong(App):
        async def on_start(self):
            game_field = Gadget(
                size=(FIELD_HEIGHT, FIELD_WIDTH),
                background_color_pair=WHITE_ON_GREEN,
            )

            self.add_gadget(game_field)


    if __name__ == "__main__":
        Pong().run()

Gadgets are interactive UI elements that make up your app. In fact, the app is just a tree of gadgets.
The `Gadget` class is little more than a container for other gadgets, but it can be given a background color pair.

The app's `add_gadget` method adds a gadget to the root gadget in the gadget tree. The root gadget always has a size
that is equal to your terminal's current size.

If you run the app now, you should see a green rectangle.


Responding to Input
-------------------
You can add two more gadgets to the game field for paddles. To allow the paddles to respond to key presses you must
subclass gadget and implement the `on_key` method.

.. code-block:: python

    PADDLE_HEIGHT = 5
    PADDLE_WIDTH = 1
    WHITE_ON_BLUE = ColorPair.from_colors(WHITE, BLUE)


    class Paddle(Gadget):
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

And the app's `on_start` method will now look like:

.. code-block:: python

    async def on_start(self):
        game_field = Gadget(
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

        game_field.add_gadgets(left_paddle, right_paddle)
        self.add_gadget(game_field)

Because the paddles were added to the game_field and not the root gadget, the position of the paddles
will be relative to the game field. Multiple gadgets can be added at once with the `add_gadgets` (note the plural)
method.

Try out the app now and you should be able to move the paddles up and down with `w`, `s`, `up` and `down` keys.

Size and Pos Hints
------------------
Size and position hints are used to place or size a gadget as some proportion of its parent. If the
parent gadget is resized, the gadget will automatically reposition or resize itself using hints.
This allows us to easily place a divider in the middle of the play field, and to add two score labels
in the middle of each half of the play field. Add the following to your `on_start` method:

.. code-block:: python

    divider = Gadget(
        size=(1, 1),
        size_hint={"height_hint": 1.0},
        pos_hint={"x_hint": 0.5, "anchor": "center"},
        background_color_pair=WHITE_ON_BLUE,
    )

    left_score_label = Text(
        size=(1, 5),
        pos=(1, 1),
        pos_hint={"x_hint": 0.25, "anchor": "center"},
    )

    right_score_label = Text(
        size=(1, 5),
        pos=(1, 1),
        pos_hint={"x_hint": 0.75, "anchor": "center"},
    )

    game_field.add_gadgets(
        left_paddle,
        right_paddle,
        divider,
        left_score_label,
        right_score_label,
    )
    self.add_gadget(game_field)

The `anchor` keyword argument is used for position hints to specify which point the of the gadget
is aligned with the hint. The default is `"top_left"`.

Scheduling Tasks
----------------
Pong isn't complete without a ball. Because batgrl uses `asyncio`, you can create a task (with `asyncio.create_task`)
to constantly update the ball's position. In the code below, the task is created in `on_add` which is
called when the gadget is added to the gadget tree.

.. code-block:: python

    class Ball(Gadget):
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

        def bounce_paddle(self, paddle: Gadget):
            self.x_pos -= 2 * self.x_velocity
            x_sgn = 1 if self.x_velocity > 0 else -1

            center_y = paddle.height // 2
            intersect = max(min(paddle.y + center_y - self.y, 0.95), -0.95)
            normalized = intersect / center_y
            self.y_velocity = -normalized
            self.x_velocity = -x_sgn * (1 - normalized**2) ** .5

            self.speed = max(0, self.speed - .001)

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
                if self.collides_gadget(self.left_paddle):
                    self.bounce_paddle(self.left_paddle)
                elif self.collides_gadget(self.right_paddle):
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

Finally, add the ball to the game field.

.. code-block:: python

    ball = Ball(
        left_paddle,
        right_paddle,
        left_score_label,
        right_score_label,
        size=(1, 2),
        background_color_pair=WHITE_ON_BLUE,
    )

    game_field.add_gadgets(
        left_paddle,
        right_paddle,
        divider,
        left_score_label,
        right_score_label,
        ball,
    )
    self.add_gadget(game_field)

Running the file now should give a complete pong game! Nice!

Now What?
---------
This is only scraping the surface of batgrl! For future improvements, you could:

* Use images or animations for the game field, paddles, or ball.
* Trigger an animation or graphical effect when the ball collides with the paddle or goes out of bounds.
* Move the paddles with the mouse.
* Add blocks to break.
