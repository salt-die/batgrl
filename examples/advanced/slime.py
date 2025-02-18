"""Slime simulation."""

import asyncio

import cv2
import numpy as np
from batgrl.app import App
from batgrl.colors import AColor, gradient
from batgrl.gadgets.behaviors.toggle_button_behavior import ToggleButtonBehavior
from batgrl.gadgets.graphics import Graphics, scale_geometry
from batgrl.gadgets.slider import Slider
from batgrl.gadgets.text import Text

NAGENTS = 3000
SENSE_SIZE = 7
PALETTE = np.array(
    gradient(
        AColor.from_hex("00000000"),
        AColor.from_hex("0606faff"),
        AColor.from_hex("4c1bbdff"),
        AColor.from_hex("5a2280ff"),
        AColor.from_hex("3f1a43ff"),
        AColor.from_hex("0f080eff"),
        n=40,
        easing="out_sine",
    )
)


class Toggle(ToggleButtonBehavior, Text):
    def __init__(self, labels, **kwargs):
        super().__init__(**kwargs)
        self.add_str("▲")
        self._tween_task = None
        self.labels: Text = labels

    def on_toggle(self):
        if self._tween_task is not None:
            self._tween_task.cancel()

        def set_normal():
            # Otherwise the button will stay in hover stay while moving with label.
            self.button_state = "normal"

        if self.toggle_state == "off":
            self.add_str("▲")
            self._tween_task = asyncio.create_task(
                self.labels.tween(
                    y=0, duration=0.5, easing="out_bounce", on_start=set_normal
                )
            )
        else:
            self.add_str("▼")
            self._tween_task = asyncio.create_task(
                self.labels.tween(
                    y=-10, duration=0.5, easing="out_bounce", on_start=set_normal
                )
            )

    def update_hover(self):
        self.canvas["fg_color"] = (255, 200, 255)

    def update_normal(self):
        self.canvas["fg_color"] = self.default_fg_color


rng = np.random.default_rng()


def velocity(angles, move_speed):
    return np.stack([np.sin(angles), np.cos(angles)]) * move_speed


class Slime(Graphics):
    sense_angle = np.pi / 4
    turn_speed = np.pi / 8
    move_speed = 1.3
    dissipate = 0.01
    blur = 0.4

    def on_add(self):
        self.apply_hints()
        self._simulation_task = asyncio.create_task(self._simulate())

    def on_remove(self):
        self._simulation_task.cancel()

    def on_size(self):
        super().on_size()
        if hasattr(self, "_simulation_task"):
            self._simulation_task.cancel()
            self._simulation_task = asyncio.create_task(self._simulate())

    async def _simulate(self):
        h, w = scale_geometry(self._blitter, self.size)

        def as_pos(coords):
            ys, xs = np.clip(coords.astype(int), ((0,), (0,)), ((h - 1,), (w - 1,)))
            return ys, xs

        deposit = np.zeros((h, w))

        positions = np.full((NAGENTS, 2), (h / 2, w / 2)).T
        angles = np.linspace(0, 2 * np.pi, NAGENTS)

        sense_size = SENSE_SIZE + (SENSE_SIZE % 2 == 0)
        kernel = np.ones((sense_size, sense_size), int)
        while True:
            # Move forward
            positions += velocity(angles, self.move_speed)

            # Boundary conditions
            ys, xs = positions

            top = ys < 0
            left = xs < 0
            bottom = ys >= h
            right = xs >= w

            ys[top] *= -1
            xs[left] *= -1
            ys[bottom] = 2 * h - 1 - ys[bottom]
            xs[right] = 2 * w - 1 - xs[right]

            oob = top | bottom | left | right
            angles[oob] = rng.random(oob.sum()) * 2 * np.pi

            deposit[ys.astype(int), xs.astype(int)] = 1

            # Sense trail
            trail = cv2.filter2D(deposit, -1, kernel, borderType=cv2.BORDER_CONSTANT)
            trail_forward = trail[as_pos(positions + velocity(angles, self.move_speed))]
            trail_left = trail[
                as_pos(positions + velocity(angles + self.sense_angle, self.move_speed))
            ]
            trail_right = trail[
                as_pos(positions + velocity(angles - self.sense_angle, self.move_speed))
            ]

            # Turn agents
            left_or_right = (trail_forward < trail_right) & (trail_forward < trail_left)
            left_or_forward = (trail_forward < trail_left) & (trail_left > trail_right)
            right_or_forward = (trail_forward < trail_right) & (
                trail_right > trail_left
            )

            random_steer = rng.random(NAGENTS)
            deltas = np.zeros(NAGENTS)
            deltas[left_or_right] = 2 * (random_steer[left_or_right] - 0.5)
            deltas[left_or_forward] += random_steer[left_or_forward]
            deltas[right_or_forward] -= random_steer[right_or_forward]
            angles += deltas * self.turn_speed

            # Blur
            if self.blur:
                cv2.GaussianBlur(deposit, ksize=(0, 0), sigmaX=self.blur, dst=deposit)

            # Dissipate
            deposit -= self.dissipate
            deposit[deposit < 0] = 0

            # Draw
            to_palette = deposit * len(PALETTE)
            self.texture[:] = PALETTE[to_palette.astype(int)]
            await asyncio.sleep(0)


