"""
A rigid body physics simulation in the terminal.

Requires `pymunk`
"""

import asyncio
from math import ceil, degrees
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
import pymunk
from batgrl.app import App
from batgrl.colors import AWHITE, AColor
from batgrl.gadgets.graphics import Graphics
from batgrl.gadgets.image import Image
from batgrl.texture_tools import composite, read_texture, resize_texture
from pymunk.vec2d import Vec2d

BOX_SIZE = W, H = Vec2d(9, 9)
BOX_MASS = 0.1
BALL_MASS = 100
BALL_RADIUS = 6
GROUND_LEVEL = 12

BOX_CENTER = HW, HH = W // 2, H // 2
BOX_POINTS = np.array([[0, 0], [0, W], [0, H], [W, H]]).reshape(-1, 1, 2)
BALL_CENTER = BALL_RADIUS, BALL_RADIUS
BALL_SIZE = BALL_RADIUS * 2, BALL_RADIUS * 2

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_BACKGROUND = ASSETS / "background.png"
PATH_TO_CRATE = ASSETS / "crate.png"
PATH_TO_BALL = ASSETS / "soccer_ball.png"
CRATE = resize_texture(read_texture(PATH_TO_CRATE), BOX_SIZE, "nearest")
BALL = resize_texture(read_texture(PATH_TO_BALL), BALL_SIZE, "nearest")


class SpaceRenderer(Graphics):
    def __init__(
        self,
        space: pymunk.Space,
        dt: float = 0.01,
        render_mode: Literal["outline", "fill", "sprite"] = "sprite",
        shape_color: AColor = AWHITE,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.space = space
        self.dt = dt
        self.render_mode = render_mode
        self.shape_color = shape_color

    def stop_simulation(self):
        if task := getattr(self, "_simulation_task", False):
            task.cancel()

    def on_remove(self):
        self.stop_simulation()

    def run_simulation(self):
        self.stop_simulation()
        self._simulation_task = asyncio.create_task(self._run_simulation())

    async def _run_simulation(self):
        while True:
            self.space.step(self.dt)
            self._draw_space()
            await asyncio.sleep(0)

    def _to_texture_coords(self, point: Vec2d) -> tuple[int, int]:
        x, y = point
        return round(x), 2 * self.height - round(y) - 1

    def _draw_space(self):
        self.clear()
        to_tex_coords = self._to_texture_coords

        for shape in self.space.shapes:
            if isinstance(shape, pymunk.shapes.Segment):
                if self.render_mode != "sprite":
                    a = shape.a.rotated(shape.body.angle) + shape.body.position
                    b = shape.b.rotated(shape.body.angle) + shape.body.position
                    cv2.line(
                        self.texture,
                        to_tex_coords(a),
                        to_tex_coords(b),
                        self.shape_color,
                    )
            elif isinstance(shape, pymunk.shapes.Poly):
                if self.render_mode == "sprite":
                    angle = degrees(shape.body.angle)
                    rot = cv2.getRotationMatrix2D(BOX_CENTER, angle, 1)
                    box = cv2.boxPoints((BOX_CENTER, BOX_SIZE, angle))
                    min_x = box[:, 0].min()
                    min_y = box[:, 1].min()
                    max_x = box[:, 0].max()
                    max_y = box[:, 1].max()
                    box_w = ceil(max_x - min_x)
                    box_h = ceil(max_y - min_y)
                    box_hw = box_w // 2
                    box_hh = box_h // 2
                    rot[0, 2] += box_hw - HW
                    rot[1, 2] += box_hh - HH
                    src = cv2.warpAffine(CRATE, rot, (box_w, box_h))
                    x, y = to_tex_coords(shape.body.position + (-box_hw, box_hh))
                    composite(src, self.texture, (y, x))
                else:
                    vertices = np.array(
                        [
                            to_tex_coords(
                                vertex.rotated(shape.body.angle) + shape.body.position
                            )
                            for vertex in shape.get_vertices()
                        ]
                    )
                    if self.render_mode == "fill":
                        cv2.fillPoly(self.texture, [vertices], color=self.shape_color)
                    else:
                        cv2.polylines(
                            self.texture,
                            [vertices],
                            isClosed=True,
                            color=self.shape_color,
                        )
            elif isinstance(shape, pymunk.shapes.Circle):
                if self.render_mode == "sprite":
                    angle == degrees(shape.body.angle)
                    rot = cv2.getRotationMatrix2D(BALL_CENTER, angle, 1)
                    src = cv2.warpAffine(BALL, rot, BALL_SIZE)
                    x, y = to_tex_coords(
                        shape.body.position + (-BALL_RADIUS, BALL_RADIUS)
                    )
                    composite(src, self.texture, (y, x))
                else:
                    pos = shape.body.position
                    center = to_tex_coords(pos)
                    circle_edge = pos + Vec2d(shape.radius, 0).rotated(shape.body.angle)
                    if self.render_mode == "fill":
                        cv2.circle(
                            self.texture,
                            center,
                            round(shape.radius),
                            self.shape_color,
                            -1,
                        )
                    else:
                        cv2.circle(
                            self.texture, center, round(shape.radius), self.shape_color
                        )
                        cv2.line(
                            self.texture,
                            center,
                            to_tex_coords(circle_edge),
                            self.shape_color,
                        )


class PhysicsApp(App):
    async def on_start(self):
        space = pymunk.Space()
        space.gravity = 0, -20
        space.damping = 0.9

        # Boxes
        for i in range(3):
            for j in range(3 - i):
                body = pymunk.Body(BOX_MASS, pymunk.moment_for_box(BOX_MASS, BOX_SIZE))
                body.position = (
                    1.3 * BOX_SIZE.x * i + 20,
                    1.3 * BOX_SIZE.y * j + GROUND_LEVEL,
                )
                box = pymunk.Poly.create_box(body, size=BOX_SIZE)
                box.elasticity = 0.3
                box.friction = 0.8
                space.add(body, box)

        # Ball
        body = pymunk.Body(
            BALL_MASS, pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
        )
        body.position = 100, 30
        body.velocity = -75, 5
        body.angular_velocity = -5
        ball = pymunk.Circle(body, BALL_RADIUS)
        ball.elasticity = 1
        ball.friction = 0.8
        space.add(body, ball)

        # Ground
        segment = pymunk.Segment(
            space.static_body, (0, GROUND_LEVEL), (540, GROUND_LEVEL), 1
        )
        segment.elasticity = 1
        segment.friction = 1.0
        space.add(segment)

        # Vertical Wall
        segment = pymunk.Segment(space.static_body, (0, GROUND_LEVEL), (0, 200), 1)
        segment.elasticity = 1
        segment.friction = 1.0
        space.add(segment)

        space_renderer = SpaceRenderer(
            space,
            render_mode="sprite",
            dt=0.03,
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
        )
        space_renderer.run_simulation()

        background = Image(
            path=PATH_TO_BACKGROUND, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )

        self.add_gadgets(background, space_renderer)


if __name__ == "__main__":
    PhysicsApp(title="Rigid Body Physics Simulation").run()
