"""
Reaction-diffusion example with nurses_2.
"""
import asyncio

import cv2
import numpy as np

from nurses_2.app import App
from nurses_2.colors import Color, BLACK, ColorPair
from nurses_2.widgets.behaviors.grab_move_behavior import GrabMoveBehavior
from nurses_2.widgets.graphic_widget import GraphicWidget
from nurses_2.widgets.slider import Slider
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.widget import Widget

KERNEL =    np.array([
    [.05, .2, .05],
    [0.2, -1, 0.2],
    [.05, .2, .05],
])
BLUE = Color.from_hex("1e1ea8")
GREEN = Color.from_hex("2fa399")
BLUE_ON_BLACK = ColorPair.from_colors(BLUE, BLACK)
GREEN_ON_BLACK = ColorPair.from_colors(GREEN, BLACK)


class MoveMe(GrabMoveBehavior, Widget):
    ...


class ReactionDiffusion(GraphicWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.diffusion_A = 1.0
        self.diffusion_B = .5
        self.feed = .01624
        self.kill = .04465

    def on_add(self):
        super().on_add()
        self.on_size()
        self._update_task = asyncio.create_task(self._step_forever())

    def on_remove(self):
        super().on_remove()
        self._update_task.cancel()

    def on_size(self):
        h, w = self._size
        h *= 2

        self.texture = np.zeros((h, w, 4), dtype=np.uint8)
        self.texture[..., 3] = 255

        self.A = np.ones((h, w), dtype=float)
        self.B = np.zeros_like(self.A)

    def on_mouse(self, mouse_event):
        if (
            mouse_event.button == "left"
            and self.collides_point(mouse_event.position)
        ):
            y, x = self.to_local(mouse_event.position)
            y *= 2

            self.B[y - 1: y + 3, x - 1: x + 2] = 1.0
            return True

    async def _step_forever(self):
        while True:
            self.step()
            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

    def step(self):
        """
        Gray-Scott algorithm.
        """
        A = self.A
        B = self.B
        feed = self.feed
        kill = self.kill

        laplace_A = cv2.filter2D(A, ddepth=-1, kernel=self.diffusion_A * KERNEL, borderType=2)
        laplace_B = cv2.filter2D(B, ddepth=-1, kernel=self.diffusion_B * KERNEL, borderType=2)

        react = A * B**2

        A[:] = np.clip(A * (1 - feed) + laplace_A - react + feed, 0, 1)
        B[:] = np.clip(B * (1 - kill - feed) + laplace_B + react, 0, 1)

        self.texture[..., 0] = (255 * A).astype(np.uint8)
        self.texture[..., 1] = (255 * B).astype(np.uint8)
        self.texture[..., 2] = (127.5 * (B - A + 1)).astype(np.uint8)


class ReactionDiffusionApp(App):
    async def on_start(self):
        rd = ReactionDiffusion(size_hint=(1.0, 1.0))
        container = MoveMe(size=(8, 30))

        attrs = (
            ("diffusion_A", 0.0, 1.0),
            ("diffusion_B", 0.0, 1.0),
            ("feed", .001, .08),
            ("kill", .01, .073),
        )

        labels = [
            TextWidget(
                size=(1, 30),
                pos=(2 * i, 0),
                default_color_pair=GREEN_ON_BLACK,
            )
            for i in range(4)
        ]
        for label, (attr, _, _) in zip(labels, attrs):
            label.add_text(f"{attr}: {getattr(rd, attr):.4}")

        def create_callback(attr, i):
            def set_attr(value):
                setattr(rd, attr, value)
                labels[i].add_text(f"{attr}: {value:.6}".ljust(30))

            return set_attr

        sliders = [
            Slider(
                min=min,
                max=max,
                size=(1, 30),
                pos=(2 * i + 1, 0),
                start_value=getattr(rd, attr),
                callback=create_callback(attr, i),
                fill_color=GREEN,
                default_color_pair=BLUE_ON_BLACK,
            )
            for i, (attr, min, max) in enumerate(attrs)
        ]

        container.add_widgets(*sliders, *labels)
        self.add_widgets(rd, container)


ReactionDiffusionApp(title="Reaction Diffusion").run()
