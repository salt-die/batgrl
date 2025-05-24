"""A black hole effect."""

import asyncio
from random import choice
from typing import cast

import numpy as np

from ...array_types import Coords
from ...colors import BLACK, WHITE, Color, gradient, lerp_colors
from ...geometry import (
    BezierCurve,
    Point,
    Pointlike,
    clamp,
    move_along_path,
    points_on_circle,
)
from ..text import Text
from ..text_field import TextParticleField
from ._particle import Particle

STARS = "*✸✺✹✷✵✶⋆'.⬫⬪⬩⬨⬧⬦⬥"
UNSTABLE = "◦◎◉●◉◎◦"
UNSTABLE_COLORS = [
    Color.from_hex("ffcc0d"),
    Color.from_hex("ff7326"),
    Color.from_hex("ff194d"),
    Color.from_hex("bf2669"),
    Color.from_hex("702a8c"),
    Color.from_hex("049dbf"),
]
STAR_COLOR = Color.from_hex("4a4a4d")
STAR_GRADIENT = gradient(STAR_COLOR, WHITE, n=6)
TOP_COLOR = Color.from_hex("8a008a")
MIDDLE_COLOR = Color.from_hex("00d1ff")
RNG = np.random.default_rng()


class _BlackHoleParticle(Particle):
    final_ord: int
    final_fg_color: Color
    final_pos: Pointlike


