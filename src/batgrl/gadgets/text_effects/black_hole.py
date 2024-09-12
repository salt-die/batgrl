"""A black hole effect."""

import asyncio
from random import choice

import numpy as np
from numpy.typing import NDArray

from ...colors import BLACK, WHITE, Color, gradient, lerp_colors
from ...geometry import BezierCurve, Point, clamp, move_along_path, points_on_circle
from ..text import Text
from ..text_field import TextParticleField, particle_data_from_canvas
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
STAR_GRADIENT = gradient(STAR_COLOR, WHITE, 6)
TOP_COLOR = Color.from_hex("8a008a")
MIDDLE_COLOR = Color.from_hex("00d1ff")
RNG = np.random.default_rng()


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
    pos, cells = particle_data_from_canvas(text.canvas)
    indices = np.arange(len(pos))
    RNG.shuffle(indices)

    field = TextParticleField(
        particle_positions=pos[indices],
        particle_cells=cells[indices],
        size_hint={"height_hint": 1.0, "width_hint": 1.0},
    )

    all_particles = list(Particle.iter_from_field(field))

    positions = (RNG.random((field.nparticles, 2)) * text.size).astype(int)
    for particle, position in zip(all_particles, positions):
        particle.final_char = particle.cell["char"]
        particle.final_fg_color = Color(*particle.cell["fg_color"].tolist())
        particle.final_pos = particle.pos
        particle.cell["char"] = choice(STARS)
        particle.cell["fg_color"] = choice(STAR_GRADIENT)
        particle.pos = position

    black_hole = TextParticleField(
        size_hint={"height_hint": 1.0, "width_hint": 1.0}, is_transparent=True
    )
    black_hole_radius = clamp(text.height // 3, 3, text.width // 3)
    black_hole_center = Point(text.height // 2, text.width // 2)
    nparticles = black_hole_radius * 3
    black_hole.particle_positions = field.particle_positions[-nparticles:]
    black_hole.particle_cells = field.particle_cells[-nparticles:]
    black_hole_particles = list(Particle.iter_from_field(black_hole))

    field.particle_positions = field.particle_positions[:-nparticles]
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
        black_hole.particle_positions,
        black_hole_center,
        black_hole_radius,
    )

    field.particle_positions = np.vstack(
        [field.particle_positions, black_hole.particle_positions]
    )
    field.particle_cells = np.append(field.particle_cells, black_hole.particle_cells)

    await _point_char(black_hole, black_hole_center)
    text.remove_gadget(black_hole)

    await _exploding(all_particles, black_hole_center)

    text.remove_gadget(field)


async def _forming(particles: list[Particle], positions: NDArray[np.float32]):
    for particle in particles:
        particle.cell["char"] = "✸"
        particle.cell["fg_color"] = WHITE

    paths = [
        [BezierCurve(np.array([particle.pos, position], float))]
        for particle, position in zip(particles, positions)
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


async def _rotating(
    black_hole: TextParticleField, positions: NDArray[np.float32], center: Point
):
    angles = np.linspace(0, 2 * np.pi, 100, endpoint=False)
    cos = np.cos(angles)
    sin = np.sin(angles)
    rot = np.array([[cos, -sin], [sin, cos]]).T
    i = 0

    while True:
        new_positions = positions @ rot[i]
        new_positions[:, 1] *= 2
        new_positions += center
        black_hole.particle_positions = new_positions.astype(int)
        i += 1
        i %= 100
        await asyncio.sleep(0.01)


async def _consuming(
    particles: list[Particle], positions: NDArray[np.float32], center: Point
):
    particles.sort(key=lambda p: (p.pos.y - center.y) ** 2 + (p.pos.x - center.x) ** 2)

    paths = [
        [BezierCurve(np.array([particle.pos, choice(positions), center]))]
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
    positions: NDArray[np.float32],
    center: Point,
    radius: int,
):
    new_pos = (positions - center).astype(float)
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
    black_hole.particle_positions = np.array([center])
    black_hole.particle_cells = black_hole.particle_cells[:1]
    for _ in range(3):
        for char in UNSTABLE:
            black_hole.particle_cells[0]["char"] = char
            black_hole.particle_cells[0]["fg_color"] = choice(UNSTABLE_COLORS)
            await asyncio.sleep(0.05)


async def _exploding(particles: list[Particle], center: Point):
    nearby_paths = []
    final_paths = []
    for particle in particles:
        particle.pos = center
        particle.cell["char"] = particle.final_char
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
