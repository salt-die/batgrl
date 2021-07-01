"""
`esc` to exit.
"""
import asyncio

import numpy as np
from prompt_toolkit.mouse_events import MouseEvent

from nurses_2.app import App
from nurses_2.widgets import Widget
from nurses_2.colors import gradient, bg_rainbow, WHITE
from nurses_2.mouse import MouseEvent, MouseEventType

ORANGE = 255, 140, 66, 108, 142, 173
TEAL = 10, 175, 170, 87, 10, 175

ORANGE_TO_TEAL = tuple(gradient(n=20, start_pair=ORANGE, end_pair=TEAL))
WHITE_ON_RAINBOW = tuple(bg_rainbow(n=20, fg_color=WHITE))


class BouncingWidget(Widget):
    def start(self, velocity, roll_axis, palette, coord_view):
        self.coord_view = coord_view

        h, w = self.dim
        for i in range(h):
            for j in range(w):
                self.canvas[i, j] = 'NURSES!   '[(i + j) % 10]
                self.colors[i, j] = palette[(i + j) % 20]

        asyncio.create_task(self.bounce(velocity))
        asyncio.create_task(self.roll(roll_axis))

    async def bounce(self, velocity):
        velocity /= abs(velocity)  # normalize

        pos = self.top + self.left * 1j
        root = self.root

        while True:
            pos += velocity

            self.top = top = int(pos.real)
            self.left = left = int(pos.imag)

            if (
                top <= 0 and velocity.real < 0
                or self.bottom > root.height and velocity.real > 0
            ):
                velocity = -velocity.conjugate()

            if (
                left <= 0 and velocity.imag < 0
                or self.right > root.width and velocity.imag > 0
            ):
                velocity = velocity.conjugate()

            await asyncio.sleep(.05)

    async def roll(self, axis):
        while True:
            self.canvas = np.roll(self.canvas, 1, (axis, ))
            self.colors = np.roll(self.colors, 1, (axis, ))

            await asyncio.sleep(.11)

    def on_click(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            relative_coords = self.absolute_to_relative_coords(mouse_event.position)
            self.coord_view[:12] = tuple("({:<4}, {:<4})".format(*relative_coords))
            self.coord_view[-3:] = tuple("yes") if self.collide_coords(mouse_event.position) else tuple("no ")


class MyApp(App):
    async def on_start(self):
        coord_display = Widget(dim=(2, 54))
        coord_display.canvas[0, :28] = tuple("Click relative to widget_1: ")
        coord_display.canvas[1, :28] = tuple("Click relative to widget_2: ")
        coord_display.canvas[(0, 1), 41: 51] = tuple("Collides: ")

        widget_1 = BouncingWidget(dim=(20, 20), is_transparent=True)
        widget_2 = BouncingWidget(dim=(10, 30), is_transparent=True)

        self.root.add_widgets(widget_1, widget_2, coord_display)

        widget_1.start(
            velocity=1 + 1j,
            roll_axis=0,
            palette=ORANGE_TO_TEAL,
            coord_view=coord_display.canvas[0, 28:],
        )

        widget_2.start(
            velocity=-1 - 1j,
            roll_axis=1,
            palette=WHITE_ON_RAINBOW,
            coord_view=coord_display.canvas[1, 28:],
        )


MyApp().run()
