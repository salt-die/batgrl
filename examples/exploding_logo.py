"""
Credit for ascii art logo to Matthew Barber (https://ascii.matthewbarber.io/art/python/)

Directions:
    'esc' to quit
    'r' to reset
    'click' to poke
"""
import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.colors import foreground_rainbow
from nurses_2.mouse import MouseEventType
from nurses_2.widgets.auto_resize_behavior import AutoResizeBehavior
from nurses_2.widgets.particle_field import Particle, ParticleField

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
HEIGHT, WIDTH = 28, 56

POWER = 2
MAX_PARTICLE_SPEED = 10
FRICTION = .97

NCOLORS = 100
RAINBOW = foreground_rainbow(NCOLORS)
BLUE_INDEX = round(.65 * NCOLORS)
YELLOW_INDEX = round(.1 * NCOLORS)

COLOR_CHANGE_SPEED = 5
PERCENTS = tuple(np.linspace(0, 1, 30))


class PokeParticle(Particle):
    def __init__(self, *args, color_index, **kwargs):
        self.color_index = color_index

        super().__init__(*args, color=RAINBOW[color_index], **kwargs)

        self.middle_row = self.middle_column = 0
        self.original_position = self.pos

        self.position = complex(self.top, self.left)
        self.velocity = 0j

        self._update_task = self._reset_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

    def update_geometry(self):
        """
        Re-position towards center of parent's canvas.
        """
        old_middle_row = self.middle_row
        old_middle_column = self.middle_column

        parent_middle_row, parent_middle_column = self.parent.middle
        self.middle_row = parent_middle_row - HEIGHT // 2
        self.middle_column = parent_middle_column - WIDTH // 2

        move_vertical = self.middle_row - old_middle_row
        move_horizontal = self.middle_column - old_middle_column

        o_top, o_left = self.original_position
        o_top += move_vertical
        o_left += move_horizontal

        self.original_position = o_top, o_left
        self.position += complex(move_vertical, move_horizontal)
        self.top += move_vertical
        self.left += move_horizontal

    def on_click(self, mouse_event):
        if mouse_event.event_type in (MouseEventType.MOUSE_DOWN, MouseEventType.MOUSE_DOWN_MOVE):
            if dyx := -complex(*self.absolute_to_relative_coords(mouse_event.position)):
                self.velocity += POWER * dyx / (dyx.real**2 + dyx.imag**2)

                if self._update_task.done():
                    self._reset_task.cancel()
                    self._update_task = asyncio.create_task(self.update())

    def on_press(self, key_press):
        if key_press.key == "r" and self._reset_task.done():
            self._reset_task = asyncio.create_task(self.reset())

    async def update(self):
        """
        Coroutine that updates color and position due to velocity.
        """
        parent = self.parent
        color_index = RAINBOW.index(self.color)

        while True:
            velocity = self.velocity

            speed = abs(velocity)

            if speed < .001:
                return

            color_index = round(color_index + min(speed, MAX_PARTICLE_SPEED) * COLOR_CHANGE_SPEED) % NCOLORS
            self.color = RAINBOW[color_index]

            if speed > MAX_PARTICLE_SPEED:
                velocity *= MAX_PARTICLE_SPEED / speed

            self.position += velocity

            position = self.position
            self.top = top = round(position.real)
            self.left = left = round(position.imag)

            if (
                top < 0 and velocity.real < 0
                or top >= parent.height and velocity.real > 0
            ):
                velocity = -velocity.conjugate()

            if (
                left < 0 and velocity.imag < 0
                or left >= parent.width and velocity.imag > 0
            ):
                velocity = velocity.conjugate()

            self.velocity = velocity * FRICTION

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

    async def reset(self):
        """
        Coroutine that returns a particle to its starting position with original color.
        """
        self._update_task.cancel()

        self.velocity = 0j

        start_y, start_x = self.pos
        end_y, end_x = self.original_position

        start_color_index = RAINBOW.index(self.color)
        end_color_index = self.color_index

        for percent in PERCENTS:
            percent_left = 1 - percent

            self.top = round(percent_left * start_y + percent * end_y)
            self.left = round(percent_left * start_x + percent * end_x)
            self.position = complex(self.top, self.left)

            color_index = round(percent_left * start_color_index + percent * end_color_index)
            self.color = RAINBOW[color_index]

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return


class AutoResizeParticleField(AutoResizeBehavior, ParticleField):
    pass


class MyApp(App):
    async def on_start(self):
        # Create array of starting colors of particles
        colors = np.full((HEIGHT, WIDTH), BLUE_INDEX)
        colors[-7:] = colors[-13: -7, -41:] = YELLOW_INDEX
        colors[-14, -17:] = colors[-20: -14, -15:] = YELLOW_INDEX

        field = AutoResizeParticleField()

        # Create a Particle for each non-space character in the logo
        field.add_widgets(
            PokeParticle((y, x), char=char, color_index=colors[y, x])
            for y, row in enumerate(LOGO.splitlines())
            for x, char in enumerate(row)
            if char != " "
        )

        self.root.add_widget(field)


MyApp().run()
