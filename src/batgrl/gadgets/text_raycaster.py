"""A raycaster gadget."""

import numpy as np
from numpy.typing import NDArray

from ..text_tools import _Cell, _text_to_cells, _write_lines_to_canvas
from ._raycasting import text_cast_rays
from .text import Cell, Point, PosHint, Size, SizeHint, Text

__all__ = ["TextRaycaster", "Point", "Size"]


class TextRaycaster(Text):
    r"""
    A raycaster gadget that renders with text.

    ``caster_map`` should not contain a value greater than the length of
    ``wall_textures``. A non-zero value ``N`` in ``caster_map`` represents a wall with
    texture ``wall_textures[N - 1]``.

    The integer arrays in ``wall_textures`` determine how walls are shaded. With low
    values darker and high values lighter.

    ``sprite_indexes`` should not contain a value greater than or equal to the length of
    ``sprite_textures``. A value ``N`` in ``sprite_indexes`` represents a sprite with
    texture ``sprite_textures[N]``. ``sprite_coords`` and ``sprite_indexes`` must be the
    same length.

    It's convention in ``batgrl`` to refer to RGBA arrays as textures. ``wall_textures``
    and ``sprite_textures`` do not contain RGBA arrays, but the names are kept to be
    consistent with the graphics raycaster.

    Parameters
    ----------
    caster_map : NDArray[np.uint8]
        The raycaster map.
    wall_textures : List[NDArray[np.uint8]]
        Textures for walls.
    camera_coord : tuple[float, float], default: (0.0, 0.0)
        The camera's position.
    camera_angle : float, default: 0.0
        The camera's angle.
    camera_fov : float, default: 0.66
        The camera's field-of-view. Somewhere between 0-1.
    sprite_coords : NDArray[np.float64] | None, default: None
        Positions of sprites.
    sprite_indexes : NDArray[np.uint8] | None, default: None
        Texture indexes of sprites.
    sprite_textures : list[str] | None, default: None
        Textures for sprites.
    ascii_map : str, default: " .,:;<+*LtCa4U80dQM@"
        Dark to bright ascii characters for shading.
    default_cell : NDArray[Cell] | str, default: " "
        Default cell of text canvas.
    alpha : float, default: 1.0
        Transparency of gadget.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
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
    caster_map : NDArray[np.uint8]
        The raycaster map.
    wall_textures : List[NDArray[np.uint8]]
        Textures for walls.
    camera_coord : tuple[float, float]
        The camera's position.
    camera_angle : float
        The camera's angle.
    camera_fov : float
        The camera's field-of-view. Somewhere between 0-1.
    sprite_coords : NDArray[np.float64]
        Positions of sprites.
    sprite_indexes : NDArray[np.uint8]
        Texture indexes of sprites.
    sprite_textures : list[NDArray[Cell]]
        Textures for sprites.
    ascii_map : str
        Dark to bright ascii characters for shading.
    canvas : NDArray[Cell]
        The array of characters for the gadget.
    default_cell : NDArray[Cell]
        Default cell of text canvas.
    default_fg_color : Color
        Foreground color of default cell.
    default_bg_color : Color
        Background color of default cell.
    alpha : float
        Transparency of gadget.
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
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
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
    app : App
        The running app.

    Methods
    -------
    cast_rays()
        Update canvas by casting all rays.
    add_border(style="light", ...)
        Add a border to the gadget.
    add_syntax_highlighting(lexer, style)
        Add syntax highlighting to current text in canvas.
    add_str(str, pos, ...)
        Add a single line of text to the canvas.
    set_text(text, ...)
        Resize gadget to fit text, erase canvas, then fill canvas with text.
    clear()
        Fill canvas with default cell.
    shift(n=1)
        Shift content in canvas up (or down in case of negative `n`).
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
    add_gadgets(\*gadgets)
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
        caster_map: NDArray[np.uint8],
        wall_textures: list[NDArray[np.uint8]] | None,
        camera_coord: tuple[float, float] = (0.0, 0.0),
        camera_angle: float = 0.0,
        camera_fov: float = 0.66,
        sprite_coords: NDArray[np.float64] | None = None,
        sprite_indexes: NDArray[np.uint8] | None = None,
        sprite_textures: list[str] | None = None,
        ascii_map: str = " .,:;<+*LtCa4U80dQM@",
        default_cell: NDArray[Cell] | str = " ",
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            default_cell=default_cell,
            alpha=alpha,
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

        self.sprite_coords: NDArray[np.float64]
        """Positions of sprites."""
        if sprite_coords is None:
            self.sprite_coords = np.empty((0, 2), np.float64)
        else:
            self.sprite_coords = sprite_coords

        self.sprite_indexes: NDArray[np.uint8]
        """Texture indexes of sprites."""
        if sprite_indexes is None:
            self.sprite_indexes = np.empty(0, np.uint8)
        else:
            self.sprite_indexes = sprite_indexes

        self.sprite_textures: list[NDArray[Cell]] = []
        """Textures for sprites."""
        if sprite_textures is not None:
            for texture in sprite_textures:
                spr_size, lines = _text_to_cells(texture)
                canvas = np.empty(spr_size, Cell)
                _write_lines_to_canvas(
                    lines, canvas, self.default_fg_color, self.default_bg_color
                )
                self.sprite_textures.append(canvas.view(_Cell))

        self.ascii_map = ascii_map
        """Dark to bright ascii characters for shading."""

        self.on_size()

    @property
    def ascii_map(self) -> str:
        """Dark to bright ascii characters for shading."""
        return "".join(chr(i) for i in self._ascii_map)

    @ascii_map.setter
    def ascii_map(self, ascii_map: str):
        self._ascii_map = np.array([ord(char) for char in ascii_map], np.uint32)

    def cast_rays(self):
        """Update canvas by casting all rays."""
        self.clear()
        text_cast_rays(
            self.canvas.view(_Cell),
            self.caster_map,
            self.camera_coord,
            self.camera_angle,
            self.camera_fov,
            self.wall_textures,
            self.sprite_indexes,
            self.sprite_coords,
            self.sprite_textures,
            self._ascii_map,
        )
