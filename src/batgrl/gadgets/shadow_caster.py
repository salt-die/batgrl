"""A shadow caster gadget."""

from collections.abc import Callable
from itertools import product
from typing import Literal

import numpy as np

from ..array_types import ULong2D
from ..colors import AWHITE, BLACK, TRANSPARENT, AColor, Color
from ._shadow_casting import cast_shadows
from .graphics import (
    Blitter,
    Graphics,
    Interpolation,
    Point,
    Pointlike,
    PosHint,
    Size,
    SizeHint,
    Sizelike,
    clamp,
)

__all__ = ["Point", "Restrictiveness", "ShadowCaster", "Size"]

AGRAY = AColor(50, 50, 50)
QUADS = tuple(product((1, -1), (1, -1), (False, True)))

Restrictiveness = Literal["permissive", "moderate", "restrictive"]
"""
The restrictiveness of the shadow caster.

``Restrictiveness`` is one of "permissive", "moderate", "restrictive".

For "permissive", any interval is visible as long as any of it's start, center, or end
points are visible. For "moderate", the center and either end must be visible. For
"restrictive", all points in the interval must be visible.
"""


def default_light_decay(x: float) -> float:
    if x == 0:
        return 1
    return 1 / x


class ShadowCaster(Graphics):
    r"""
    A restrictive precise angle shadowcaster.

    :meth:`cast_shadows` must be called to generate or update :attr:`texture`.

    Light decay distance and :attr:`radius` are calculated from the point of view of the
    ``caster_map`` and does not depend on the size of the camera or the size of the
    caster. As a consequence, changing the blitter should only change the resolution of
    the caster.

    ``light_coords`` and ``light_colors`` must be same length.

    Parameters
    ----------
    caster_map : ULong2D
        A 2-d map. Non-zero values are walls.
    camera_pos : Pointlike
        Position of camera in map.
    camera_size : Sizelike
        Size of camera. Determines how much of the map is visible.
    tile_colors : list[AColor] | None, default: None
        A value ``n`` in the map will be colored ``tile_colors[n]``. If ``None``,
        ``tile_colors`` will be set to ``[AGRAY, AWHITE]``.
    light_coords : list[tuple[float, float]] | None, default: None
        A list of coordinates for all light sources on the map.
    light_colors : list[Color] | None, default: None
        A list of colors for all light sources on the map.
    ambient_light : Color, default: BLACK
        Color of ambient light. Default is no light.
    restrictiveness : Restrictiveness, default: "permissive"
        Restrictiveness of casting algorithm.
    radius : int, default: 20
        Max visible radius from a light source.
    smoothing : float, default: 1.0 / 3.0
        Smoothness of shadow edges. This value will be clamped between ``0`` and ``1``.
    not_visible_blocks : bool, default: True
        Whether all not-visible cells will be treated as opaque.
    light_decay : Callable[[float], float], default: default_light_decay
        The strength of light as a function of distance from light origin. The default
        decay is ``1 / distance``.
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        Transparency of gadget.
    interpolation : Interpolation, default: "linear"
        Interpolation used when gadget is resized.
    blitter : Blitter, default: "half"
        Determines how graphics are rendered.
    size : Sizelike, default: Size(10, 10)
        Size of gadget.
    pos : Pointlike, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: True
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    caster_map : ULong2D
        A 2-d map. Non-zero values are walls.
    camera_pos : Pointlike
        Position of camera in map.
    camera_size : Sizelike
        Size of camera. Determines how much of the map is visible.
    tile_colors : list[AColor]
        A value ``n`` in the map will be colored ``tile_colors[n]``.
    light_coords : list[tuple[float, float]] | None
        A list of coordinates for all light sources on the map.
    light_colors : list[Color] | None
        A list of colors for all light sources on the map.
    ambient_light : Color
        Color of ambient light.
    restrictiveness : Restrictiveness
        Restrictiveness of casting algorithm.
    radius : int
        Max visible radius from a light source.
    smoothing : float
        Smoothness of shadow edges.
    not_visible_blocks : bool
        Whether all not-visible cells will be treated as opaque.
    light_decay : Callable[[float], float]
        The strength of light as a function of distance from origin.
    texture : RGBA_2D
        uint8 RGBA color array.
    default_color : AColor
        Default texture color.
    alpha : float
        Transparency of gadget.
    interpolation : Interpolation
        Interpolation used when gadget is resized.
    blitter : Blitter
        Determines how graphics are rendered.
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
        y-coordinate of top of gadget.
    y : int
        y-coordinate of top of gadget.
    left : int
        x-coordinate of left side of gadget.
    x : int
        x-coordinate of left side of gadget.
    bottom : int
        y-coordinate of bottom of gadget.
    right : int
        x-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : TotalSizeHint
        Size as a proportion of parent's height and width.
    pos_hint : TotalPosHint
        Position as a proportion of parent's height and width.
    parent: Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        Whether gadget is transparent.
    is_visible : bool
        Whether gadget is visible.
    is_enabled : bool
        Whether gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App | None
        The running app.

    Methods
    -------
    cast_shadows()
        Update texture by shadow casting all light sources.
    to_map_coords(point)
        Convert a point in the gadget's local coordinates to a point in the map's
        coordinates.
    to_png(path)
        Write :attr:`texture` to provided path as a `png` image.
    clear()
        Fill texture with default color.
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(gadget_it, \*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    tween(...)
        Sequentially update gadget properties over time.
    on_size()
        Update gadget after a resize.
    on_transparency()
        Update gadget after transparency is enabled/disabled.
    on_add()
        Update gadget after being added to the gadget tree.
    on_remove()
        Update gadget after being removed from the gadget tree.
    on_key(key_event)
        Handle a key press event.
    on_mouse(mouse_event)
        Handle a mouse event.
    on_paste(paste_event)
        Handle a paste event.
    on_terminal_focus(focus_event)
        Handle a focus event.
    """

    def __init__(
        self,
        *,
        caster_map: ULong2D,
        camera_pos: Pointlike,
        camera_size: Sizelike,
        tile_colors: list[AColor] | None = None,
        light_coords: list[tuple[float, float]] | None = None,
        light_colors: list[Color] | None = None,
        ambient_light: Color = BLACK,
        restrictiveness: Restrictiveness = "permissive",
        radius: int = 20,
        smoothing: float = 1.0 / 3.0,
        not_visible_blocks: bool = True,
        light_decay: Callable[[float], float] = default_light_decay,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        blitter: Blitter = "half",
        interpolation: Interpolation = "linear",
        size: Sizelike = Size(10, 10),
        pos: Pointlike = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            default_color=default_color,
            alpha=alpha,
            interpolation=interpolation,
            blitter=blitter,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self.caster_map = caster_map
        self.camera_pos = camera_pos
        self.camera_size = camera_size
        self.tile_colors = tile_colors or [AGRAY, AWHITE]
        self.light_coords = light_coords or []
        self.light_colors = light_colors or []
        self.ambient_light = ambient_light
        self.restrictiveness = restrictiveness
        self.radius = radius
        self.smoothing = clamp(smoothing, 0.0, 1.0)
        self.not_visible_blocks = not_visible_blocks
        self.light_decay = light_decay

    def on_size(self):
        """Resize ``texture`` and ``_light_intensity`` buffer on size."""
        super().on_size()
        h, w, _ = self.texture.shape
        self._light_intensity = np.empty((h, w, 3), float)

    def cast_shadows(self):
        """Update texture by shadow casting all light sources."""
        self._light_intensity[:] = self.ambient_light
        cast_shadows(
            self.texture,
            self._light_intensity,
            self.caster_map,
            self.camera_pos,
            self.camera_size,
            self.tile_colors,
            self.light_coords,
            self.light_colors,
            self.restrictiveness,
            self.radius,
            self.smoothing,
            self.not_visible_blocks,
            self.light_decay,
        )

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

        cy, cx = self.camera_pos
        ch, cw = self.camera_size

        return ch / h * y + cy, cw / w * x + cx
