"""A shadow caster gadget."""
from bisect import bisect
from collections.abc import Callable
from dataclasses import dataclass, field
from itertools import product
from math import dist
from typing import Literal

import cv2
import numpy as np
from numpy.typing import NDArray

from ..colors import AWHITE, BLACK, TRANSPARENT, WHITE, AColor, Color
from .graphics import (
    Graphics,
    Interpolation,
    Point,
    PosHint,
    PosHintDict,
    Region,
    Size,
    SizeHint,
    SizeHintDict,
    clamp,
)

__all__ = [
    "Camera",
    "Interpolation",
    "LightSource",
    "Point",
    "PosHint",
    "PosHintDict",
    "Restrictiveness",
    "ShadowCaster",
    "Size",
    "SizeHint",
    "SizeHintDict",
]

AGRAY = AColor(50, 50, 50)
QUADS = tuple(product((1, -1), (1, -1), (False, True)))

Restrictiveness = Literal["permissive", "moderate", "reestrictive"]
"""
The restrictiveness of the shadow caster.

:class:`Restrictiveness` is one of "permissive", "moderate", "restrictive".

For "permissive", any interval is visible as long as any of it's start, center, or end
points are visible. For "moderate", the center and either end must be visible. For
"restrictive", all points in the interval must be visible.
"""


@dataclass(slots=True)
class Camera:
    """
    The camera determines the visible portion of the map.

    If the camera's size is not equal to the caster's size, the camera will resize the
    visible portion of the map to fill the caster's size. To prevent resizing the
    visible portion of the map, the camera's size should be equal to the caster's size.

    Parameters
    ----------
    pos : Point
        The position of the upper-left corner of the camera on the map.
    size : Size
        Size of the camera.

    Methods
    -------
    get_submap(map):
        Get the section of the map visible by the camera.

    Notes
    -----
    Submap values for areas of the camera that are out-of-bounds of the map will be
    zero.
    """

    pos: Point
    size: Size

    def get_submap(self, map: NDArray[np.uint32]) -> NDArray[np.uint32]:
        """
        Get the section of a map visible by the camera.

        Returns
        -------
        NDArray[np.uint32]
            Section of map visible by the camera.
        """
        submap = np.zeros(self.size, dtype=np.uint8)

        source = Region.from_rect((0, 0), map.shape)
        dest = Region.from_rect(self.pos, self.size)

        if intersection := source & dest:
            rect = next(intersection.rects())
            submap[rect.to_slices(self.pos)] = map[rect.to_slices()]

        return submap


@dataclass(slots=True)
class LightSource:
    """
    A light source.

    Parameters
    ----------
    coords : float[tuple, tuple], default: (0.0, 0.0)
        Coordinates of light source on map.
    color : Color, default: WHITE
        Color of light source.

    Attributes
    ----------
    coords : float[tuple, tuple]
        Coordinates of light source on map.
    color : Color
        Color of light source.
    """

    coords: tuple[float, float] = 0.0, 0.0
    color: Color = WHITE


@dataclass(slots=True)
class _Interval:
    """
    A continuous interval.

    Parameters
    ----------
    start : float
        Start of interval.
    end : float
        End of interval.

    Attributes
    ----------
    start : float
        Start of interval.
    end : float
        End of interval.
    """

    start: float
    end: float
    center: float = field(init=False)

    def __post_init__(self):
        self.center = (self.start + self.end) / 2

    def __contains__(self, item: float) -> bool:
        return self.start <= item <= self.end

    def __gt__(self, other):
        if isinstance(other, (float, int)):
            return other < self.start

        return (other.start, other.end) < (self.start, self.end)


