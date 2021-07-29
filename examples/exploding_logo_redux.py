"""
Directions:
    'esc' to quit
    'r' to reset
    'click' to poke
"""
import asyncio
from pathlib import Path

import numpy as np

from nurses_2.app import App
from nurses_2.mouse import MouseButton
from nurses_2.widgets.behaviors import AutoSizeBehavior
from nurses_2.widgets.particle_field import HalfBlockField, HalfBlockParticle
from nurses_2.widgets.image import Image

HEIGHT, WIDTH = 18, 36
POWER = 2
MAX_PARTICLE_SPEED = 10
FRICTION = .97

PERCENTS = tuple(np.linspace(0, 1, 30))

IMAGE_DIR = Path('images')
PATH_TO_BACKGROUND = IMAGE_DIR / 'background.png'
PATH_TO_LOGO_FULL = IMAGE_DIR / 'python_discord_logo.png'


class PokeParticle(HalfBlockParticle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        parent_middle_row, parent_middle_column = self.parent.center
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
        if mouse_event.button == MouseButton.LEFT:
            if dyx := -complex(*self.absolute_to_relative_coords(mouse_event.position)):
                self.velocity += POWER * dyx / (dyx.real**2 + dyx.imag**2)

                if self._update_task.done():
                    self._reset_task.cancel()
                    self._update_task = asyncio.create_task(self.update())

    def on_press(self, key_press):
        if key_press.key == "r" and self._reset_task.done():
            self._reset_task = asyncio.create_task(self.reset())

    async def update(self):
        parent = self.parent

        while True:
            velocity = self.velocity

            speed = abs(velocity)

            if speed < .001:
                return

            if speed > MAX_PARTICLE_SPEED:
                velocity *= MAX_PARTICLE_SPEED / speed

            self.position += velocity
            position = self.position

            self.top = top = position.real
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

        for percent in PERCENTS:
            percent_left = 1 - percent

            self.top = percent_left * start_y + percent * end_y
            self.left = round(percent_left * start_x + percent * end_x)
            self.position = complex(self.top, self.left)

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return


class AutoSizeHalfBlockField(AutoSizeBehavior, HalfBlockField):
    pass


class AutoSizeImage(AutoSizeBehavior, Image):
    pass


class MyApp(App):
    async def on_start(self):
        background = AutoSizeImage(path=PATH_TO_BACKGROUND)

        logo = Image(dim=(HEIGHT, WIDTH), path=PATH_TO_LOGO_FULL, is_transparent=True, alpha=.8)

        field = AutoSizeHalfBlockField()

        for y in range(logo.height):
            for x in range(logo.width):
                if logo.alpha_channels[y, x, 0]:
                    field.add_widget(
                        PokeParticle(
                            pos=(y + .25, x),
                            color=logo.colors[y, x, :3],
                            alpha=logo.alpha_channels[y, x, 0],
                        )
                    )

                if logo.alpha_channels[y, x, 1]:
                    field.add_widget(
                        PokeParticle(
                            pos=(y + .75, x),
                            color=logo.colors[y, x, 3:],
                            alpha=logo.alpha_channels[y, x, 1],
                        )
                    )

        self.root.add_widgets(background, field)


MyApp().run()
