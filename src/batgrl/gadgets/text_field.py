"""
A text particle field.

A particle field specializes in rendering many single "pixel" children from an array of
particle positions and an array of particle cells.
"""

from typing import Any

import numpy as np
from numpy.typing import NDArray

from .._rendering import text_field_render
from ..geometry import clamp
from ..text_tools import _Cell
from .gadget import Cell, Gadget, Point, PosHint, Size, SizeHint, new_cell

__all__ = ["TextParticleField", "Point", "Size"]


class TextParticleField(Gadget):
    r"""
    A text particle field.

    A particle field specializes in rendering many single "pixel" children from an array
    of particle positions and an array of particle cells.

    Parameters
    ----------
    particle_positions : NDArray[np.float64] | None, default: None
        An array of particle positions with shape `(N, 2)`.
    particle_cells : NDArray[Cell] | None, default: None
        An array of Cells of particles with shape `(N,)`.
    particle_properties : dict[str, Any] | None, default: None
        Additional particle properties.
    alpha : float, default: 0.0
        Transparency of particles.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
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
    particle_cells : NDArray[Cell]
        An array of Cells of particles with shape `(N,)`.
    particle_properties : dict[str, Any]
        Additional particle properties.
    alpha : float
        Transparency of particles.
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
    particles_from_cells(cells)
        Set particle positions and cells from non-whitespace characters of a Cell array.
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
        particle_cells: NDArray[Cell] | None = None,
        particle_properties: dict[str, Any] = None,
        alpha: float = 0.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
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

        self.particle_cells: NDArray[Cell]
        """An array of Cells of particles with shape `(N,)`"""
        if particle_cells is None:
            self.particle_cells = np.full(len(self.particle_positions), new_cell())
        else:
            self.particle_cells = np.ascontiguousarray(particle_cells, dtype=Cell)

        self.particle_properties: dict[str, Any]
        """Additional particle properties."""
        if particle_properties is None:
            self.particle_properties = {}
        else:
            self.particle_properties = particle_properties

        self.alpha = alpha
        """Transparency of gadget."""

    @property
    def alpha(self) -> float:
        """Transparency of particles."""
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._alpha = clamp(alpha, 0.0, 1.0)

    @property
    def nparticles(self) -> int:
        """Number of particles in particle field."""
        return len(self.particle_positions)

    def particles_from_cells(self, cells: NDArray[Cell]) -> None:
        """
        Set particle positions and cells from non-whitespace characters of a Cell array.

        Parameters
        ----------
        cells : NDArray[Cell]
            A Cell numpy array (such as a :class:`Text` gadget's canvas).
        """
        positions = np.argwhere(np.isin(cells["char"], (" ", "⠀"), invert=True))
        pys, pxs = positions.T
        self.particle_positions = np.ascontiguousarray(positions.astype(np.float64))
        self.particle_cells = np.ascontiguousarray(cells[pys, pxs])

    def _render(
        self,
        cells: NDArray[Cell],
        graphics: NDArray[np.uint8],
        kind: NDArray[np.uint8],
    ):
        """Render visible region of gadget."""
        text_field_render(
            cells,
            graphics,
            kind,
            self.absolute_pos,
            self._is_transparent,
            self.particle_positions,
            self.particle_cells.view(_Cell),
            self._alpha,
            self._region,
        )