class SlimeApp(App):
    async def on_start(self):
        slime = Slime(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            blitter="braille",
            is_transparent=False,
        )
        labels = Text(size=(11, 31), is_transparent=True)
        labels.add_str("Sense Angle:")
        labels.add_str("Turn Speed:", pos=(2, 0))
        labels.add_str("Move Speed:", pos=(4, 0))
        labels.add_str("Dissipate:", pos=(6, 0))
        labels.add_str("Blur:", pos=(8, 0))
        labels.canvas["fg_color"] = 255

        def sense_callback(value):
            slime.sense_angle = value
            labels.add_str(f"{value:4.2f}", pos=(0, 27))

        def turn_callback(value):
            slime.turn_speed = value
            labels.add_str(f"{value:4.2f}", pos=(2, 27))

        def move_callback(value):
            slime.move_speed = value
            labels.add_str(f"{value:4.2f}", pos=(4, 27))

        def dissipate_callback(value):
            slime.dissipate = value
            labels.add_str(f"{value:4.2f}", pos=(6, 27))

        def blur_callback(value):
            slime.blur = value
            labels.add_str(f"{value:4.2f}", pos=(8, 27))

        sense_slider = Slider(
            min=np.pi / 8,
            max=np.pi / 2,
            start_value=np.pi / 4,
            callback=sense_callback,
            size=(1, 31),
            pos=(1, 0),
            is_transparent=True,
            alpha=0,
        )
        turn_slider = Slider(
            min=np.pi / 36,
            max=np.pi / 2,
            start_value=np.pi / 8,
            callback=turn_callback,
            size=(1, 31),
            pos=(3, 0),
            is_transparent=True,
            alpha=0,
        )
        move_slider = Slider(
            min=0.1,
            max=3.0,
            start_value=1.3,
            callback=move_callback,
            size=(1, 31),
            pos=(5, 0),
            is_transparent=True,
            alpha=0,
        )
        dissipate_slider = Slider(
            min=0.0005,
            max=0.2,
            start_value=0.01,
            callback=dissipate_callback,
            size=(1, 31),
            pos=(7, 0),
            is_transparent=True,
            alpha=0,
        )
        blur_slider = Slider(
            min=0.0,
            max=0.75,
            start_value=0.4,
            callback=blur_callback,
            size=(1, 31),
            pos=(9, 0),
            is_transparent=True,
            alpha=0,
        )

        labels.add_gadgets(
            sense_slider,
            turn_slider,
            move_slider,
            dissipate_slider,
            blur_slider,
        )

        toggle = Toggle(labels, size=(1, 2), pos=(10, 15), is_transparent=True)
        labels.add_gadget(toggle)

        self.add_gadgets(slime, labels)


if __name__ == "__main__":
    SlimeApp(title="Slime").run()
