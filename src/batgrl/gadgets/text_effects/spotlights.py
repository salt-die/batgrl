"""A spotlight effect."""

import asyncio
from dataclasses import dataclass
from random import randrange

import numpy as np
from numpy.typing import NDArray

from ...colors import BLUE, GREEN, RED, Color
from ...geometry import BezierCurve, Point, Size, move_along_path
from ..text import Text


@dataclass
class _SpotLight:
    pos: Point
    color: Color
    radius: float = 8
    falloff: float = 0.3


async def spotlights_effect(text: Text):
    """
    Create a spotlight effect.

    Parameters
    ----------
    text : Text
        The text gadget which to run the effect.

    Warnings
    --------
    Modifying `text` size while effect is running will break the effect.
    """
    cover = Text(size=text.size)
    cover.canvas[:] = text.canvas

    in_fg = text.canvas["fg_color"]
    in_bg = text.canvas["bg_color"]
    out_fg = cover.canvas["fg_color"]
    out_bg = cover.canvas["bg_color"]

    spotlights = [
        _SpotLight(pos=_random_point(text.size), color=RED),
        _SpotLight(pos=_random_point(text.size), color=GREEN),
        _SpotLight(pos=_random_point(text.size), color=BLUE),
    ]

    text.add_gadget(cover)
    for _ in range(5):
        positions = [_random_point(text.size) for _ in spotlights]
        await _move_spotlights(in_fg, in_bg, out_fg, out_bg, spotlights, positions)

    center = text.height // 2, text.width // 2
    positions = [center for _ in spotlights]
    await _move_spotlights(in_fg, in_bg, out_fg, out_bg, spotlights, positions)
    await _grow_spotlights(in_fg, in_bg, out_fg, out_bg, spotlights)
    text.remove_gadget(cover)


def _random_point(size: Size):
    h, w = size
    return randrange(h), randrange(w)


def _draw_spotlights(
    in_fg: NDArray[np.uint8],
    in_bg: NDArray[np.uint8],
    out_fg: NDArray[np.uint8],
    out_bg: NDArray[np.uint8],
    spotlights: list[_SpotLight],
):
    out_fg[:] = in_fg
    out_bg[:] = in_bg
    weighted = np.zeros_like(in_fg, float)
    for spotlight in spotlights:
        h, w, _ = in_fg.shape
        y, x = spotlight.pos
        x /= 2
        ys, xs = np.indices((h, w)).astype(float)
        xs /= 2

        distances = ((ys - y) ** 2 + (xs - x) ** 2) ** 0.5
        distances[distances > spotlight.radius] = np.inf
        weights = np.exp(-spotlight.falloff * distances)
        color = np.array(spotlight.color, float)
        color /= 255
        weighted += color * weights[:, :, None]

    weighted.clip(0, 1, out=weighted)
    out_fg[:] = (in_fg * weighted).astype(np.uint8)
    out_bg[:] = (in_bg * weighted).astype(np.uint8)


async def _move_spotlights(
    in_fg: NDArray[np.uint8],
    in_bg: NDArray[np.uint8],
    out_fg: NDArray[np.uint8],
    out_bg: NDArray[np.uint8],
    spotlights: list[_SpotLight],
    positions: list[Point],
):
    def draw(*args):
        _draw_spotlights(in_fg, in_bg, out_fg, out_bg, spotlights)

    paths = []
    for spotlight, position in zip(spotlights, positions):
        curve = BezierCurve(np.array([spotlight.pos, position], float))
        paths.append([curve])

    motions = [
        move_along_path(
            spotlight,
            path,
            speed=20,
            easing="in_out_quad",
            on_start=draw,
            on_progress=draw,
            on_complete=draw,
        )
        for spotlight, path in zip(spotlights, paths)
    ]
    await asyncio.gather(*motions)


async def _grow_spotlights(
    in_fg: NDArray[np.uint8],
    in_bg: NDArray[np.uint8],
    out_fg: NDArray[np.uint8],
    out_bg: NDArray[np.uint8],
    spotlights: list[_SpotLight],
):
    h, w, _ = in_fg.shape

    end_radius = ((h / 2) ** 2 + (w / 2) ** 2) ** 0.5
    frames = 100

    all_radii = [
        np.linspace(spotlight.radius, end_radius, frames) for spotlight in spotlights
    ]
    all_falloffs = [
        np.linspace(spotlight.falloff, 0, frames) for spotlight in spotlights
    ]

    for i in range(frames):
        for spotlight, radii, falloffs in zip(spotlights, all_radii, all_falloffs):
            spotlight.radius = radii[i]
            spotlight.falloff = falloffs[i]

        _draw_spotlights(in_fg, in_bg, out_fg, out_bg, spotlights)
        await asyncio.sleep(0.02)
