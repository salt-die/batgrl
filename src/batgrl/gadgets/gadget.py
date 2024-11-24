"""Base class for all gadgets."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator, MutableSequence, Sequence
from functools import wraps
from itertools import count
from numbers import Real
from time import perf_counter
from types import MappingProxyType
from typing import Final, Literal, Self, TypedDict
from weakref import WeakKeyDictionary

import numpy as np
from numpy.typing import NDArray

from ..geometry import EASINGS, Easing, Point, Region, Size, clamp, lerp, round_down
from ..terminal.events import FocusEvent, KeyEvent, MouseEvent, PasteEvent
from ..text_tools import Cell, new_cell

__all__ = [
    "Anchor",
    "Cell",
    "Easing",
    "Point",
    "PosHint",
    "Region",
    "Size",
    "SizeHint",
    "Gadget",
    "bindable",
    "new_cell",
    "clamp",
    "lerp",
]

_UID: Final = count(1)
_ANCHOR_TO_POS: Final = {
    "top-left": (0.0, 0.0),
    "top": (0.0, 0.5),
    "top-right": (0.0, 1.0),
    "left": (0.5, 0.0),
    "center": (0.5, 0.5),
    "right": (0.5, 1.0),
    "bottom-left": (1.0, 0.0),
    "bottom": (1.0, 0.5),
    "bottom-right": (1.0, 1.0),
}
_DEFAULT_POS_HINT: Final = {
    "anchor": "center",
    "y_hint": None,
    "x_hint": None,
    "x_offset": 0,
    "y_offset": 0,
}
"""The default pos hint."""
_DEFAULT_SIZE_HINT: Final = {
    "height_hint": None,
    "width_hint": None,
    "height_offset": 0,
    "width_offset": 0,
    "max_height": None,
    "min_height": None,
    "max_width": None,
    "min_width": None,
}
"""The default size hint."""

Anchor = Literal[
    "top-left",
    "top",
    "top-right",
    "left",
    "center",
    "right",
    "bottom-left",
    "bottom",
    "bottom-right",
]
"""Point of gadget attached to a pos hint."""


class _GadgetList(MutableSequence):
    """
    A sequence of gadget's.

    Gadget regions are invalidated if their index in the sequence changes.
    """

    def __init__(self) -> None:
        self._gadgets: list[Gadget] = []

    def __len__(self) -> int:
        return len(self._gadgets)

    def __getitem__(self, index: int) -> Gadget:
        return self._gadgets[index]

    def __setitem__(self, index: int, gadget: Gadget) -> None:
        self._gadgets[index] = gadget
        gadget._invalidate_region()

    def _invalidate_regions_after_index(self, index: int) -> None:
        for i in range(index, len(self)):
            self[i]._invalidate_region()

    def __delitem__(self, index: int) -> None:
        del self._gadgets[index]
        self._invalidate_regions_after_index(index)

    def insert(self, index: int, gadget: Gadget) -> None:
        self._gadgets.insert(index, gadget)
        self._invalidate_regions_after_index(index)

    def __iter__(self) -> Iterator[Gadget]:
        return iter(self._gadgets)

    def copy(self) -> list[Gadget]:
        """
        Return a copy of the internal list of gadgets.

        Note this doesn't return a ``_GadgetList``.
        """
        return self._gadgets.copy()


class PosHint(TypedDict, total=False):
    """
    A position hint.

    A pos hint allows a gadget to automatically position itself when added to the
    gadget tree or when its parent resizes. ``y_hint`` controls vertical position and
    ``x_hint`` horizontal. ``anchor`` determines which point of the gadget is attached
    to the pos hint. For instance, in the diagram below, if the ``y_hint`` and
    ``x_hint`` are both ``0.5`` the pos hint will be at point ``c`` on the parent
    (50% of the parent's height and width). Additionally, if the anchor is ``"top"``,
    the anchor will be at point ``a`` on the gadget::

             parent
        +---------------+
        |               |    +---a---+
        |       c       |    |gadget |
        |               |    +-------+
        +---------------+


    Subsequently, ``a`` will be aligned with ``c``, so that the gadget is positioned as
    below::

             parent
        +---------------+
        |               |
        |   +-------+   |
        |   |gadget |   |
        +---+-------+---+

    The additional parameters ``y_offset`` and ``x_offset`` allow one to translate the
    gadget by some integer offsets after the pos hint has been applied.

    Attributes
    ----------
    anchor : Anchor | tuple[float, float]
        Determines which point is attached to the pos hint.
    y_hint : float | None
        Vertical position as a proportion of parent's height.
    x_hint : float | None
        Horizontal position as a proportion of parent's width.
    y_offset : int
        Vertical offset after pos hint is applied.
    x_offset : int
        Horizontal offset after pos hint is applied.
    """

    anchor: Anchor | tuple[float, float]
    """Determines which point is attached to the pos hint."""
    y_hint: float | None
    """Vertical position as a proportion of parent's height."""
    x_hint: float | None
    """Horizontal position as a proportion of parent's width."""
    y_offset: int
    """Vertical offset after pos hint is applied."""
    x_offset: int
    """Horizontal offset after pos hint is applied."""


class SizeHint(TypedDict, total=False):
    """
    A size hint.

    A size hint allows a gadget to automatically size itself when added to the gadget
    tree or when its parent resizes. ``height_hint`` is the proportion of the parent's
    height the gadget's height will be and ``width_hint`` the proportion of the parent's
    width. Additional parameters ``height_offset`` and ``width_offset`` allow adjusting
    the size by some integer amount after the size hint has been applied. If given,
    ``min_height``, ``max_height``, ``min_width``, and ``max_width`` will prevent the
    gadget from sizing too small or too large.

    Attributes
    ----------
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    height_offset : int
        Height offset after height-hint is applied.
    width_offset : int
        Width offset after width-hint is applied.
    max_height : int | None
        Maximum allowed height.
    min_height : int | None
        Minimum allowed height.
    max_width : int | None
        Maximum allowed width.
    min_width : int | None
        Minimum allowed width.
    """

    height_hint: float | None
    """Height as a proportion of parent's height."""
    width_hint: float | None
    """Width as a proportion of parent's width."""
    height_offset: int
    """Height offset after height-hint is applied."""
    width_offset: int
    """Width offset after width-hint is applied."""
    max_height: int | None
    """Maximum allowed height."""
    min_height: int | None
    """Minimum allowed height."""
    max_width: int | None
    """Maximum allowed width."""
    min_width: int | None
    """Minimum allowed width."""


def _normalize_pos_hint(pos_hint: PosHint) -> PosHint:
    normal_hint = _DEFAULT_POS_HINT | pos_hint
    if normal_hint["y_hint"] is not None:
        normal_hint["y_hint"] = float(normal_hint["y_hint"])
    if normal_hint["x_hint"] is not None:
        normal_hint["x_hint"] = float(normal_hint["x_hint"])
    if isinstance(normal_hint["anchor"], str):
        normal_hint["anchor"] = _ANCHOR_TO_POS[normal_hint["anchor"]]
    return normal_hint


def _normalize_size_hint(size_hint: SizeHint) -> SizeHint:
    normal_hint = _DEFAULT_SIZE_HINT | size_hint
    if normal_hint["height_hint"] is not None:
        normal_hint["height_hint"] = float(normal_hint["height_hint"])
    if normal_hint["width_hint"] is not None:
        normal_hint["width_hint"] = float(normal_hint["width_hint"])
    return normal_hint


def bindable(setter):
    """Decorate property setters to make them bindable."""
    instances: WeakKeyDictionary[Gadget, Callable[[], None]] = WeakKeyDictionary()

    @wraps(setter)
    def wrapper(self, *args, **kwargs):
        setter(self, *args, **kwargs)
        if bindings := instances.get(self):
            for callback in bindings.values():
                callback()

    wrapper.instances = instances

    return wrapper


class Gadget:
    r"""
    Base class for creating gadgets.

    Parameters
    ----------
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
    parent : Gadget | None
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
        Update gadget after transparency enabled/disabled.
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

    __bindings: dict[int, str] = {}
    """UID to property name mapping."""

    def __init__(
        self,
        *,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.parent: Gadget | None = None
        """The gadget's parent."""
        self.children: _GadgetList = _GadgetList()
        """The gadget's children."""

        h, w = size
        self._size = Size(clamp(h, 0, None), clamp(w, 0, None))
        """Size of gadget."""
        self._pos = Point(*pos)
        """Position relative to parent."""
        self._size_hint: SizeHint = _normalize_size_hint(size_hint or {})
        """Gadget's size as a proportion of its parent's size."""
        self._pos_hint: PosHint = _normalize_pos_hint(pos_hint or {})
        """Gadget's position as a proportion of its parent's size."""
        self._is_transparent = is_transparent
        """Whether gadget is transparent."""
        self._is_visible = is_visible
        """Whether gadget is visible."""
        self._is_enabled = is_enabled
        """Whether gadget is enabled."""
        self._region_valid: bool = False
        """Whether current region is valid."""
        self._clipping_region: Region = Region()
        """Initial region clipped by ancestor regions."""
        self._root_region_before: Region = Region()
        """The root's region before gadget's region is removed from it."""
        self._region: Region = Region()
        """The visible portion of the gadget on the screen."""

    def __repr__(self):
        return (
            f"{type(self).__name__}(size={self.size}, pos={self.pos}, "
            f"size_hint={self._size_hint}, pos_hint={self._pos_hint}, "
            f"is_transparent={self.is_transparent}, is_visible={self.is_visible}, "
            f"is_enabled={self.is_enabled})"
        )

    @property
    def size(self) -> Size:
        """Size of gadget."""
        return self._size

    @size.setter
    @bindable
    def size(self, size: Size):
        if size == self._size:
            self._apply_pos_hints()
            return

        h, w = size
        size = Size(clamp(int(h), 0, None), clamp(int(w), 0, None))
        if self.root is None:
            self._size = size
        else:
            with self.root._render_lock:
                self._size = size
                self._invalidate_region()

        self._apply_pos_hints()
        for child in self.children:
            child.apply_hints()
        self.on_size()

    @property
    def height(self) -> int:
        """Height of gadget."""
        return self._size[0]

    @height.setter
    def height(self, height: int):
        self.size = height, self.width

    rows = height
    """Alias for :attr:`height`."""

    @property
    def width(self) -> int:
        """Width of gadget."""
        return self._size[1]

    @width.setter
    def width(self, width: int):
        self.size = self.height, width

    columns = width
    """Alias for :attr:`width`."""

    @property
    def pos(self) -> Point:
        """Position relative to parent."""
        return self._pos

    @pos.setter
    @bindable
    def pos(self, pos: Point):
        y, x = pos
        pos = Point(int(y), int(x))

        if self.root is None:
            self._pos = pos
        else:
            with self.root._render_lock:
                self._pos = pos
                self._invalidate_region()

    @property
    def top(self) -> int:
        """y-coordinate of top of gadget."""
        return self._pos[0]

    @top.setter
    def top(self, top: int):
        self.pos = top, self.left

    y = top
    """y-coordinate of top of gadget."""

    @property
    def left(self) -> int:
        """x-coordinate of left side of gadget."""
        return self._pos[1]

    @left.setter
    def left(self, left: int):
        self.pos = self.top, left

    x = left
    """x-coordinate of left side of gadget."""

    @property
    def bottom(self) -> int:
        """y-coordinate of bottom of gadget."""
        return self.top + self.height

    @bottom.setter
    def bottom(self, bottom: int):
        self.top = bottom - self.height

    @property
    def right(self) -> int:
        """x-coordinate of right side of gadget."""
        return self.left + self.width

    @right.setter
    def right(self, right: int):
        self.left = right - self.width

    @property
    def center(self) -> Point:
        """Position of center of gadget."""
        return self.pos + self.size.center

    @center.setter
    def center(self, center: Point):
        cy, cx = center
        h, w = self.size
        self.pos = Point(cy - h // 2, cx - w // 2)

    @property
    def absolute_pos(self) -> Point | None:
        """Absolute position on screen."""
        if self.parent is None:
            return None
        return self.pos + self.parent.absolute_pos

    @property
    def size_hint(self) -> SizeHint:
        """Gadget's size as a proportion of its parent's size."""
        return MappingProxyType(self._size_hint)

    @size_hint.setter
    def size_hint(self, size_hint: SizeHint):
        self._size_hint = _normalize_size_hint(size_hint)
        self.apply_hints()

    @property
    def pos_hint(self) -> PosHint:
        """Gadget's position as a proportion of its parent's size."""
        return MappingProxyType(self._pos_hint)

    @pos_hint.setter
    def pos_hint(self, pos_hint: PosHint):
        self._pos_hint = _normalize_pos_hint(pos_hint)
        self.apply_hints()

    @property
    def is_transparent(self) -> bool:
        """Whether gadget is transparent."""
        return self._is_transparent

    @is_transparent.setter
    @bindable
    def is_transparent(self, is_transparent: bool):
        if is_transparent != self._is_transparent:
            self._is_transparent = is_transparent
            if self.root is not None:
                self._invalidate_region()
            self.on_transparency()

    @property
    def is_visible(self) -> bool:
        """
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
        """
        return self._is_visible

    @is_visible.setter
    @bindable
    def is_visible(self, is_visible: bool):
        if is_visible != self._is_visible:
            self._is_visible = is_visible
            if self.root is not None:
                self._invalidate_region()

    @property
    def is_enabled(self) -> bool:
        """
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.
        """
        return self._is_enabled

    @is_enabled.setter
    @bindable
    def is_enabled(self, is_enabled: bool):
        if is_enabled != self._is_enabled:
            self._is_enabled = is_enabled
            if self.root is not None:
                self._invalidate_region()

    @property
    def root(self) -> Self | None:
        """Return the root gadget if connected to gadget tree."""
        return self.parent and self.parent.root

    @property
    def app(self):
        """The running app."""
        return self.root.app

    def _render(self, canvas: NDArray[Cell]) -> None:
        """Render visible region of gadget."""

    def dispatch_key(self, key_event: KeyEvent) -> bool | None:
        """
        Dispatch a key press event until handled.

        A key press event is handled if a handler returns ``True``.

        Parameters
        ----------
        key_event : KeyEvent
            The key event to dispatch.

        Returns
        -------
        bool | None
            Whether the dispatch was handled.
        """
        return any(
            gadget.dispatch_key(key_event)
            for gadget in reversed(self.children)
            if gadget.is_enabled
        ) or self.on_key(key_event)

    def dispatch_mouse(self, mouse_event: MouseEvent) -> bool | None:
        """
        Dispatch a mouse event until handled.

        A mouse event is handled if a handler returns ``True``.

        Parameters
        ----------
        mouse_event : MouseEvent
            The mouse event to dispatch.

        Returns
        -------
        bool | None
            Whether the dispatch was handled.
        """
        return any(
            gadget.dispatch_mouse(mouse_event)
            for gadget in reversed(self.children)
            if gadget.is_enabled
        ) or self.on_mouse(mouse_event)

    def dispatch_paste(self, paste_event: PasteEvent) -> bool | None:
        """
        Dispatch a paste event until handled.

        A paste event is handled if a handler returns ``True``.

        Parameters
        ----------
        paste_event : PasteEvent
            The paste event to dispatch.

        Returns
        -------
        bool | None
            Whether the dispatch was handled.
        """
        return any(
            gadget.dispatch_paste(paste_event)
            for gadget in reversed(self.children)
            if gadget.is_enabled
        ) or self.on_paste(paste_event)

    def dispatch_terminal_focus(self, focus_event: FocusEvent) -> bool | None:
        """
        Dispatch a focus event until handled.

        A focus event is handled if a handler returns ``True``.

        Parameters
        ----------
        focus_event : FocusEvent
            The focus event to dispatch.

        Returns
        -------
        bool | None
            Whether the dispatch was handled.
        """
        return any(
            gadget.dispatch_terminal_focus(focus_event)
            for gadget in reversed(self.children)
            if gadget.is_enabled
        ) or self.on_terminal_focus(focus_event)

    def _invalidate_region(self, notify_root: bool = True) -> None:
        """Invalidate region and all children's regions."""
        self._region_valid = False
        if notify_root and self.root is not None:
            self.root._all_regions_valid = False
        for child in self.children:
            child._invalidate_region(False)

    def apply_hints(self) -> None:
        """
        Apply size and pos hints.

        This is called automatically when the gadget is added to the gadget tree and
        when the gadget's parent's size changes.
        """
        if self.parent is None:
            return

        parent_height, parent_width = self.parent.size
        height, width = self.size
        if self._size_hint["height_hint"] is not None:
            height = clamp(
                round_down(parent_height * self._size_hint["height_hint"])
                + self._size_hint["height_offset"],
                self._size_hint["min_height"],
                self._size_hint["max_height"],
            )

        if self._size_hint["width_hint"] is not None:
            width = clamp(
                round_down(parent_width * self._size_hint["width_hint"])
                + self._size_hint["width_offset"],
                self._size_hint["min_width"],
                self._size_hint["max_width"],
            )

        self.size = height, width  # `size` setter will call `_apply_pos_hints()`.

    def _apply_pos_hints(self) -> None:
        if self.parent is None:
            return

        parent_height, parent_width = self.parent.size
        height, width = self.size
        y, x = self.pos
        y_anchor, x_anchor = self._pos_hint["anchor"]

        if self._pos_hint["y_hint"] is not None:
            y = (
                round_down(parent_height * self._pos_hint["y_hint"])
                - round_down(height * y_anchor)
                + self._pos_hint["y_offset"]
            )

        if self._pos_hint["x_hint"] is not None:
            x = (
                round_down(parent_width * self._pos_hint["x_hint"])
                - round_down(width * x_anchor)
                + self._pos_hint["x_offset"]
            )
        self.pos = y, x

    def to_local(self, point: Point) -> Point:
        """
        Convert point in absolute coordinates to local coordinates.

        Parameters
        ----------
        point : Point
            Point in absolute (screen) coordinates.

        Returns
        -------
        Point
            The point in local coordinates.
        """
        if self.parent is None:
            return point - self.pos
        return self.parent.to_local(point) - self.pos

    def collides_point(self, point: Point) -> bool:
        """
        Return true if point collides with visible portion of gadget.

        Parameters
        ----------
        point : Point
            A point.

        Returns
        -------
        bool
            Whether point collides with gadget.
        """
        if self.root is None or not self.is_visible or not self.is_enabled:
            return False

        return point in self._region or any(
            point in child._region
            for child in self.walk()
            if child.is_visible or child.is_enabled
        )

    def collides_gadget(self, other: Self) -> bool:
        """
        Return true if other is within gadget's bounding box.

        Parameters
        ----------
        other : Gadget
            Another gadget.

        Returns
        -------
        bool
            Whether other collides with gadget.
        """
        self_top, self_left = self.absolute_pos
        self_bottom = self_top + self.height
        self_right = self.left + self.width

        other_top, other_left = other.absolute_pos
        other_bottom = other_top + other.height
        other_right = other_left + other.width

        return not (
            self_top >= other_bottom
            or other_top >= self_bottom
            or self_left >= other_right
            or other_left >= self_right
        )

    def pull_to_front(self) -> None:
        """Move gadget to end of gadget stack so that it is drawn last."""
        if self.parent is not None:
            self.parent.children.remove(self)
            self.parent.children.append(self)

    def walk(self) -> Iterator[Self]:
        """
        Yield all descendents of this gadget (preorder traversal).

        Yields
        ------
        Gadget
            A descendent of this gadget.
        """
        for child in self.children:
            yield child
            yield from child.walk()

    def walk_reverse(self) -> Iterator[Self]:
        """
        Yield all descendents of this gadget (reverse postorder traversal).

        Yields
        ------
        Gadget
            A descendent of this gadget.
        """
        for child in reversed(self.children):
            yield from child.walk_reverse()
            yield child

    def ancestors(self) -> Iterator[Self]:
        """
        Yield all ancestors of this gadget.

        Yields
        ------
        Gadget
            An ancestor of this gadget.
        """
        if self.parent:
            yield self.parent
            yield from self.parent.ancestors()

    def add_gadget(self, gadget: Self) -> None:
        """
        Add a child gadget.

        Parameters
        ----------
        gadget : Gadget
            A gadget to add as a child.
        """
        self.children.append(gadget)
        gadget.parent = self

        if self.root is not None:
            gadget.on_add()

    def add_gadgets(self, *gadgets: Self) -> None:
        r"""
        Add multiple child gadgets.

        Parameters
        ----------
        \*gadgets : Gadget
            Gadgets to add as children. Can also accept a single iterable of gadgets.
        """
        if len(gadgets) == 1 and not isinstance(gadgets[0], Gadget):
            # Assume item is an iterable of gadgets.
            gadgets = gadgets[0]

        for gadget in gadgets:
            self.add_gadget(gadget)

    def remove_gadget(self, gadget: Self) -> None:
        """
        Remove a child gadget.

        Parameters
        ----------
        gadget : Gadget
            The gadget to remove from children.
        """
        if self.root is not None:
            gadget.on_remove()

        self.children.remove(gadget)
        gadget.parent = None

    def prolicide(self) -> None:
        """Recursively remove all children."""
        for child in self.children.copy():
            child.destroy()

    def destroy(self) -> None:
        """Remove this gadget and recursively remove all its children."""
        self.prolicide()
        if self.parent:
            self.parent.remove_gadget(self)

    def bind(self, prop: str, callback: Callable[[], None]) -> int:
        """
        Bind `callback` to a gadget property. When the property is updated, `callback`
        is called with no arguments.

        Parameters
        ----------
        prop : str
            The name of the gadget property.
        callback : Callable[[], None]
            Callback to bind to property.

        Returns
        -------
        int
            A unique id used to unbind the callback.
        """
        uid = next(_UID)
        setter = getattr(type(self), prop).fset
        bindings = setter.instances.setdefault(self, {})
        bindings[uid] = callback
        self.__bindings[uid] = prop
        return uid

    def unbind(self, uid: int) -> None:
        """
        Unbind a callback from a gadget property.

        Parameters
        ----------
        uid : int
            Unique id returned by the :meth:`bind` method.
        """
        prop = self.__bindings.pop(uid, None)
        if prop is None:
            return
        setter = getattr(type(self), prop).fset
        if self in setter.instances:
            setter.instances[self].pop(uid, None)

    @staticmethod
    def _tween_lerp(start, end, p) -> Real | Sequence[Real] | PosHint | SizeHint | None:
        """Lerp for none, sequences, and hints."""
        if start is None or end is None:
            return None

        if isinstance(start, Real) and isinstance(end, Real):
            value = lerp(start, end, p)
            if isinstance(start, int):
                return round_down(value)
            return value

        if isinstance(start, Sequence):
            return [
                Gadget._tween_lerp(start_value, end_value, p)
                for start_value, end_value in zip(start, end)
            ]

        if isinstance(start, MappingProxyType):
            return {
                key: Gadget._tween_lerp(start_value, end.get(key), p)
                for key, start_value in start.items()
            }

    async def tween(
        self,
        *,
        duration: float = 1.0,
        easing: Easing = "linear",
        on_start: Callable[[], None] | None = None,
        on_progress: Callable[[float], None] | None = None,
        on_complete: Callable[[], None] | None = None,
        **properties: Real | NDArray[np.number] | Sequence[Real] | PosHint | SizeHint,
    ) -> None:
        """
        Coroutine that sequentially updates gadget properties over a duration (in
        seconds).

        Parameters
        ----------
        duration : float, default: 1.0
            The duration of the tween in seconds.
        easing : Easing, default: "linear"
            The easing used for tweening.
        on_start : Callable[[], None] | None, default: None
            Called when tween starts.
        on_progress : Callable[[float], None] | None, default: None
            Called as tween updates with current progress.
        on_complete : Callable[[], None] | None, default: None
            Called when tween completes.
        **properties : Real | NDArray[np.number] | Sequence[Real] | PosHint | SizeHint
            Gadget properties' target values. E.g., to smoothly tween a gadget's
            position to (5, 10) over 2.5 seconds, specify the `pos` property as a
            keyword-argument:
            ``await gadget.tween(pos=(5, 10), duration=2.5, easing="out_bounce")``

        Notes
        -----
        Tweened values will be coerced to match the type of the initial value of their
        corresponding property.

        Non-numeric values will be set immediately.

        Warnings
        --------
        Running several tweens on the same properties concurrently will probably result
        in unexpected behavior.
        """
        end_time = perf_counter() + duration
        easing_function = EASINGS[easing]
        start_values = tuple(getattr(self, attr) for attr in properties)

        if pos_hint := properties.get("pos_hint"):
            properties["pos_hint"] = _normalize_pos_hint(pos_hint)
        if size_hint := properties.get("size_hint"):
            properties["size_hint"] = _normalize_size_hint(size_hint)
        if on_start is not None:
            on_start()

        while (current_time := perf_counter()) < end_time:
            p = easing_function(1 - (end_time - current_time) / duration)

            for start_value, (prop, target) in zip(start_values, properties.items()):
                setattr(self, prop, Gadget._tween_lerp(start_value, target, p))

            if on_progress is not None:
                on_progress(p)

            await asyncio.sleep(0)

        for prop, target in properties.items():
            setattr(self, prop, target)

        if on_complete is not None:
            on_complete()

    def on_size(self) -> None:
        """Update gadget after a resize."""

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""

    def on_add(self) -> None:
        """Update gadget after being added to the gadget tree."""
        self.apply_hints()
        for child in self.children:
            child.on_add()

    def on_remove(self) -> None:
        """Update gadget after being removed from the gadget tree."""
        for child in self.children:
            child.on_remove()

    def on_key(self, key_event: KeyEvent) -> bool | None:
        """
        Handle a key press event.

        Handled key presses should return ``True``.

        Parameters
        ----------
        key_event : KeyEvent
            The key event to handle.

        Returns
        -------
        bool | None
            Whether the key event was handled.
        """

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        """
        Handle a mouse event.

        Handled mouse events should return ``True``.

        Parameters
        ----------
        mouse_event : MouseEvent
            The mouse event to handle.

        Returns
        -------
        bool | None
            Whether the mouse event was handled.
        """

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        """
        Handle a paste event.

        Handled paste events should return ``True``.

        Parameters
        ----------
        paste_event : PasteEvent
            The paste event to handle.

        Returns
        -------
        bool | None
            Whether the paste event was handled.
        """

    def on_terminal_focus(self, focus_event: FocusEvent) -> bool | None:
        """
        Handle a focus event.

        Handled focus events should return ``True``.

        Parameters
        ----------
        focus_event : FocusEvent
            The focus event to handle.

        Returns
        -------
        bool | None
            Whether the focus event was handled.
        """
