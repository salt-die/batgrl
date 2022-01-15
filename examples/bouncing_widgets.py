"""
`esc` to exit.
"""
import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.colors import gradient, background_rainbow, Color, ColorPair
from nurses_2.io import MouseEventType
from nurses_2.widgets.text_widget import TextWidget

ORANGE = Color(255, 140, 66)
GREY = Color(108, 142, 173)
TEAL = Color(10, 175, 170)
PURPLE = Color(87, 10, 175)
ORANGE_ON_GREY = ColorPair.from_colors(ORANGE, GREY)
TEAL_ON_PURPLE = ColorPair.from_colors(TEAL, PURPLE)

ORANGE_TO_TEAL = gradient(start=ORANGE_ON_GREY, end=TEAL_ON_PURPLE, ncolors=10)
WHITE_ON_RAINBOW = background_rainbow(ncolors=10)


class BouncingWidget(TextWidget):
    def start(
        self,
        velocity,
        roll_step,
        palette,
        coord_view,
        collides_view,
    ):
        self.coord_view = coord_view
        self.collides_view = collides_view

        h, w = self.size
        for i in range(h):
            for j in range(w):
                self.canvas[i, j] = "NURSES!   "[(i + j) % 10]
                self.colors[i, j] = palette[(i + j) % 10]

        asyncio.create_task(self.bounce(velocity))
        asyncio.create_task(self.roll(roll_step))

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
                or self.bottom >= root.height and velocity.real > 0
            ):
                velocity = -velocity.conjugate()

            if (
                left <= 0 and velocity.imag < 0
                or self.right >= root.width and velocity.imag > 0
            ):
                velocity = velocity.conjugate()

            await asyncio.sleep(.05)

    async def roll(self, step):
        while True:
            self.canvas = np.roll(self.canvas, step, (0, ))
            self.colors = np.roll(self.colors, -step, (0, ))

            await asyncio.sleep(.11)

    def on_click(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            point = self.to_local(mouse_event.position)
            self.coord_view.add_text("({:<4}, {:<4})".format(*point))
            self.collides_view.add_text("yes" if self.collides_point(mouse_event.position) else "no ")


class MyApp(App):
    async def on_start(self):
        info_display = TextWidget(size=(3, 54))
        info_display.add_text("Click relative to widget_1: ", row=0)
        info_display.add_text("Click relative to widget_2: ", row=1)
        info_display.add_text("Collides: ", row=(0, 1), column=41)
        info_display.add_text("Widgets overlap: ", row=2)

        widget_1 = BouncingWidget(size=(20, 20), is_transparent=True)
        widget_2 = BouncingWidget(size=(10, 30), is_transparent=True)

        self.add_widgets(widget_1, widget_2, info_display)

        widget_1.start(
            velocity=1 + 1j,
            roll_step=1,
            palette=ORANGE_TO_TEAL,
            coord_view=info_display.get_view[0, 28:40],  # A view wide enough to fit coordinate display
            collides_view=info_display.get_view[0, -3:],  # A view wide enough for "yes" or "no "
        )

        widget_2.start(
            velocity=-1 - 1j,
            roll_step=-1,
            palette=WHITE_ON_RAINBOW,
            coord_view=info_display.get_view[1, 28:40],
            collides_view=info_display.get_view[1, -3:],
        )

        widget_overlap = info_display.get_view[2, 17:]

        while True:
            widget_overlap.add_text("True " if widget_1.collides_widget(widget_2) else "False")
            await asyncio.sleep(.5)


MyApp().run()
