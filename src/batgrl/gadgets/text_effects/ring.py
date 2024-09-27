"""A ring effect."""

import asyncio
from math import cos, dist, sin, tau
from random import choice, random
from time import perf_counter

import numpy as np

from ...colors import BLUE, WHITE, Color, gradient, lerp_colors
from ...geometry import BezierCurve, Point, Size, move_along_path
from ..text import Text
from ..text_field import TextParticleField, particle_data_from_canvas
from ._particle import Particle

RNG = np.random.default_rng()
RING_COLORS = [Color.from_hex("8a008a"), Color.from_hex("00d1ff")]
DISPERSE_COLORS = gradient(BLUE, WHITE, 10)


async def ring_effect(text: Text):
    """
    Create a ring effect.

    Parameters
    ----------
    text : Text
        The text gadget which to run the effect.

    Warnings
    --------
    Modifying `text` size while effect is running will break the effect.
    """
    pos, cells = particle_data_from_canvas(text.canvas)
    indices = np.arange(len(pos))
    RNG.shuffle(indices)

    field = TextParticleField(
        particle_positions=pos,
        particle_cells=cells,
        size_hint={"height_hint": 1.0, "width_hint": 1.0},
    )

    particles = list(Particle.iter_from_field(field))
    for particle in particles:
        particle.final_pos = particle.pos
    positions = (RNG.random((field.nparticles, 2)) * text.size).astype(int)
    field.particle_positions = positions

    min_dim = min(text.height, text.width / 2)
    max_radius = int(2**0.5 * (min_dim / 2))

    radii = list(range(max_radius - 3, 3, -min_dim // 5))
    center = Point(text.height // 2, text.width // 2)

    text.add_gadget(field)

    radius_to_particles = await _move_to_rings(particles, radii, center)
    await _spin_rings(radius_to_particles, center)
    await _disperse(particles, text.size)
    radius_to_particles = await _move_to_rings(particles, radii, center)
    await _spin_rings(radius_to_particles, center, reverse=True)
    await _disperse(particles, text.size)
    radius_to_particles = await _move_to_rings(particles, radii, center)
    await _spin_rings(radius_to_particles, center)
    await _settle(particles, text)

    text.remove_gadget(field)


def _distance_to_circle(p: Point, radius: int, center: Point) -> float:
    py, px = p
    px /= 2
    cy, cx = center
    cx /= 2
    return abs(dist((py, px), (cy, cx)) - radius)


def _closest_point_on_circle(
    p: Point, radius: int, center: Point
) -> tuple[float, float]:
    py, px = p
    px /= 2
    cy, cx = center
    cx /= 2
    vy, vx = py - cy, px - cx
    length_v = (vy**2 + vx**2) ** 0.5
    if length_v == 0:
        return cy, 2 * cx
    ty = cy + vy / length_v * radius
    tx = cx + vx / length_v * radius
    return ty, 2 * tx


def _rotate_around_center(p: Point, center: Point, theta: float) -> tuple[float, float]:
    py, px = p
    cy, cx = center
    oy, ox = py - cy, (px - cx) / 2

    sth = sin(theta)
    cth = cos(theta)

    return oy * sth - ox * cth + cy, 2 * (oy * cth + ox * sth) + cx


def _random_nearby_point(p: Point) -> tuple[float, float]:
    d = random() * 7
    theta = random() * tau
    py, px = p

    return d * sin(theta) + py, d * cos(theta) + px


async def _move_to_rings(
    particles: list[Particle], radii: list[int], center: Point
) -> dict[int, list[Particle]]:
    ring_colors = {
        radius: RING_COLORS[i % len(RING_COLORS)] for i, radius in enumerate(radii)
    }
    radius_to_particles = {radius: [] for radius in radii}
    paths = []
    for particle in particles:
        radius = min(
            radii, key=lambda radius: _distance_to_circle(particle.pos, radius, center)
        )
        radius_to_particles[radius].append(particle)
        p = _closest_point_on_circle(particle.pos, radius, center)
        paths.append([BezierCurve(np.array([particle.pos, p]))])
        particle.ring_point = p
        particle.ring_color = ring_colors[radius]

    def create_fade(particle):
        a = Color(*particle.cell["fg_color"].tolist())
        b = particle.ring_color

        def fade_particle(p):
            particle.cell["fg_color"] = lerp_colors(a, b, p)

        return fade_particle

    motions = [
        move_along_path(
            particle,
            path,
            speed=5,
            easing="in_circ",
            on_progress=create_fade(particle),
        )
        for particle, path in zip(particles, paths)
    ]

    await asyncio.gather(*motions)

    return radius_to_particles


async def _spin_rings(
    radius_to_particles: dict[int, list[Particle]], center: Point, reverse: bool = False
):
    start = perf_counter()
    theta = tau / 100

    while True:
        elapsed = perf_counter() - start
        if elapsed > 3:
            return

        for i, particles in enumerate(radius_to_particles.values()):
            direction = 1 if (i + reverse) % 2 else -1
            for particle in particles:
                y, x = _rotate_around_center(
                    particle.ring_point, center, direction * theta
                )
                particle.pos = int(y), int(x)

        theta += tau / 100
        await asyncio.sleep(0)


async def _disperse(particles: list[Particle], field_size: Size):
    paths = []
    for particle in particles:
        controls = [particle.pos] + [
            _random_nearby_point(particle.pos) for _ in range(6)
        ]
        particle_path = [
            BezierCurve(np.array(controls[:3])),
            BezierCurve(np.array(controls[2:5])),
            BezierCurve(np.array(controls[4:])),
        ]
        paths.append(particle_path)

    def create_fade(particle):
        a = Color(*particle.cell["fg_color"].tolist())
        b = choice(DISPERSE_COLORS)

        def fade_particle(p):
            particle.cell["fg_color"] = lerp_colors(a, b, p)

        return fade_particle

    motions = [
        move_along_path(
            particle,
            path,
            speed=10,
            on_progress=create_fade(particle),
        )
        for particle, path in zip(particles, paths)
    ]

    await asyncio.gather(*motions)


async def _settle(particles: list[Particle], text: Text):
    paths = []
    for particle in particles:
        controls = [
            particle.pos,
            *(_random_nearby_point(particle.pos) for _ in range(5)),
            particle.final_pos,
        ]
        particle_path = [
            BezierCurve(np.array(controls[:3])),
            BezierCurve(np.array(controls[2:5])),
            BezierCurve(np.array(controls[4:])),
        ]
        paths.append(particle_path)

    def create_fade(particle):
        a = Color(*particle.cell["fg_color"].tolist())
        b = Color(*text.canvas[particle.final_pos]["fg_color"].tolist())

        def fade_particle(p):
            particle.cell["fg_color"] = lerp_colors(a, b, p)

        return fade_particle

    motions = [
        move_along_path(
            particle,
            path,
            speed=20,
            easing="out_quad",
            on_progress=create_fade(particle),
        )
        for particle, path in zip(particles, paths)
    ]

    await asyncio.gather(*motions)
