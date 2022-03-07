from bisect import bisect
from itertools import product
from math import dist
from typing import Callable

import cv2
import numpy as np

from ...clamp import clamp
from ...colors import AColor, AWHITE
from ..graphic_widget import GraphicWidget, Point
from .shadow_caster_data_structures import (
    Camera,
    Coordinates,
    Interval,
    LightIntensity,
    LightSource,
    Restrictiveness,
)


AGRAY = AColor(50, 50, 50)
QUADS = tuple(product((1, -1), (1, -1), (False, True)))


class ShadowCaster(GraphicWidget):
    """
    A restrictive precise angle shadowcaster. `cast_shadows` must be
    called to generate or update texture.

    Parameters
    ----------
    map : np.ndarray
        A 2-d map. Non-zero values are walls.
    camera : Camera
        A camera that determines the visible portion of the map.
    tile_colors : list[AColor] | None, default: None
        A value `n` in the map will be colored `tile_color[n]`. If `None`,
        `tile_colors` will be set to `[AGRAY, AWHITE]`.
    light_sources : list[LightSource] | None, default: None
        Position of each light source. If `None`, `light_sources` will be set to an
        empty list.
    ambient_light : LightIntensity, default: LightIntensity(0.0, 0.0, 0.0)
        Ambient light.
    light_decay : Callable[[float], float], default: lambda d: 1 if d == 0 else 1 / d
        The strength of light as a function of distance from origin.
    radius : int, default: 20
        Max visible radius.
    smoothing : float, default: 1.0 / 3.0
        Smoothness of shadow edges. This value will be clamped between `0` and `1`.
    not_visible_blocks : bool, default: True
        If `True`, all not-visible cells will be treated as opaque.
    restrictiveness : Restrictiveness, default: Restrictiveness.MODERATE
        Restrictiveness modifies the visibility of points.
    """
    def __init__(
        self,
        map: np.ndarray,
        camera: Camera,
        tile_colors: list[AColor] | None=None,
        light_sources: list[LightSource] | None=None,
        ambient_light: LightIntensity=LightIntensity(0.0, 0.0, 0.0),
        light_decay: Callable[[float], float]=lambda d: 1 if d == 0 else 1 / d,
        radius: int=20,
        smoothing: float=1.0/3.0,
        not_visible_blocks: bool=True,
        restrictiveness: Restrictiveness=Restrictiveness.MODERATE,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.map = map
        self.camera = camera
        self.tile_colors = np.array(tile_colors or [AGRAY, AWHITE], dtype=np.uint8)
        self.light_sources = light_sources or [ ]
        self.ambient_light = ambient_light
        self.light_decay = light_decay
        self.radius = radius
        self.smoothing = clamp(smoothing, 0.0, 1.0)
        self.not_visible_blocks = not_visible_blocks
        self.restrictiveness = restrictiveness

    def cast_shadows(self):
        """
        Update texture by shadow casting all light sources.
        """
        h, w, _ = self.texture.shape

        cy, cx = self.camera.pos
        ch, cw = self.camera.size

        v_scale = h / ch
        h_scale = w / cw

        map = cv2.resize(
            self.camera.get_submap(self.map),
            (w, h),
            interpolation=cv2.INTER_NEAREST,
        )

        # Combined light intensities for all light_sources:
        total_light = np.full((h, w, 3), self.ambient_light, dtype=float)

        for light_source in self.light_sources:
            intensities = np.zeros_like(total_light)

            # Calculate light position in camera's coordinates:
            ly, lx = light_source.coords
            origin = round(v_scale * (ly - cy)), round(h_scale * (lx - cx))

            intensity = light_source.intensity

            for quad in QUADS:
                self._visible_points_quad(quad, origin, intensity, intensities, map)

            total_light += intensities

        colored_map = self.tile_colors[map]
        self.texture[..., :3] = colored_map[..., :3] * np.clip(total_light, 0.0, 1.0)
        self.texture[..., 3] = colored_map[..., 3]

    def _visible_points_quad(self, quad, origin, intensity, intensities, map):
        y, x, vert = quad
        oy, ox = origin
        h, w, _ = intensities.shape

        light_decay = self.light_decay
        smooth_radius = self.radius + self.smoothing

        obstructions = [ ]
        for i in range(self.radius):
            if len(obstructions) == 1 and obstructions[0] == (0.0, 1.0):
                return

            theta = 1.0 / float(i + 1)

            for j in range(i + 1):
                if vert:
                    p = py, px = oy + i * y, ox + j * x
                else:
                    p = py, px = oy + j * y, ox + i * x

                if not (0 <= py < h and 0 <= px < w):
                    continue

                if (d := dist(origin, p)) <= smooth_radius:
                    interval = Interval(j * theta, (j + 1) * theta)

                    if self._point_is_visible(interval, obstructions):
                        intensities[p] = intensity
                        intensities[p] *= light_decay(d)

                        if map[p] != 0:
                            self._add_obstruction(obstructions, interval)

                    elif self.not_visible_blocks:
                        self._add_obstruction(obstructions, interval)

    def _point_is_visible(self, interval: Interval, obstructions):
        start_visible = center_visible = end_visible = True
        start, end = interval
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

    def _add_obstruction(self, obstructions, obstruction: Interval):
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
            obstructions.insert(a, Interval(start, end))
        else:
            obstructions[a: b] = [Interval(start, end)]

    def to_map_coords(self, point: Point) -> Coordinates:
        """
        Convert a point in the widget's local coordinates to a
        point in the map's coordinates.

        Parameters
        ----------
        point : Point
            Point in local coordinates.
        """
        y, x = point
        h, w = self.size

        cy, cx = self.camera.pos
        ch, cw = self.camera.size

        return Coordinates(ch / h * y + cy, cw / w * x + cx)
