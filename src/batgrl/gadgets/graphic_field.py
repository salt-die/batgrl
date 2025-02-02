"""
A graphic particle field.

A particle field specializes in rendering many single "pixel" children from an array of
particle positions and and an particle colors.
"""

from typing import Any

import numpy as np
from numpy.typing import NDArray

from .._rendering import graphics_field_render
from .gadget import Cell, Gadget, Point, PosHint, Size, SizeHint, bindable, clamp
from .graphics import Blitter, Graphics, scale_geometry

__all__ = ["GraphicParticleField", "Point", "Size"]


class GraphicParticleField(Gadget):
    r"""
    A graphic particle field.

    A particle field specializes in rendering many single "pixel" children from an array
    of particle positions and and an particle colors. Particles positions are a
    ``(N, 2)`` shaped array of floats. The decimal part of the positions allows
    different blitters to place correct "subpixel" characters. For instance a position
    ``(0.0, 0.0)`` might render the character ``"⠁"``, while ``(0.5, 0.0)`` might render
    ``"⠄"``.

    Parameters
    ----------
    particle_positions : NDArray[np.float64] | None, default: None
        An array of particle positions with shape ``(N, 2)``.
    particle_colors : NDArray[np.uint8] | None, default: None
        A RGBA array of particle colors with shape ``(N, 4)``.
    particle_properties : dict[str, Any] | None, default: None
        Additional particle properties.
    alpha : float, default: 1.0
        Transparency of gadget.
    blitter : Blitter, default: "half"
        Determines how graphics are rendered.
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
    nparticles : int
        Number of particles in particle field.
    particle_positions : NDArray[np.float64]
        An array of particle positions with shape `(N, 2)`.
    particle_colors : NDArray[np.uint8]
        A RGBA array of particle colors with shape `(N, 4)`.
    particle_properties : dict[str, Any]
        Additional particle properties.
    alpha : float
        Transparency of gadget.
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
    particles_from_texture(texture)
        Set particle positions and colors from visible pixels of an RGBA texture.
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
        particle_positions: NDArray[np.float64] | None = None,
        particle_colors: NDArray[np.uint8] | None = None,
        particle_properties: dict[str, Any] | None = None,
        alpha: float = 1.0,
        blitter: Blitter = "half",
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.particle_positions: NDArray[np.float64]
        """An array of particle positions with shape `(N, 2)`."""
        if particle_positions is None:
            self.particle_positions = np.zeros((0, 2), dtype=np.float64)
        else:
            self.particle_positions = np.ascontiguousarray(
                particle_positions, dtype=np.float64
            )

        self.particle_colors: NDArray[np.uint8]
        """A RGBA array of particle colors with shape `(N, 4)`."""
        if particle_colors is None:
            self.particle_colors = np.zeros(
                (len(self.particle_positions), 4), dtype=np.uint8
            )
        else:
            self.particle_colors = np.ascontiguousarray(particle_colors, dtype=np.uint8)

        self.particle_properties: dict[str, Any]
        """Additional particle properties."""
        if particle_properties is None:
            self.particle_properties = {}
        else:
            self.particle_properties = particle_properties

        self.alpha = alpha
        """Transparency of gadget."""
        self.blitter = blitter
        """Determines how graphics are rendered."""

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._alpha

    @alpha.setter
    @bindable
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)

    @property
    def blitter(self) -> Blitter:
        """Determines how graphics are rendered."""
        return self._blitter

    @blitter.setter
    def blitter(self, blitter: Blitter):
        if blitter not in Blitter.__args__:
            raise TypeError(f"{blitter} is not a valid blitter type.")
        if blitter == "sixel" and not Graphics._sixel_support:
            self._blitter = "half"
        else:
            self._blitter = blitter

    def on_add(self) -> None:
        """Change sixel blitter if sixel is not supported on add."""
        if self._blitter == "sixel" and not Graphics._sixel_support:
            self.blitter = "half"
        super().on_add()

    @property
    def nparticles(self) -> int:
        """Number of particles in particle field."""
        return len(self.particle_positions)

    def particles_from_texture(self, texture: NDArray[np.uint8]) -> None:
        """
        Set particle positions and colors from visible pixels of an RGBA texture.

        Parameters
        ----------
        texture : NDArray[np.uint8]
            A uint8 RGBA numpy array.
        """
        positions = np.argwhere(texture[..., 3])
        pys, pxs = positions.T
        self.particle_colors = np.ascontiguousarray(texture[pys, pxs])
        self.particle_positions = np.ascontiguousarray(positions.astype(np.float64))
        self.particle_positions /= scale_geometry(self._blitter, Size(1, 1))

    def _render(
        self,
        cells: NDArray[Cell],
        graphics: NDArray[np.uint8],
        kind: NDArray[np.uint8],
    ):
        """Render visible region of gadget."""
        graphics_field_render(
            cells,
            graphics,
            kind,
            self.absolute_pos,
            self._blitter,
            self._is_transparent,
            self.particle_positions,
            self.particle_colors,
            self._alpha,
            self._region,
        )
