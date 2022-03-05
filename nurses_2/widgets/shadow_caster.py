from bisect import bisect
from enum import Enum
from itertools import product
from math import dist
from typing import NamedTuple, Callable

import cv2
import numpy as np

from ..clamp import clamp
from ..colors import AColor, AWHITE
from .graphic_widget import GraphicWidget, Point
from .raycaster.protocols import Map

AGRAY = AColor(50, 50, 50)
QUADS = tuple(product((1, -1), (1, -1), (False, True)))


class Range(NamedTuple):
    start: float
    end: float

    def __contains__(self, item: float) -> bool:
        return self.start <= item <= self.end

    def __gt__(self, other):
        if isinstance(other, (float, int)):
            return other < self.start

        return (other.start, other.end) < (self.start, self.end)


class Restrictiveness(str, Enum):
    PERMISSIVE = "permissive"
    MODERATE = "moderate"
    RESTRICTIVE = "restrictive"


class ShadowCaster(GraphicWidget):
    """
    A restrictive precise angle shadowcaster.

    Parameters
    ----------
    map : Map
        A 2-d map. Non-zero values are walls.
    tile_colors : list[AColor], default: [AGRAY, AWHITE]
        A value `n` in the map corresponds to `tile_color[n]`.
    light_sources : list[Point], default: [Point(0, 0)]
        Position of each light source.
    ambient_light : float, default: 0.0
        Ambient light. Must be between 0 and 1.
    light_decay : Callable[[float], float], default: lambda d: 1 if d == 0 else 1 / d
        The strength of light as a function of distance from origin.
    radius : int, default: 20
        Max visible radius.
    smoothing : float, default: 1.0 / 3.0
        Smoothness of vision bubbles. Must be between 0 and 1.
    not_visible_blocks : bool, default: True
        If `True`, all not visible cells will be treated as opaque.
    restrictiveness : Restrictiveness, default: Restrictiveness.MODERATE
        Restrictiveness modifies the visibility of points.
    """
    def __init__(
        self,
        map: Map,
        tile_colors: list[AColor]=[AGRAY, AWHITE],
        light_sources: list[Point]=[Point(0, 0)],
        ambient_light: float=0.0,
        light_decay: Callable[[float], float]=lambda d: 1 if d == 0 else 1 / d,
        radius: int=20,
        smoothing: float=1.0/3.0,
        not_visible_blocks: bool=True,
        restrictiveness: Restrictiveness=Restrictiveness.MODERATE,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.map = map
        self.tile_colors = np.array(tile_colors, dtype=np.uint8)
        self.light_sources = light_sources
        self.ambient_light = clamp(ambient_light, 0.0, 1.0)
        self.light_decay = light_decay
        self.radius = radius
        self.smoothing = clamp(smoothing, 0.0, 1.0)
        self.not_visible_blocks = not_visible_blocks
        self.restrictiveness = restrictiveness

    def update_visibility(self):
        h, w, _ = self.texture.shape

        self.resized_map = cv2.resize(self.map, (w, h))
        self.visibility = np.full((h, w), self.ambient_light, dtype=float)

        for light_source in self.light_sources:
            oy, ox = light_source
            oy *= 2
            if not (0 <= oy < h and 0 <= ox < w):
                continue

            self.visibility[oy: oy + 2, ox] = (
                np.clip(self.light_decay(0) + self.visibility[oy: oy + 2, ox], 0.0, 1.0)
            )

            self._visited = np.zeros((h, w), dtype=bool)
            for quad in QUADS:
                self._visible_points_quad(quad, Point(oy, ox))

        colored_map = self.tile_colors[self.resized_map]
        self.texture[..., :3] = colored_map[..., :3] * self.visibility[..., None]
        self.texture[..., 3] = colored_map[..., 3]

    def _visible_points_quad(self, quad, light_source):
        visibility = self.visibility
        h, w = visibility.shape
        light_decay = self.light_decay
        smooth_radius = self.radius + self.smoothing
        map = self.resized_map
        oy, ox = light_source

        obstructions = [ ]
        for i in range(1, self.radius):
            if len(obstructions) == 1 and obstructions[0] == (0.0, 1.0):
                return

            theta = 1.0 / float(i + 1)

            for j in range(i + 1):
                y, x, vert = quad

                if vert:
                    p = py, px = oy + i * y, ox + j * x
                else:
                    p = py, px = oy + j * y, ox + i * x

                if not (0 <= py < h and 0 <= px < w):
                    break

                if self._visited[p]:
                    continue
                else:
                    self._visited[p] = True

                d = dist(light_source, p)

                if d <= smooth_radius:
                    range_ = Range(j * theta, (j + 1) * theta)

                    if self._point_is_visible(range_, obstructions):
                        visibility[p] = clamp(light_decay(d) + visibility[p], 0.0, 1.0)

                        if map[p] != 0:
                            self._add_obstruction(obstructions, range_)

                    elif self.not_visible_blocks:
                        self._add_obstruction(obstructions, range_)

    def _point_is_visible(self, range_: Range, obstructions):
        start_visible = center_visible = end_visible = True
        start, end = range_
        center = (start + end) / 2

        a = bisect(obstructions, start)
        if a > 0:
            a -= 1

        b = bisect(obstructions, end)
        if b < len(obstructions):
            b += 1

        for i in range(a, b):
            obstruction = obstructions[i]

            if start_visible and start in obstruction:
                start_visible = False

            if center_visible and center in obstruction:
                center_visible = False

            if end_visible and end in obstruction:
                end_visible = False

        match self.restrictiveness:
            case Restrictiveness.PERMISSIVE:
                return center_visible or start_visible or end_visible
            case Restrictiveness.MODERATE:
                return center_visible and (start_visible or end_visible)
            case Restrictiveness.RESTRICTIVE:
                return center_visible and start_visible and end_visible

    def _add_obstruction(self, obstructions, obstruction: Range):
        start, end = obstruction

        a = bisect(obstructions, start)
        b = bisect(obstructions, end)

        if a > 0 and start <= obstructions[a - 1].end:
            start = obstructions[a - 1].start
            a -= 1

        if b < len(obstructions) and obstructions[b].end <= end:
            end = obstructions[b].end
            b += 1
        elif b > 0 and end < obstructions[b - 1].end:
            end = obstructions[b - 1].end

        if a == b:
            obstructions.insert(a, Range(start, end))
        else:
            obstructions[a: b] = [Range(start, end)]
