"""A raycaster gadget."""

import numpy as np

from ..array_types import RGBA_2D, Coords, ULong1D, ULong2D
from ..colors import ABLACK, TRANSPARENT, AColor
from ._raycasting import cast_rays
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
)

__all__ = ["Point", "Raycaster", "Size"]


class Raycaster(Graphics):
    r"""
    A raycaster gadget.

    ``caster_map`` should not contain a value greater than the length of
    ``wall_textures``. A non-zero value ``N`` in ``caster_map`` represents a wall with
    texture ``wall_textures[N - 1]``.

    ``sprite_indexes`` should not contain a value greater than or equal to the length of
    ``sprite_textures``. A value ``N`` in ``sprite_indexes`` represents a sprite with
    texture ``sprite_textures[N]``. ``sprite_coords`` and ``sprite_indexes`` must be the
    same length.

    Parameters
    ----------
    caster_map : ULong2D
        The raycaster map.
    wall_textures : list[RGBA_2D]
        Textures for walls.
    camera_coord : tuple[float, float], default: (0.0, 0.0)
        The camera's position.
    camera_angle : float, default: 0.0
        The camera's angle.
    camera_fov : float, default: 0.66
        The camera's field-of-view. Somewhere between 0-1.
    sprite_coords : Coords | None, default: None
        Positions of sprites.
    sprite_indexes : ULong1D | None, default: None
        Texture indexes of sprites.
    sprite_textures : list[RGBA_2D] | None, default: None
        Textures for sprites.
    ceiling : RGBA_2D | None, default: None
        Optional ceiling texture.
    ceiling_color : AColor, default: ABLACK
        Color of ceiling if no ceiling texture.
    floor : RGBA_2D | None, default: None
        Optional floor texture.
    floor_color : AColor, default: ABLACK
        Color of floor if no floor texture.
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
        The raycaster map.
    wall_textures : list[RGBA_2D]
        Textures for walls.
    camera_coord : tuple[float, float]
        The camera's position.
    camera_angle : float
        The camera's angle.
    camera_fov : float
        The camera's field-of-view. Somewhere between 0-1.
    sprite_coords : Coords
        Positions of sprites.
    sprite_indexes : ULong1D
        Texture indexes of sprites.
    sprite_textures : list[RGBA_2D]
        Textures for sprites.
    ceiling : RGBA_2D | None
        The ceiling texture.
    ceiling_color : AColor
        Color of ceiling if no ceiling texture.
    floor : RGBA_2D | None
        The floor texture.
    floor_color : AColor
        Color of floor if no floor texture.
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
    cast_rays()
        Update texture by casting all rays.
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
        wall_textures: list[RGBA_2D],
        camera_coord: tuple[float, float] = (0.0, 0.0),
        camera_angle: float = 0.0,
        camera_fov: float = 0.66,
        sprite_coords: Coords | None = None,
        sprite_indexes: ULong1D | None = None,
        sprite_textures: list[RGBA_2D] | None = None,
        ceiling: RGBA_2D | None = None,
        ceiling_color: AColor = ABLACK,
        floor: RGBA_2D | None = None,
        floor_color: AColor = ABLACK,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        blitter: Blitter = "half",
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
        """The raycaster map."""
        self.wall_textures = wall_textures
        """Textures for walls."""
        self.camera_coord = camera_coord
        """The camera's position."""
        self.camera_angle = camera_angle
        """The camera's angle."""
        self.camera_fov = camera_fov
        """The camera's field-of-view. Somewhere between 0-1."""
        self.sprite_coords: Coords
        """Positions of sprites."""
        if sprite_coords is None:
            self.sprite_coords = np.empty((0, 2), np.float64)
        else:
            self.sprite_coords = sprite_coords

        self.sprite_indexes: ULong1D
        """Texture indexes of sprites."""
        if sprite_indexes is None:
            self.sprite_indexes = np.empty(0, np.uint8)
        else:
            self.sprite_indexes = sprite_indexes

        self.sprite_textures = sprite_textures
        """Textures for sprites."""
        self.ceiling = ceiling
        """Optional ceiling texture."""
        self.ceiling_color = ceiling_color
        """Color of ceiling if no ceiling texture."""
        self.floor = floor
        """Optional floor texture."""
        self.floor_color = floor_color
        """Color of floor if no floor texture."""

        self.on_size()

    def cast_rays(self):
        """Update texture by casting all rays."""
        h = self.texture.shape[0]
        self.texture[: h // 2] = self.ceiling_color
        self.texture[h // 2 :] = self.floor_color
        cast_rays(
            self.texture,
            self.caster_map,
            self.camera_coord,
            self.camera_angle,
            self.camera_fov,
            self.wall_textures,
            self.ceiling,
            self.floor,
            self.sprite_indexes,
            self.sprite_coords,
            self.sprite_textures,
        )
