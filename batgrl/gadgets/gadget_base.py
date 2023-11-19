"""Base class for all gadgets."""
import asyncio
from collections.abc import Callable, Iterator, Sequence
from dataclasses import asdict, dataclass
from functools import wraps
from numbers import Real
from time import monotonic
from typing import Coroutine, Literal, Optional, TypedDict
from weakref import WeakKeyDictionary

import numpy as np
from numpy.typing import NDArray

from .. import easings
from ..geometry import Point, Region, Size, clamp, lerp
from ..io import KeyEvent, MouseEvent, PasteEvent
from .text_tools import Char, coerce_char, style_char

__all__ = [
    "Anchor",
    "Char",
    "Easing",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "Region",
    "GadgetBase",
    "clamp",
    "coerce_char",
    "lerp",
    "style_char",
    "subscribable",
]


def round_down(n: float) -> int:
    """Like the built-in `round`, but always rounds down."""
    i, r = divmod(n, 1)
    if r <= 0.5:
        return int(i)
    return int(i + 1)


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
"""
Point of gadget attached to a pos hint.
"""


_ANCHOR_TO_POS: dict[Anchor, tuple[float, float]] = {
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


class _Hint:
    """
    Base for size and pos hints. Calls gadget's `apply_hints` when an attribute is
    changed.
    """

    __slots__ = ("_gadget",)

    def __setattr__(self, attr, value):
        super().__setattr__(attr, value)
        if (
            attr != "_gadget"
            and attr in self.__dataclass_fields__
            and getattr(self, "_gadget", None) is not None
        ):
            self._gadget.apply_hints()


@dataclass(slots=True)
class PosHint(_Hint):
    """
    A position hint.

    A pos hint allows a gadget to automatically position itself when added to the
    gadget tree or when its parent resizes. `y_hint` controls vertical position and
    `x_hint` horizontal. `anchor` determines which point of the gadget is attached to
    the pos hint. For instance, in the diagram below, if the `y_hint` and `x_hint` are
    both `0.5` the pos hint will be at point `c` on the parent (50% of the parent's
    height and width). Additionally, if the anchor is `"top"`, the anchor will be at
    point `a` on the gadget::

             parent
        +---------------+
        |               |    +---a---+
        |       c       |    |gadget |
        |               |    +-------+
        +---------------+


    Subsequently, `a` will be aligned with `c`, so that the gadget is positioned as
    below::

             parent
        +---------------+
        |               |
        |   +-------+   |
        |   |gadget |   |
        +---+-------+---+

    The additional parameters `y_offset` and `x_offset` allow one to translate the
    gadget by some integer offsets after the pos hint has been applied.

    Parameters
    ----------
    anchor : Anchor | tuple[float, float], default: "center"
        Determines which point is attached to the pos hint.
    y_hint : float | None, default: None
        Vertical position as a proportion of parent's height.
    x_hint : float | None, default: None
        Horizontal position as a proportion of parent's width.
    y_offset : int, default: 0
        Vertical offset after pos hint is applied.
    x_offset : int, default: 0
        Horizontal offset after pos hint is applied.

    Attributes
    ----------
    anchor : Anchor | tuple[float, float]
        Determines which point is attached to the pos hint.
    y_anchor : float
        Y-coordinate of anchor.
    x_anchor : float
        X-coordinate of anchor.
    y_hint : float | None
        Vertical position as a proportion of parent's height.
    x_hint : float | None
        Horizontal position as a proportion of parent's width.
    y_offset : int
        Vertical offset after pos hint is applied.
    x_offset : int
        Horizontal offset after pos hint is applied.
    """

    anchor: Anchor | tuple[float, float] = "center"
    """Determines which point is attached to the pos hint."""
    y_hint: float | None = None
    """Vertical position as a proportion of parent's height."""
    x_hint: float | None = None
    """Horizontal position as a proportion of parent's width."""
    y_offset: int = 0
    """Vertical offset after y-hint is applied."""
    x_offset: int = 0
    """Horizontal offset after x-hint is applied."""

    @property
    def y_anchor(self) -> float:
        """The y-coordinate of the anchor."""
        if isinstance(self.anchor, str):
            return _ANCHOR_TO_POS[self.anchor][0]

    @y_anchor.setter
    def y_anchor(self, y_anchor: float):
        if isinstance(self.anchor, str):
            x_anchor = _ANCHOR_TO_POS[self.anchor][1]
        self.anchor = y_anchor, x_anchor

    @property
    def x_anchor(self) -> float:
        """The x-coordinate of the anchor."""
        if isinstance(self.anchor, str):
            return _ANCHOR_TO_POS[self.anchor][1]

    @x_anchor.setter
    def x_anchor(self, x_anchor: float):
        if isinstance(self.anchor, str):
            y_anchor = _ANCHOR_TO_POS[self.anchor][0]
        self.anchor = x_anchor, y_anchor


@dataclass(slots=True)
class SizeHint(_Hint):
    """
    A size hint.

    A size hint allows a gadget to automatically size itself when added to the gadget
    tree or when its parent resizes. `height_hint` is the proportion of the parent's
    height the gadget's height will be and `width_hint` the proportion of the parent's
    width. Additional parameters `height_offset` and `width_offset` allow adjusting the
    size by some integer amount after the size hint has been applied. If given,
    `min_height`, `max_height`, `min_width`, max_width` will prevent the gadget from
    sizing too small or too large.

    Parameters
    ----------
    height_hint : float | None, default: None
        Height as a proportion of parent's height.
    width_hint : float | None, default: None
        Width as a proportion of parent's width.
    height_offset : int , default: 0
        Height offset after height-hint is applied.
    width_offset : int, default: 0
        Width offset after width-hint is applied.
    min_height : int | None, default: None
        Minimum allowed height.
    max_height : int | None, default: None
        Maximum allowed height.
    min_width : int | None, default: None
        Minimum allowed width.
    max_width : int | None, default: None
        Maximum allowed width.

    Attributes
    ----------
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    min_height : int | None
        Minimum allowed height.
    max_height : int | None
        Maximum allowed height.
    min_width : int | None
        Minimum allowed width.
    max_width : int | None
        Maximum allowed width.
    """

    height_hint: float | None = None
    width_hint: float | None = None
    height_offset: int = 0
    width_offset: int = 0
    max_height: int | None = None
    min_height: int | None = None
    max_width: int | None = None
    min_width: int | None = None


class PosHintDict(TypedDict, total=False):
    """
    PosHint parameters as a dict.

    Methods
    -------
    clear():
        Remove all items from the dictionary.
    copy():
        Return a shallow copy of the dictionary.
    fromkeys(iterable, value=None):
        Create a new dictionary with keys from iterable and values set to value.
    get(key, default=None):
        Return the value for key if key is in the dictionary, else default. If default
        is not given, it defaults to None, so that this method never raises a KeyError.
    items():
        Return a new view of the dictionary’s items ((key, value) pairs). See the
        documentation of view objects.
    keys():
        Return a new view of the dictionary’s keys. See the documentation of view
        objects.
    pop(...):
        If key is in the dictionary, remove it and return its value, else return
        default. If default is not given and key is not in the dictionary, a KeyError is
        raised.
    popitem():
        Remove and return a (key, value) pair from the dictionary. Pairs are returned in
        LIFO order. popitem() is useful to destructively iterate over a dictionary, as
        often used in set algorithms. If the dictionary is empty, calling popitem()
        raises a KeyError.
    setdefault(key, default=None):
        If key is in the dictionary, return its value. If not, insert key with a value
        of default and return default. default defaults to None.
    update(...):
        Update the dictionary with the key/value pairs from other, overwriting existing
        keys. Return None.
    values():
        Return a new view of the dictionary’s values. See the documentation of view
        objects.
    """

    anchor: Anchor | tuple[float, float]
    y_hint: float | None
    x_hint: float | None
    y_offset: int
    x_offset: int


class SizeHintDict(TypedDict, total=False):
    """
    SizeHint parameters as a dict.

    Methods
    -------
    clear():
        Remove all items from the dictionary.
    copy():
        Return a shallow copy of the dictionary.
    fromkeys(iterable, value=None):
        Create a new dictionary with keys from iterable and values set to value.
    get(key, default=None):
        Return the value for key if key is in the dictionary, else default. If default
        is not given, it defaults to None, so that this method never raises a KeyError.
    items():
        Return a new view of the dictionary’s items ((key, value) pairs). See the
        documentation of view objects.
    keys():
        Return a new view of the dictionary’s keys. See the documentation of view
        objects.
    pop(...):
        If key is in the dictionary, remove it and return its value, else return
        default. If default is not given and key is not in the dictionary, a KeyError is
        raised.
    popitem():
        Remove and return a (key, value) pair from the dictionary. Pairs are returned in
        LIFO order. popitem() is useful to destructively iterate over a dictionary, as
        often used in set algorithms. If the dictionary is empty, calling popitem()
        raises a KeyError.
    setdefault(key, default=None):
        If key is in the dictionary, return its value. If not, insert key with a value
        of default and return default. default defaults to None.
    update(...):
        Update the dictionary with the key/value pairs from other, overwriting existing
        keys. Return None.
    values():
        Return a new view of the dictionary’s values. See the documentation of view
        objects.
    """

    height_hint: float | None
    width_hint: float | None
    height_offset: int
    width_offset: int
    max_height: int | None
    min_height: int | None
    max_width: int | None
    min_width: int | None


Easing = Literal[
    "linear",
    "in_quad",
    "out_quad",
    "in_out_quad",
    "in_cubic",
    "out_cubic",
    "in_out_cubic",
    "in_quart",
    "out_quart",
    "in_out_quart",
    "in_quint",
    "out_quint",
    "in_out_quint",
    "in_sine",
    "out_sine",
    "in_out_sine",
    "in_exp",
    "out_exp",
    "in_out_exp",
    "in_circ",
    "out_circ",
    "in_out_circ",
    "in_elastic",
    "out_elastic",
    "in_out_elastic",
    "in_back",
    "out_back",
    "in_out_back",
    "in_bounce",
    "out_bounce",
    "in_out_bounce",
]
"""Easings for :meth:`batgrl.gadgets.GadgetBase.tween`"""


def subscribable(setter):
    """Decorate property setters to make them subscribable."""
    instances = WeakKeyDictionary()

    @wraps(setter)
    def wrapper(self, *args, **kwargs):
        setter(self, *args, **kwargs)

        if subscribers := instances.get(self):
            for action in subscribers.values():
                action()

    wrapper.instances = instances

    return wrapper


class GadgetBase:
    r"""
    Base class for creating gadgets.

    Parameters
    ----------
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        A transparent gadget allows regions beneath it to be painted.
    is_visible : bool, default: True
        Whether gadget is visible. GadgetBase will still receive input events if not
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
    parent : GadgetBase | None
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
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.parent: GadgetBase | None = None
        self.children: list[GadgetBase] = []

        h, w = size
        self._size = Size(clamp(h, 1, None), clamp(w, 1, None))
        self._pos = Point(*pos)

        if size_hint is None:
            self._size_hint = SizeHint()
        elif isinstance(size_hint, dict):
            self._size_hint = SizeHint(**size_hint)
        else:
            self._size_hint = size_hint
        self._size_hint._gadget = self

        if pos_hint is None:
            self._pos_hint = PosHint()
        elif isinstance(pos_hint, dict):
            self._pos_hint = PosHint(**pos_hint)
        else:
            self._pos_hint = pos_hint
        self._pos_hint._gadget = self

        self.is_transparent = is_transparent
        self.is_visible = is_visible
        self.is_enabled = is_enabled

        self.region: Region = Region()
        """The visible portion of the gadget on the screen."""

    def __repr__(self):
        return f"{type(self).__name__}(size={self.size}, pos={self.pos})"

    @property
    def size(self) -> Size:
        """Size of gadget."""
        return self._size

    @size.setter
    @subscribable
    def size(self, size: Size):
        if size == self._size:
            return

        h, w = size
        size = Size(clamp(int(h), 1, None), clamp(int(w), 1, None))

        if self.root is None:
            self._size = size
            self.on_size()

            for child in self.children:
                child.apply_hints()

            return

        with self.root._render_lock:
            self._size = size
            self.on_size()

            for child in self.children:
                child.apply_hints()

    @property
    def height(self) -> int:
        """Height of gadget."""
        return self._size[0]

    @height.setter
    def height(self, height: int):
        self.size = height, self.width

    rows = height

    @property
    def width(self) -> int:
        """Width of gadget."""
        return self._size[1]

    @width.setter
    def width(self, width: int):
        self.size = self.height, width

    columns = width

    @property
    def pos(self) -> Point:
        """Position relative to parent."""
        return self._pos

    @pos.setter
    @subscribable
    def pos(self, pos: Point):
        y, x = pos
        pos = Point(int(y), int(x))

        if self.root is None:
            self._pos = pos
        else:
            with self.root._render_lock:
                self._pos = pos

    @property
    def top(self) -> int:
        """Y-coordinate of top of gadget."""
        return self._pos[0]

    @top.setter
    def top(self, top: int):
        self.pos = top, self.left

    y = top
    """Y-coordinate of top of gadget."""

    @property
    def left(self) -> int:
        """X-coordinate of left side of gadget."""
        return self._pos[1]

    @left.setter
    def left(self, left: int):
        self.pos = self.top, left

    x = left
    """X-coordinate of left side of gadget."""

    @property
    def bottom(self) -> int:
        """Y-coordinate of bottom of gadget."""
        return self.top + self.height

    @bottom.setter
    def bottom(self, bottom: int):
        self.top = bottom - self.height

    @property
    def right(self) -> int:
        """X-coordinate of right side of gadget."""
        return self.left + self.width

    @right.setter
    def right(self, right: int):
        self.left = right - self.width

    @property
    def center(self) -> Point:
        """Position of center of gadget."""
        y, x = self.pos
        h, w = self.size
        return Point(y + h // 2, x + w // 2)

    @center.setter
    def center(self, center: Point):
        cy, cx = center
        h, w = self.size
        self.pos = Point(cy - h // 2, cx - w // 2)

    @property
    def absolute_pos(self) -> Point:
        """Absolute position on screen."""
        if self.parent is None:
            return self.pos
        y, x = self.parent.absolute_pos
        return Point(self.top + y, self.left + x)

    @property
    def size_hint(self) -> SizeHint:
        """GadgetBase's size as a proportion of its parent's size."""
        return self._size_hint

    @size_hint.setter
    def size_hint(self, size_hint: SizeHint):
        """
        Set gadget's size as a proportion of its parent's size.

        Negative size hints are set to 0.0.
        """
        if isinstance(size_hint, dict):
            size_hint = SizeHint(**size_hint)
        if size_hint.height_hint is not None:
            size_hint.height_hint = float(size_hint.height_hint)
        if size_hint.width_hint is not None:
            size_hint.width_hint = float(size_hint.width_hint)

        size_hint._gadget = self
        self._size_hint._gadget = None
        self._size_hint = size_hint

        self.apply_hints()

    @property
    def pos_hint(self) -> PosHint:
        """GadgetBase's position as a proportion of its parent's size."""
        return self._pos_hint

    @pos_hint.setter
    def pos_hint(self, pos_hint: PosHint):
        if isinstance(pos_hint, dict):
            pos_hint = PosHint(**pos_hint)
        if pos_hint.y_hint is not None:
            pos_hint.y_hint = float(pos_hint.y_hint)
        if pos_hint.x_hint is not None:
            pos_hint.x_hint = float(pos_hint.x_hint)
        pos_hint._gadget = self
        self._pos_hint._gadget = None
        self._pos_hint = pos_hint
        self.apply_hints()

    @property
    def root(self) -> Optional["GadgetBase"]:
        """Return the root gadget if connected to gadget tree."""
        return self.parent and self.parent.root

    @property
    def app(self):
        """The running app."""
        return self.root.app

    def on_size(self):
        """Update gadget after a resize."""

    def apply_hints(self):
        """
        Apply size and pos hints.

        This is called automatically when the gadget is added to the gadget tree and
        when the gadget's parent's size changes.
        """
        if self.parent is None:
            return

        if self._size_hint.height_hint is None:
            height = self.height
        else:
            height = clamp(
                round_down(self.parent.height * self._size_hint.height_hint)
                + self._size_hint.height_offset,
                self._size_hint.min_height,
                self._size_hint.max_height,
            )

        if self._size_hint.width_hint is None:
            width = self.width
        else:
            width = clamp(
                round_down(self.parent.width * self._size_hint.width_hint)
                + self._size_hint.width_offset,
                self._size_hint.min_width,
                self._size_hint.max_width,
            )

        self.size = height, width

        if isinstance(self._pos_hint.anchor, str):
            y_anchor, x_anchor = _ANCHOR_TO_POS[self._pos_hint.anchor]
        else:
            y_anchor, x_anchor = self._pos_hint.anchor

        top, left = self.pos
        if self._pos_hint.y_hint is not None:
            top = (
                round_down(self.parent.height * self._pos_hint.y_hint)
                - round_down(height * y_anchor)
                + self._pos_hint.y_offset
            )

        if self._pos_hint.x_hint is not None:
            left = (
                round_down(self.parent.width * self._pos_hint.x_hint)
                - round_down(width * x_anchor)
                + self._pos_hint.x_offset
            )
        self.pos = top, left

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
            return point

        y, x = self.parent.to_local(point)
        return Point(y - self.top, x - self.left)

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
        if not self.is_visible or not self.is_enabled:
            return False

        return point in self.region or any(
            point in child.region
            for child in self.walk()
            if child.is_visible or child.is_enabled
        )

    def collides_gadget(self, other: "GadgetBase") -> bool:
        """
        Return true if other is within gadget's bounding box.

        Parameters
        ----------
        other : GadgetBase
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

    def add_gadget(self, gadget: "GadgetBase"):
        """
        Add a child gadget.

        Parameters
        ----------
        gadget : GadgetBase
            A gadget to add as a child.
        """
        self.children.append(gadget)
        gadget.parent = self

        if self.root is not None:
            gadget.on_add()

    def add_gadgets(self, *gadgets: "GadgetBase"):
        r"""
        Add multiple child gadgets.

        Parameters
        ----------
        \*gadgets : GadgetBase
            Gadgets to add as children. Can also accept a single iterable of gadgets.
        """
        if len(gadgets) == 1 and not isinstance(gadgets[0], GadgetBase):
            # Assume item is an iterable of gadgets.
            gadgets = gadgets[0]

        for gadget in gadgets:
            self.add_gadget(gadget)

    def remove_gadget(self, gadget: "GadgetBase"):
        """
        Remove a child gadget.

        Parameters
        ----------
        gadget : GadgetBase
            The gadget to remove from children.
        """
        if self.root is not None:
            gadget.on_remove()

        self.children.remove(gadget)
        gadget.parent = None

    def pull_to_front(self):
        """Move gadget to end of gadget stack so that it is drawn last."""
        if self.parent is not None:
            self.parent.children.remove(self)
            self.parent.children.append(self)

    def walk_from_root(self) -> Iterator["GadgetBase"]:
        """
        Yield all descendents of the root gadget (preorder traversal).

        Yields
        ------
        GadgetBase
            A descendent of the root gadget.
        """
        yield from self.root.walk()

    def walk(self) -> Iterator["GadgetBase"]:
        """
        Yield all descendents of this gadget (preorder traversal).

        Yields
        ------
        GadgetBase
            A descendent of this gadget.
        """
        for child in self.children:
            yield child
            yield from child.walk()

    def walk_reverse(self) -> Iterator["GadgetBase"]:
        """
        Yield all descendents of this gadget (reverse postorder traversal).

        Yields
        ------
        GadgetBase
            A descendent of this gadget.
        """
        for child in reversed(self.children):
            yield from child.walk_reverse()
            yield child

    def ancestors(self) -> Iterator["GadgetBase"]:
        """
        Yield all ancestors of this gadget.

        Yields
        ------
        GadgetBase
            An ancestor of this gadget.
        """
        if self.parent:
            yield self.parent
            yield from self.parent.ancestors()

    def subscribe(
        self,
        source: "GadgetBase",
        attr: str,
        action: Callable[[], None],
    ):
        """
        Subscribe to a gadget property. When property is modified, `action` will be
        called.

        Parameters
        ----------
        source : GadgetBase
            The source of the gadget property.
        attr : str
            The name of the gadget property.
        action : Callable[[], None]
            Called when the property is updated.
        """
        setter = getattr(type(source), attr).fset
        subscribers = setter.instances.setdefault(source, WeakKeyDictionary())
        subscribers[self] = action

    def unsubscribe(self, source: "GadgetBase", attr: str) -> Callable[[], None] | None:
        """
        Unsubscribe to a gadget event and return the action that was subscribed to the
        property or ``None`` if subscription isn't found.

        Parameters
        ----------
        source : GadgetBase
            The source of the gadget property.
        attr : str
            The name of the gadget property.

        Returns
        -------
        Callable[[], None] | None
            The action that was subscribed to the property or `None` if no subscription
            was found.
        """
        setter = getattr(type(source), attr).fset
        return setter.instances[source].pop(self, None)

    def dispatch_key(self, key_event: KeyEvent) -> bool | None:
        """
        Dispatch key press until handled.

        A key press is handled if a handler returns ``True``.

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
        Dispatch mouse event until handled.

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
        Dispatch paste event until handled.

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

    def on_key(self, key_event: KeyEvent) -> bool | None:
        """
        Handle key press event. (Handled key presses should return ``True`` else
        ``False`` or ``None``).

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
        Handle mouse event. (Handled mouse events should return ``True`` else ``False``
        or ``None``).

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
        Handle paste event. (Handled paste events should return ``True`` else ``False``
        or ``None``).

        Parameters
        ----------
        paste_event : PasteEvent
            The paste event to handle.

        Returns
        -------
        bool | None
            Whether the paste event was handled.
        """

    def render(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        """Render visible region of gadget into root's `canvas` and `colors` arrays."""

    @staticmethod
    def _tween_lerp(start, end, p):
        """Tween non-real values."""
        if start is None or end is None:
            return end

        if isinstance(start, Real) and isinstance(end, Real):
            value = lerp(start, end, p)
            if isinstance(start, int):
                return round_down(value)
            return value

        if isinstance(start, Sequence):
            return [
                GadgetBase._tween_lerp(start_value, end_value, p)
                for start_value, end_value in zip(start, end)
            ]

        if isinstance(start, dict):
            if isinstance(start.get("anchor"), str):
                start["anchor"] = _ANCHOR_TO_POS[start["anchor"]]
            if isinstance(end.get("anchor"), str):
                end["anchor"] = _ANCHOR_TO_POS[end["anchor"]]

            return {
                key: GadgetBase._tween_lerp(start_value, end.get(key), p)
                for key, start_value in start.items()
            }

    async def tween(
        self,
        *,
        duration: float = 1.0,
        easing: Easing = "linear",
        on_start: Callable[[], None] | None = None,
        on_progress: Callable[[], None] | None = None,
        on_complete: Callable[[], None] | None = None,
        **properties: dict[
            str,
            Real
            | NDArray[np.number]
            | Sequence[Real]
            | PosHint
            | SizeHint
            | PosHintDict
            | SizeHintDict,
        ],
    ) -> Coroutine:
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
        on_progress : Callable[[], None] | None, default: None
            Called when tween updates.
        on_complete : Callable[[], None] | None, default: None
            Called when tween completes.
        **properties : dict[
            str,
            Real
            | NDArray[np.number]
            | Sequence[Real]
            | PosHint
            | SizeHint
            | PosHintDict
            | SizeHintDict,
        ]
            GadgetBase properties' target values. E.g., to smoothly tween a gadget's
            position to (5, 10) over 2.5 seconds, specify the `pos` property as a
            keyword-argument:
            ``await gadget.tween(pos=(5, 10), duration=2.5, easing="out_bounce")``

        Returns
        -------
        Coroutine
            A coroutine updates gadget properties over some time.

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
        end_time = monotonic() + duration
        start_values = tuple(
            asdict(getattr(self, attr))
            if isinstance(getattr(self, attr), (PosHint, SizeHint))
            else getattr(self, attr)
            for attr in properties
        )
        easing_function = getattr(easings, easing)

        if pos_hint := properties.get("pos_hint"):
            if isinstance(pos_hint, dict):
                pos_hint = PosHint(**properties["pos_hint"])
            properties["pos_hint"] = asdict(pos_hint)

        if size_hint := properties.get("size_hint"):
            if isinstance(size_hint, dict):
                size_hint = SizeHint(**properties["size_hint"])
            properties["size_hint"] = asdict(size_hint)

        if on_start:
            on_start()

        while (current_time := monotonic()) < end_time:
            p = easing_function(1 - (end_time - current_time) / duration)

            for start_value, (prop, target) in zip(start_values, properties.items()):
                setattr(self, prop, GadgetBase._tween_lerp(start_value, target, p))

            if on_progress:
                on_progress()

            await asyncio.sleep(0)

        for prop, target in properties.items():
            setattr(self, prop, target)

        if on_complete:
            on_complete()

    def on_add(self):
        """Apply size hints and call children's `on_add`."""
        self.apply_hints()
        for child in self.children:
            child.on_add()

    def on_remove(self):
        """Call children's `on_remove`."""
        for child in self.children:
            child.on_remove()

    def prolicide(self):
        """Recursively remove all children."""
        for child in self.children.copy():
            child.destroy()

    def destroy(self):
        """Remove this gadget and recursively remove all its children."""
        self.prolicide()
        if self.parent:
            self.parent.remove_gadget(self)
