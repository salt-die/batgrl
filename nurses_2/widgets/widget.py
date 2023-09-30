"""
Base class for all widgets.
"""
import asyncio
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from functools import wraps
from numbers import Real
from time import monotonic
from typing import Literal, Optional, TypedDict
from weakref import WeakKeyDictionary

import numpy as np
from numpy.typing import NDArray
from wcwidth import wcwidth

from .. import easings
from ..colors import ColorPair
from ..geometry import Point, Rect, Size, clamp, intersection, lerp
from ..io import KeyEvent, MouseEvent, PasteEvent

__all__ = [
    "Anchor",
    "Char",
    "Easing",
    "Point",
    "PosHint",
    "PosHintDict",
    "Rect",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "Widget",
    "clamp",
    "intersection",
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
Point of widget attached to a pos hint.
"""


@np.vectorize
def char_widths(char: np.dtype("<U1")) -> int:
    """Return the width of a character."""
    return 0 if char == "" else wcwidth(char)


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
    Base for size and pos hints. Calls widget's `apply_hints` when an attribute is
    changed.
    """

    __slots__ = ("_widget",)

    def __setattr__(self, attr, value):
        super().__setattr__(attr, value)
        if (
            attr != "_widget"
            and attr in self.__dataclass_fields__
            and getattr(self, "_widget", None) is not None
        ):
            self._widget.apply_hints()


@dataclass(slots=True)
class PosHint(_Hint):
    """
    A position hint.

    A pos hint allows a widget to automatically position itself when added to the
    widget tree or when its parent resizes. `y_hint` controls vertical position and
    `x_hint` horizontal. `anchor` determines which point of the widget is attached to
    the pos hint. For instance, in the diagram below, if the `y_hint` and `x_hint` are
    both `0.5` the pos hint will be at point `c` on the parent (50% of the parent's
    height and width). Additionally, if the anchor is `"top"`, the anchor will be at
    point `a` on the widget::

             parent
        +---------------+
        |               |    +---a---+
        |       c       |    |widget |
        |               |    +-------+
        +---------------+


    Subsequently, `a` will be aligned with `c`, so that the widget is positioned as
    below::

             parent
        +---------------+
        |               |
        |   +-------+   |
        |   |widget |   |
        +---+-------+---+

    The additional parameters `y_offset` and `x_offset` allow one to translate the
    widget by some integer offsets after the pos hint has been applied.

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
        """
        The y-coordinate of the anchor.
        """
        if isinstance(self.anchor, str):
            return _ANCHOR_TO_POS[self.anchor][0]

    @y_anchor.setter
    def y_anchor(self, y_anchor: float):
        if isinstance(self.anchor, str):
            x_anchor = _ANCHOR_TO_POS[self.anchor][1]
        self.anchor = y_anchor, x_anchor

    @property
    def x_anchor(self) -> float:
        """
        The x-coordinate of the anchor.
        """
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

    A size hint allows a widget to automatically size itself when added to the widget
    tree or when its parent resizes. `height_hint` is the proportion of the parent's
    height the widget's height will be and `width_hint` the proportion of the parent's
    width. Additional parameters `height_offset` and `width_offset` allow adjusting the
    size by some integer amount after the size hint has been applied. If given,
    `min_height`, `max_height`, `min_width`, max_width` will prevent the widget from
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
    """PosHint parameters as a dict."""

    anchor: Anchor | tuple[float, float]
    y_hint: float | None
    x_hint: float | None
    y_offset: int
    x_offset: int


class SizeHintDict(TypedDict, total=False):
    """SizeHint parameters as a dict."""

    height_hint: float | None
    width_hint: float | None
    height_offset: int
    width_offset: int
    max_height: int | None
    min_height: int | None
    max_width: int | None
    min_width: int | None


Char = np.dtype(
    [
        ("char", "U1"),
        ("bold", "?"),
        ("italic", "?"),
        ("underline", "?"),
        ("strikethrough", "?"),
        ("overline", "?"),
    ]
)
"""Data type of canvas arrays."""


def style_char(
    char: str,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    strikethrough: bool = False,
    overline: bool = False,
) -> NDArray[Char]:
    """
    Return a zero-dimensional `Char` array.

    The primary use for this function is to paint a styled character into a `Char`
    array. For instance, `my_widget.canvas[:] = style_char("a", bold=True)` would
    fill `my_widget`'s canvas with bold `a`s. Alternatively, one can avoid this function
    by setting only the `"char"` field of a `Char` array, e.g.,
    `my_widget.canvas["char"][:] = "a"`, but the boolean styling fields won't be
    changed. Avoid setting `Char` arrays with strings; `my_widget.canvas[:] = "a"` is
    incorrect,`"a"` will be coerced into true for all the boolean styling fields, so
    that `my_widget` is filled with bold, italic, underline, strikethrough, and overline
    `a`s.

    Parameters
    ----------
    char : str
        A single unicode character.
    bold : bool, default: False
        Whether char is bold.
    italic : bool, default: False
        Whether char is italic.
    underline : bool, default: False
        Whether char is underlined.
    strikethrough : bool, default: False
        Whether char is strikethrough.
    overline : bool, default: False
        Whether char is overlined.

    Returns
    -------
    NDArray[Char]
        A zero-dimensional `Char` array with the styled character.
    """
    return np.array(
        (char, bold, italic, underline, strikethrough, overline), dtype=Char
    )


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
"""Easings for :meth:`nurses_2.widgets.Widget.tween`"""


def subscribable(setter):
    """
    A decorator for property setters that makes the properties subscribable.
    """
    instances = WeakKeyDictionary()

    @wraps(setter)
    def wrapper(self, *args, **kwargs):
        setter(self, *args, **kwargs)

        if subscribers := instances.get(self):
            for action in subscribers.values():
                action()

    wrapper.instances = instances

    return wrapper


class Widget:
    """
    Base class for creating widgets.

    Parameters
    ----------
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether widget is visible. Widget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether widget is enabled. A disabled widget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the widget if the widget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if the widget is not transparent.

    Attributes
    ----------
    size : Size
        Size of widget.
    height : int
        Height of widget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of widget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of widget.
    y : int
        Y-coordinate of top of widget.
    left : int
        X-coordinate of left side of widget.
    x : int
        X-coordinate of left side of widget.
    bottom : int
        Y-coordinate of bottom of widget.
    right : int
        X-coordinate of right side of widget.
    center : Point
        Position of center of widget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the widget if the widget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Widget | None
        Parent widget.
    children : list[Widget]
        Children widgets.
    is_transparent : bool
        True if widget is transparent.
    is_visible : bool
        True if widget is visible.
    is_enabled : bool
        True if widget is enabled.
    root : Widget | None
        If widget is in widget tree, return the root widget.
    app : App
        The running app.

    Methods
    -------
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of widget.
    collides_widget:
        True if other is within widget's bounding box.
    add_widget:
        Add a child widget.
    add_widgets:
        Add multiple child widgets.
    remove_widget:
        Remove a child widget.
    pull_to_front:
        Move to end of widget stack so widget is drawn last.
    walk_from_root:
        Yield all descendents of root widget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a widget property.
    unsubscribe:
        Unsubscribe to a widget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    on_add:
        Called after a widget is added to widget tree.
    on_remove:
        Called before widget is removed from widget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this widget and all descendents.
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
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        self.parent: Widget | None = None
        self.children: list[Widget] = []

        h, w = size
        self._size = Size(clamp(h, 1, None), clamp(w, 1, None))
        self._pos = Point(*pos)

        if size_hint is None:
            self._size_hint = SizeHint()
        elif isinstance(size_hint, dict):
            self._size_hint = SizeHint(**size_hint)
        else:
            self._size_hint = size_hint
        self._size_hint._widget = self

        if pos_hint is None:
            self._pos_hint = PosHint()
        elif isinstance(pos_hint, dict):
            self._pos_hint = PosHint(**pos_hint)
        else:
            self._pos_hint = pos_hint
        self._pos_hint._widget = self

        self.background_color_pair = background_color_pair
        self.background_char = background_char

        self.is_transparent = is_transparent
        self.is_visible = is_visible
        self.is_enabled = is_enabled

    def __repr__(self):
        return (
            f"{type(self).__name__}(size={self.size}, pos={self.pos}, size_hint="
            f"{self.size_hint}, pos_hint={self.pos_hint}, is_transparent="
            f"{self.is_transparent}, is_visible={self.is_visible}, is_enabled="
            f"{self.is_enabled}, background_char={self.background_char}, "
            f"background_color_pair={self.background_color_pair})"
        )

    @property
    def size(self) -> Size:
        """
        Size of widget.
        """
        return self._size

    @size.setter
    @subscribable
    def size(self, size: Size):
        if size == self._size:
            return

        h, w = size
        self._size = Size(clamp(h, 1, None), clamp(w, 1, None))

        self.on_size()

        for child in self.children:
            child.apply_hints()

    @property
    def height(self) -> int:
        """
        Height of widget.
        """
        return self._size[0]

    @height.setter
    def height(self, height: int):
        self.size = height, self.width

    rows = height

    @property
    def width(self) -> int:
        """
        Width of widget.
        """
        return self._size[1]

    @width.setter
    def width(self, width: int):
        self.size = self.height, width

    columns = width

    @property
    def pos(self) -> Point:
        """
        Position relative to parent.
        """
        return self._pos

    @pos.setter
    @subscribable
    def pos(self, point: Point):
        self._pos = Point(*point)

    @property
    def top(self) -> int:
        """Y-coordinate of top of widget."""
        return self._pos[0]

    @top.setter
    def top(self, top: int):
        self.pos = top, self.left

    y = top
    """Y-coordinate of top of widget."""

    @property
    def left(self) -> int:
        """X-coordinate of left side of widget."""
        return self._pos[1]

    @left.setter
    def left(self, left: int):
        self.pos = self.top, left

    x = left
    """X-coordinate of left side of widget."""

    @property
    def bottom(self) -> int:
        """
        Y-coordinate of bottom of widget.
        """
        return self.top + self.height

    @bottom.setter
    def bottom(self, bottom: int):
        self.top = bottom - self.height

    @property
    def right(self) -> int:
        """
        X-coordinate of right side of widget.
        """
        return self.left + self.width

    @right.setter
    def right(self, right: int):
        self.left = right - self.width

    @property
    def center(self) -> Point:
        """
        Position of center of widget.
        """
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
        """
        Absolute position on screen.
        """
        y, x = self.parent.absolute_pos
        return Point(self.top + y, self.left + x)

    @property
    def size_hint(self) -> SizeHint:
        """
        Widget's size as a proportion of its parent's size.
        """
        return self._size_hint

    @size_hint.setter
    def size_hint(self, size_hint: SizeHint):
        """
        Set widget's size as a proportion of its parent's size.

        Negative size hints are set to 0.0.
        """
        if isinstance(size_hint, dict):
            size_hint = SizeHint(**size_hint)
        if size_hint.height_hint is not None:
            size_hint.height_hint = float(size_hint.height_hint)
        if size_hint.width_hint is not None:
            size_hint.width_hint = float(size_hint.width_hint)

        size_hint._widget = self
        self._size_hint._widget = None
        self._size_hint = size_hint

        self.apply_hints()

    @property
    def pos_hint(self) -> PosHint:
        """
        Widget's position as a proportion of its parent's size.
        """
        return self._pos_hint

    @pos_hint.setter
    def pos_hint(self, pos_hint: PosHint):
        if isinstance(pos_hint, dict):
            pos_hint = PosHint(**pos_hint)
        if pos_hint.y_hint is not None:
            pos_hint.y_hint = float(pos_hint.y_hint)
        if pos_hint.x_hint is not None:
            pos_hint.x_hint = float(pos_hint.x_hint)
        pos_hint._widget = self
        self._pos_hint._widget = None
        self._pos_hint = pos_hint
        self.apply_hints()

    @property
    def background_char(self) -> str | None:
        """
        The background character of the widget if the widget is not transparent.
        """
        return self._background_char

    @background_char.setter
    def background_char(self, background_char: str | None):
        if isinstance(background_char, str) and wcwidth(background_char[0]) == 1:
            self._background_char = background_char[0]
        else:
            self._background_char = None

    @property
    def root(self) -> Optional["Widget"]:
        """
        Return the root widget if connected to widget tree.
        """
        return self.parent and self.parent.root

    @property
    def app(self):
        """
        The running app.
        """
        return self.root.app

    def on_size(self):
        """
        Called when widget is resized.
        """

    def apply_hints(self):
        """
        Apply size and pos hints.

        This is called automatically when the widget is added to the widget tree and
        when the widget's parent's size changes.
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

        if self._pos_hint.y_hint is not None:
            self.top = (
                round_down(self.parent.height * self._pos_hint.y_hint)
                - round_down(height * y_anchor)
                + self._pos_hint.y_offset
            )

        if self._pos_hint.x_hint is not None:
            self.left = (
                round_down(self.parent.width * self._pos_hint.x_hint)
                - round_down(width * x_anchor)
                + self._pos_hint.x_offset
            )

    def to_local(self, point: Point) -> Point:
        """
        Convert point in absolute coordinates to local coordinates.
        """
        if self.parent is None:
            return point

        y, x = self.parent.to_local(point)
        return Point(y - self.top, x - self.left)

    def collides_point(self, point: Point) -> bool:
        """
        True if point collides with an uncovered portion of widget.
        """
        if self.parent is None:
            y, x = point
            return 0 <= y < self.height and 0 <= x < self.width

        if not self.parent.collides_point(point):
            return False

        y, x = self.parent.to_local(point)
        for sibling in reversed(self.parent.children):
            if sibling is not self:
                if (
                    sibling.is_enabled
                    and sibling.top <= y < sibling.bottom
                    and sibling.left <= x < sibling.right
                ):
                    # Point collides with a sibling that is above it.
                    return False
            else:
                return self.top <= y < self.bottom and self.left <= x < self.right

    def collides_widget(self, other: "Widget") -> bool:
        """
        True if some part of `other` is within bounding box.
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

    def add_widget(self, widget: "Widget"):
        """
        Add a child widget.
        """
        self.children.append(widget)
        widget.parent = self

        if self.root:
            widget.on_add()

    def add_widgets(self, *widgets: "Widget"):
        """
        Add multiple child widgets.
        """
        if len(widgets) == 1 and not isinstance(widgets[0], Widget):
            # Assume item is an iterable of widgets.
            widgets = widgets[0]

        for widget in widgets:
            self.add_widget(widget)

    def remove_widget(self, widget: "Widget"):
        """
        Remove a child widget.
        """
        if self.root:
            widget.on_remove()

        self.children.remove(widget)
        widget.parent = None

    def pull_to_front(self):
        """
        Move widget to end of widget stack so that it is drawn last.
        """
        if self.parent is not None:
            self.parent.children.remove(self)
            self.parent.children.append(self)

    def walk_from_root(self):
        """
        Yield all descendents of the root widget.
        """
        for child in self.root.children:
            yield child
            yield from child.walk()

    def walk(self, reverse: bool = False):
        """
        Yield all descendents (or ancestors if `reverse` is true).
        """
        if reverse:
            if self.parent:
                yield self.parent
                yield from self.parent.walk(reverse=True)
        else:
            for child in self.children:
                yield child
                yield from child.walk()

    def subscribe(
        self,
        source: "Widget",
        attr: str,
        action: Callable[[], None],
    ):
        """
        Subscribe to a widget property. When property is modified, `action` will be
        called.

        Parameters
        ----------
        source : Widget
            The source of the widget property.
        attr : str
            The name of the widget property.
        action : Callable[[], None]
            Called when the property is updated.
        """
        setter = getattr(type(source), attr).fset
        subscribers = setter.instances.setdefault(source, WeakKeyDictionary())
        subscribers[self] = action

    def unsubscribe(self, source: "Widget", attr: str) -> Callable[[], None] | None:
        """
        Unsubscribe to a widget event and return the callable that was subscribed
        to the event or ``None`` if subscription isn't found.
        """
        setter = getattr(type(source), attr).fset
        return setter.instances[source].pop(self, None)

    def dispatch_key(self, key_event: KeyEvent) -> bool | None:
        """
        Dispatch key press until handled. (A key press is handled if a handler returns
        ``True``.)
        """
        return any(
            widget.dispatch_key(key_event)
            for widget in reversed(self.children)
            if widget.is_enabled
        ) or self.on_key(key_event)

    def dispatch_mouse(self, mouse_event: MouseEvent) -> bool | None:
        """
        Dispatch mouse event until handled. (A mouse event is handled if a handler
        returns ``True``.)
        """
        return any(
            widget.dispatch_mouse(mouse_event)
            for widget in reversed(self.children)
            if widget.is_enabled
        ) or self.on_mouse(mouse_event)

    def dispatch_paste(self, paste_event: PasteEvent) -> bool | None:
        """
        Dispatch paste event until handled. (A paste event is handled if a handler
        returns ``True``.)
        """
        return any(
            widget.dispatch_paste(paste_event)
            for widget in reversed(self.children)
            if widget.is_enabled
        ) or self.on_paste(paste_event)

    def on_key(self, key_event: KeyEvent) -> bool | None:
        """
        Handle key press event. (Handled key presses should return ``True`` else
        ``False`` or ``None``).
        """

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        """
        Handle mouse event. (Handled mouse events should return ``True`` else ``False``
        or ``None``).
        """

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        """
        Handle paste event. (Handled paste events should return ``True`` else ``False``
        or ``None``).
        """

    def render(
        self,
        canvas_view: NDArray[Char],
        colors_view: NDArray[np.uint8],
        source: tuple[slice, slice],
    ):
        """
        Paint region given by `source` into `canvas_view` and `colors_view`.
        """
        if not self.is_transparent:
            if self.background_char is not None:
                canvas_view[:] = style_char(self.background_char)

            if self.background_color_pair is not None:
                colors_view[:] = self.background_color_pair

        self.render_children(source, canvas_view, colors_view)

    def render_children(
        self,
        destination: tuple[slice, slice],
        canvas_view: NDArray[Char],
        colors_view: NDArray[np.uint8],
    ):
        vert_slice, hori_slice = destination
        dest = Rect(
            vert_slice.start, vert_slice.stop, hori_slice.start, hori_slice.stop
        )

        for child in self.children:
            if child.is_visible and child.is_enabled:
                source = Rect(child.top, child.bottom, child.left, child.right)
                if (slices := intersection(dest, source)) is not None:
                    dest_slice, source_slice = slices
                    child.render(
                        canvas_view[dest_slice], colors_view[dest_slice], source_slice
                    )

    @staticmethod
    def _tween_lerp(start, end, p):
        """
        Helper function to tween non-Real values.
        """
        if start is None or end is None:
            return end

        if isinstance(start, Real) and isinstance(end, Real):
            value = lerp(start, end, p)
            if isinstance(start, int):
                return round_down(value)
            return value

        if isinstance(start, Sequence):
            return [
                Widget._tween_lerp(start_value, end_value, p)
                for start_value, end_value in zip(start, end)
            ]

        if isinstance(start, dict):
            if isinstance(start.get("anchor"), str):
                start["anchor"] = _ANCHOR_TO_POS[start["anchor"]]
            if isinstance(end.get("anchor"), str):
                end["anchor"] = _ANCHOR_TO_POS[end["anchor"]]

            return {
                key: Widget._tween_lerp(start_value, end.get(key), p)
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
    ):
        """
        Coroutine that sequentially updates widget properties over a duration (in
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
            Widget properties' target values. E.g., to smoothly tween a widget's
            position to (5, 10) over 2.5 seconds, specify the `pos` property as a
            keyword-argument:
            ``await widget.tween(pos=(5, 10), duration=2.5, easing="out_bounce")``

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
                setattr(self, prop, Widget._tween_lerp(start_value, target, p))

            if on_progress:
                on_progress()

            await asyncio.sleep(0)

        for prop, target in properties.items():
            setattr(self, prop, target)

        if on_complete:
            on_complete()

    def on_add(self):
        """
        Called after a widget is added to widget tree.
        """
        self.apply_hints()
        for child in self.children:
            child.on_add()

    def on_remove(self):
        """
        Called before widget is removed from widget tree.
        """
        for child in self.children:
            child.on_remove()

    def prolicide(self):
        """
        Recursively remove all children.
        """
        for child in self.children.copy():
            child.destroy()

    def destroy(self):
        """
        Destroy this widget and all descendents.
        """
        self.prolicide()
        if self.parent:
            self.parent.remove_widget(self)
