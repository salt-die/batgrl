"""Slime simulation."""

import asyncio

import cv2
import numpy as np
from batgrl.app import App
from batgrl.colors import DEFAULT_PRIMARY_BG
from batgrl.gadgets.graphics import Graphics
from batgrl.gadgets.pane import Pane

SENSE_SIZE = 7
SENSE_ANGLE = np.pi / 4
TURN_SPEED = np.pi / 8
MOVE_SPEED = 1.3
DISSIPATE = 0.01
BLUR = 0.4
NAGENTS = 200

rng = np.random.default_rng()


def velocity(angles):
    return np.stack([np.sin(angles), np.cos(angles)]) * MOVE_SPEED


class Slime(Graphics):
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
        h, w = self.size
        h *= 2

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
            positions += velocity(angles)

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
            trail_forward = trail[as_pos(positions + velocity(angles))]
            trail_left = trail[as_pos(positions + velocity(angles + SENSE_ANGLE))]
            trail_right = trail[as_pos(positions + velocity(angles - SENSE_ANGLE))]

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
            angles += deltas * TURN_SPEED

            # Blur
            cv2.GaussianBlur(deposit, ksize=(0, 0), sigmaX=BLUR, dst=deposit)

            # Dissipate
            deposit[deposit < DISSIPATE] = 0
            deposit[deposit >= DISSIPATE] -= DISSIPATE

            # Draw
            self.texture[:] = 255 * deposit[..., None]
            await asyncio.sleep(0)


class SlimeApp(App):
    async def on_start(self):
        background = Pane(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            bg_color=DEFAULT_PRIMARY_BG,
        )
        slime = Slime(size_hint={"height_hint": 1.0, "width_hint": 1.0})
        self.add_gadgets(background, slime)


if __name__ == "__main__":
    SlimeApp(title="Slime").run()