class ShadowCaster(Graphics):
    r"""
    A restrictive precise angle shadowcaster.

    :meth:`cast_shadows` must be called to generate or update :attr:`texture`.

    Parameters
    ----------
    map : NDArray[np.uint32]
        A 2-d map. Non-zero values are walls.
    camera : Camera
        A camera that determines the visible portion of the map.
    tile_colors : list[AColor] | None, default: None
        A value `n` in the map will be colored ``tile_colors[n]``. If ``None``,
        `tile_colors` will be set to ``[AGRAY, AWHITE]``.
    light_sources : list[LightSource] | None, default: None
        A list of all light sources on the map.
    ambient_light : Color, default: BLACK
        Color of ambient light. Default is no light.
    restrictiveness : Restrictiveness, default: "moderate"
        Restrictiveness of casting algorithm.
    light_decay : Callable[[float], float], default: lambda d: 1 if d == 0 else 1 / d
        The strength of light as a function of distance from origin.
    radius : int, default: 20
        Max visible radius from a light source.
    smoothing : float, default: 1.0 / 3.0
        Smoothness of shadow edges. This value will be clamped between `0` and `1`.
    not_visible_blocks : bool, default: True
        If true, all not-visible cells will be treated as opaque.
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        If gadget is transparent, the alpha channel of the underlying texture will be
        multiplied by this value. (0 <= alpha <= 1.0)
    interpolation : Interpolation, default: "linear"
        Interpolation used when gadget is resized.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: True
        A transparent gadget allows regions beneath it to be painted. Additionally,
        non-transparent graphic gadgets are not alpha composited.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    map : NDArray[np.uint32]
        A 2-d map. Non-zero values are walls.
    camera : Camera
        A camera that determines the visible portion of the map.
    tile_colors : list[AColor]
        A value `n` in the map will be colored ``tile_colors[n]``.
    light_sources : list[LightSource]
        A list of all light sources on the map.
    ambient_light : Color
        Color of ambient light.
    restrictiveness : Restrictiveness
        Restrictiveness of casting algorithm.
    light_decay : Callable[[float], float]
        The strength of light as a function of distance from origin.
    radius : int
        Max visible radius from a light source.
    smoothing : float
        Smoothness of shadow edges.
    not_visible_blocks : bool
        If true, all not-visible cells will be treated as opaque.
    texture : NDArray[np.uint8]
        uint8 RGBA color array.
    default_color : AColor
        Default texture color.
    alpha : float
        Transparency of gadget if :attr:`is_transparent` is true.
    interpolation : Interpolation
        Interpolation used when gadget is resized.
    size : Size
        Size of gadget.
    height : int
        Height of gadget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of gadget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of gadget.
    y : int
        Y-coordinate of top of gadget.
    left : int
        X-coordinate of left side of gadget.
    x : int
        X-coordinate of left side of gadget.
    bottom : int
        Y-coordinate of bottom of gadget.
    right : int
        X-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    parent: GadgetBase | None
        Parent gadget.
    children : list[GadgetBase]
        Children gadgets.
    is_transparent : bool
        True if gadget is transparent.
    is_visible : bool
        True if gadget is visible.
    is_enabled : bool
        True if gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    cast_shadows():
        Update texture by shadow casting all light sources.
    to_map_coords(point: Point):
        Convert a point in the gadget's local coordinates to a point in the map's
        coordinates.
    to_png(path):
        Write :attr:`texture` to provided path as a `png` image.
    on_size():
        Update gadget after a resize.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        Return true if point collides with visible portion of gadget.
    collides_gadget(other):
        Return true if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\*gadgets):
        Add multiple child gadgets.
    remove_gadget(gadget):
        Remove a child gadget.
    pull_to_front():
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root():
        Yield all descendents of the root gadget (preorder traversal).
    walk():
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse():
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors():
        Yield all ancestors of this gadget.
    subscribe(source, attr, action):
        Subscribe to a gadget property.
    unsubscribe(source, attr):
        Unsubscribe to a gadget property.
    on_key(key_event):
        Handle key press event.
    on_mouse(mouse_event):
        Handle mouse event.
    on_paste(paste_event):
        Handle paste event.
    tween(...):
        Sequentially update gadget properties over time.
    on_add():
        Apply size hints and call children's `on_add`.
    on_remove():
        Call children's `on_remove`.
    prolicide():
        Recursively remove all children.
    destroy():
        Remove this gadget and recursively remove all its children.
    """

    def __init__(
        self,
        *,
        map: NDArray[np.uint32],
        camera: Camera,
        tile_colors: list[AColor] | None = None,
        light_sources: list[LightSource] | None = None,
        ambient_light: Color = BLACK,
        restrictiveness: Restrictiveness = "moderate",
        light_decay: Callable[[float], float] = lambda d: 1 if d == 0 else 1 / d,
        radius: int = 20,
        smoothing: float = 1.0 / 3.0,
        not_visible_blocks: bool = True,
        is_transparent: bool = True,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            is_transparent=is_transparent,
            default_color=default_color,
            alpha=alpha,
            interpolation=interpolation,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self.map = map
        self.camera = camera
        self.tile_colors = np.array(tile_colors or [AGRAY, AWHITE], dtype=np.uint8)
        self.light_sources = light_sources or []
        self.ambient_light = ambient_light
        self.restrictiveness = restrictiveness
        self.light_decay = light_decay
        self.radius = radius
        self.smoothing = clamp(smoothing, 0.0, 1.0)
        self.not_visible_blocks = not_visible_blocks

    def cast_shadows(self):
        """Update texture by shadow casting all light sources."""
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

        # Combined light colors for all light_sources:
        total_light = np.full((h, w, 3), self.ambient_light, dtype=float)

        for light_source in self.light_sources:
            colors = np.zeros_like(total_light)

            # Calculate light position in camera's coordinates:
            ly, lx = light_source.coords
            origin = round(v_scale * (ly - cy)), round(h_scale * (lx - cx))

            color = light_source.color

            for quad in QUADS:
                self._visible_points_quad(quad, origin, color, colors, map)

            total_light += colors

        colored_map = self.tile_colors[map]
        self.texture[..., :3] = colored_map[..., :3] * np.clip(
            total_light / 255, 0.0, 1.0
        )
        self.texture[..., 3] = colored_map[..., 3]

    def _visible_points_quad(self, quad, origin, color, colors, map):
        y, x, vert = quad
        oy, ox = origin
        h, w, _ = colors.shape

        light_decay = self.light_decay
        smooth_radius = self.radius + self.smoothing

        obstructions = []
        for i in range(self.radius):
            if (
                len(obstructions) == 1
                and obstructions[0].start == 0.0
                and obstructions[0].end == 1.0
            ):
                return

            theta = 1.0 / float(i + 1)
            if vert:
                py = oy + i * y
            else:
                px = ox + i * x

            for j in range(i + 1):
                if vert:
                    px = ox + j * x
                else:
                    py = oy + j * y

                p = py, px

                if not (0 <= py < h and 0 <= px < w):
                    continue

                if (d := dist(origin, p)) <= smooth_radius:
                    interval = _Interval(j * theta, (j + 1) * theta)

                    if self._point_is_visible(interval, obstructions):
                        colors[p] = color
                        colors[p] *= light_decay(d)

                        if map[p] != 0:
                            self._add_obstruction(obstructions, interval)

                    elif self.not_visible_blocks:
                        self._add_obstruction(obstructions, interval)

    def _point_is_visible(self, interval: _Interval, obstructions):
        start_visible = center_visible = end_visible = True

        a = bisect(obstructions, interval.start)
        if a > 0:
            a -= 1

        b = bisect(obstructions, interval.end)
        if b < len(obstructions):
            b += 1

        for i in range(a, b):
            obstruction = obstructions[i]

            if start_visible and interval.start in obstruction:
                start_visible = False

            if center_visible and interval.center in obstruction:
                center_visible = False

            if end_visible and interval.end in obstruction:
                end_visible = False

        match self.restrictiveness:
            case "permissive":
                return center_visible or start_visible or end_visible
            case "moderate":
                return center_visible and (start_visible or end_visible)
            case "restrictive":
                return center_visible and start_visible and end_visible

    def _add_obstruction(self, obstructions, obstruction: _Interval):
        start = obstruction.start
        end = obstruction.end

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
            obstructions.insert(a, _Interval(start, end))
        else:
            obstructions[a:b] = [_Interval(start, end)]

    def to_map_coords(self, point: Point) -> tuple[float, float]:
        """
        Convert a point in the gadget's local coordinates to a point in the map's
        coordinates.

        Parameters
        ----------
        point : Point
            Point in local coordinates.

        Returns
        -------
        tuple[float, float]
            The coordinates of the point in the map.
        """
        y, x = point
        h, w = self.size

        cy, cx = self.camera.pos
        ch, cw = self.camera.size

        return ch / h * y + cy, cw / w * x + cx