async def black_hole_effect(text: Text):
    """
    Create a black hole effect.

    Parameters
    ----------
    text : Text
        The text gadget which to run the effect.

    Warnings
    --------
    Modifying `text` size while effect is running will break the effect.
    """
    field = TextParticleField(size_hint={"height_hint": 1.0, "width_hint": 1.0})
    field.particles_from_cells(text.canvas)

    all_particles = list(_BlackHoleParticle.iter_from_field(field))

    coords = cast(Coords, RNG.random((field.nparticles, 2)) * text.size)
    for particle, position in zip(all_particles, coords):
        particle.final_ord = particle.cell["ord"]  # type: ignore
        particle.final_fg_color = Color(*particle.cell["fg_color"].tolist())
        particle.final_pos = particle.pos
        particle.cell["ord"] = ord(choice(STARS))
        particle.cell["fg_color"] = choice(STAR_GRADIENT)
        particle.pos = position

    black_hole = TextParticleField(
        size_hint={"height_hint": 1.0, "width_hint": 1.0}, is_transparent=True
    )
    black_hole_radius = clamp(text.height // 3, 3, text.width // 3)
    black_hole_center = Point(text.height // 2, text.width // 2)
    nparticles = black_hole_radius * 3
    black_hole.particle_coords = field.particle_coords[-nparticles:]
    black_hole.particle_cells = field.particle_cells[-nparticles:]
    black_hole_particles = list(Particle.iter_from_field(black_hole))

    field.particle_coords = field.particle_coords[:-nparticles]
    field.particle_cells = field.particle_cells[:-nparticles]
    other_particles = all_particles[:-nparticles]

    circle_positions = points_on_circle(black_hole.nparticles, black_hole_radius)
    black_hole_positions = circle_positions.copy()
    black_hole_positions[:, 1] *= 2
    black_hole_positions += black_hole_center

    text.add_gadgets(field, black_hole)

    await _forming(black_hole_particles, black_hole_positions)

    rot = _rotating(black_hole, circle_positions, black_hole_center)
    rotate_task = asyncio.create_task(rot)

    await _consuming(other_particles, black_hole_positions, black_hole_center)

    rotate_task.cancel()

    await _collapsing(
        black_hole_particles,
        black_hole.particle_coords,
        black_hole_center,
        black_hole_radius,
    )

    field.particle_coords = np.vstack(
        [field.particle_coords, black_hole.particle_coords]
    )
    field.particle_cells = np.append(field.particle_cells, black_hole.particle_cells)

    await _point_char(black_hole, black_hole_center)
    text.remove_gadget(black_hole)

    await _exploding(all_particles, black_hole_center)

    text.remove_gadget(field)


async def _forming(particles: list[Particle], coords: Coords):
    for particle in particles:
        particle.cell["ord"] = ord("✸")
        particle.cell["fg_color"] = WHITE

    paths = [
        [BezierCurve(np.array([particle.pos, position], float))]
        for particle, position in zip(particles, coords)
    ]

    speed = len(particles)
    motions = [
        move_along_path(particle, path, speed=speed, easing="in_out_sine")
        for particle, path in zip(particles, paths)
    ]

    tasks = []
    for motion in motions:
        tasks.append(asyncio.create_task(motion))
        await asyncio.sleep(1 / speed)

    await asyncio.gather(*tasks)


async def _rotating(black_hole: TextParticleField, coords: Coords, center: Point):
    angles = np.linspace(0, 2 * np.pi, 100, endpoint=False)
    cos = np.cos(angles)
    sin = np.sin(angles)
    rot = np.array([[cos, -sin], [sin, cos]]).T
    i = 0

    while True:
        new_positions = coords @ rot[i]
        new_positions[:, 1] *= 2
        new_positions += center
        black_hole.particle_coords = new_positions
        i += 1
        i %= 100
        await asyncio.sleep(0.01)


async def _consuming(
    particles: list[_BlackHoleParticle],
    coords: Coords,
    center: Point,
):
    particles.sort(key=lambda p: (p.pos.y - center.y) ** 2 + (p.pos.x - center.x) ** 2)

    paths = [
        [BezierCurve(np.array([particle.pos, choice(coords), center]))]
        for particle in particles
    ]

    def create_fade(particle):
        start_color = particle.cell["fg_color"]

        def fade_particle(p):
            particle.cell["fg_color"] = lerp_colors(start_color, BLACK, p)

        return fade_particle

    motions = [
        move_along_path(
            particle, path, speed=20, easing="in_exp", on_progress=create_fade(particle)
        )
        for particle, path in zip(particles, paths)
    ]

    tasks = []
    nconsumes = clamp(int(len(particles) / 10), 2, 15)
    while motions:
        for motion in motions[:nconsumes]:
            tasks.append(asyncio.create_task(motion))
        motions = motions[nconsumes:]
        nconsumes += 1
        await asyncio.sleep(0.10)

    await asyncio.gather(*tasks)


async def _collapsing(
    particles: list[Particle],
    coords: Coords,
    center: Point,
    radius: int,
):
    new_pos = (coords - center).astype(float)
    new_pos *= (radius + 3) / radius
    new_pos += center

    paths = []
    for particle, position in zip(particles, new_pos):
        particle_path = [
            BezierCurve(np.array([particle.pos, position])),
            BezierCurve(np.array([position, center])),
        ]
        paths.append(particle_path)

    motions = [
        move_along_path(particle, path, speed=20, easing="in_exp")
        for particle, path in zip(particles, paths)
    ]

    await asyncio.gather(*motions)


async def _point_char(black_hole: TextParticleField, center: Point):
    black_hole.particle_coords = np.array([center]).astype(np.float64)
    black_hole.particle_cells = black_hole.particle_cells[:1]
    for _ in range(3):
        for char in UNSTABLE:
            black_hole.particle_cells[0]["ord"] = ord(char)
            black_hole.particle_cells[0]["fg_color"] = choice(UNSTABLE_COLORS)
            await asyncio.sleep(0.05)


async def _exploding(particles: list[_BlackHoleParticle], center: Point):
    nearby_paths = []
    final_paths = []
    for particle in particles:
        particle.pos = center
        particle.cell["ord"] = particle.final_ord
        particle.cell["fg_color"] = choice(UNSTABLE_COLORS)
        near_point = choice(points_on_circle(6, 5))
        near_point[1] *= 2
        near_point += particle.final_pos
        nearby_paths.append([BezierCurve(np.array([particle.pos, near_point]))])
        final_paths.append([BezierCurve(np.array([near_point, particle.final_pos]))])

    nearby_motions = [
        move_along_path(particle, path, speed=20, easing="out_exp")
        for particle, path in zip(particles, nearby_paths)
    ]

    await asyncio.gather(*nearby_motions)

    def create_fade(particle):
        start_color = particle.cell["fg_color"]

        def fade_particle(p):
            particle.cell["fg_color"] = lerp_colors(
                start_color, particle.final_fg_color, p
            )

        return fade_particle

    final_motions = [
        move_along_path(
            particle,
            path,
            speed=7,
            easing="in_cubic",
            on_progress=create_fade(particle),
        )
        for particle, path in zip(particles, final_paths)
    ]

    await asyncio.gather(*final_motions)
