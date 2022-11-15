"""
Base class for all widgets.
"""
import asyncio
from collections.abc import Callable, Sequence
from functools import wraps
from time import monotonic
from typing import Optional
from weakref import WeakKeyDictionary

from .. import easings
from ..clamp import clamp
from ..colors import ColorPair
from ..data_structures import *
from ..io import KeyEvent, MouseEvent, PasteEvent
from .widget_data_structures import *

__all__ = (
    "emitter",
    "Anchor",
    "ColorPair",
    "Easing",
    "Point",
    "PosHint",
    "Size",
    "SizeHint",
    "Widget",
)

def emitter(setter):
    """
    A decorator for widget property setters that will
    notify subscribers when the property is updated.
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

def intersection(a: Rect, b: Rect):
    """
    Find the intersection of two rects and return the numpy slices that
    correspond to that intersection for both rects.
    """
    btop, bbottom, bleft, bright = b
    bheight, bwidth = bbottom - btop, bright - bleft

    atop, abottom, aleft, aright = a
    atop -= btop
    abottom -= btop
    aleft -= bleft
    aright -= bleft

    if (
        atop >= bheight
        or abottom < 0
        or aleft >= bwidth
        or aright < 0
    ):  # Empty intersection.
        return

    if atop < 0:
        at = -atop
        bt = 0
    else:
        at = 0
        bt = atop

    if abottom >= bheight:
        ab = bheight - atop
        bb = bheight
    else:
        ab = abottom - atop
        bb = abottom

    if aleft < 0:
        al = -aleft
        bl = 0
    else:
        al = 0
        bl = aleft

    if aright >= bwidth:
        ar = bwidth - aleft
        br = bwidth
    else:
        ar = aright - aleft
        br = aright

    return (slice(at, ab), slice(al, ar)), (slice(bt, bb), slice(bl, br))


class Widget:
    """
    Base class for creating widgets.

    Parameters
    ----------
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint, default: SizeHint(None, None)
        Proportion of parent's height and width. Non-None values will have
        precedent over :attr:`size`.
    min_height : int | None, default: None
        Minimum height set due to size_hint. Ignored if corresponding size
        hint is None.
    max_height : int | None, default: None
        Maximum height set due to size_hint. Ignored if corresponding size
        hint is None.
    min_width : int | None, default: None
        Minimum width set due to size_hint. Ignored if corresponding size
        hint is None.
    max_width : int | None, default: None
        Maximum width set due to size_hint. Ignored if corresponding size
        hint is None.
    pos_hint : PosHint, default: PosHint(None, None)
        Position as a proportion of parent's height and width. Non-None values
        will have precedent over :attr:`pos`.
    anchor : Anchor, default: Anchor.TOP_LEFT
        The point of the widget attached to :attr:`pos_hint`.
    is_transparent : bool, default: False
        If true, background_char and background_color_pair won't be painted.
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    background_char : str | None, default: None
        The background character of the widget if not `None` and if the widget
        is not transparent.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if not `None` and if the
        widget is not transparent.

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
        Position relative to parent.
    top : int
        Y-coordinate of position.
    y : int
        Y-coordinate of position.
    left : int
        X-coordinate of position.
    x : int
        X-coordinate of position.
    bottom : int
        :attr:`top` + :attr:`height`.
    right : int
        :attr:`left` + :attr:`width`.
    absolute_pos : Point
        Absolute position on screen.
    center : Point
        Center of widget in local coordinates.
    size_hint : SizeHint
        Size as a proportion of parent's size.
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    min_height : int
        Minimum height allowed when using :attr:`size_hint`.
    max_height : int
        Maximum height allowed when using :attr:`size_hint`.
    min_width : int
        Minimum width allowed when using :attr:`size_hint`.
    max_width : int
        Maximum width allowed when using :attr:`size_hint`.
    pos_hint : PosHint
        Position as a proportion of parent's size.
    y_hint : float | None
        Vertical position as a proportion of parent's size.
    x_hint : float | None
        Horizontal position as a proportion of parent's size.
    anchor : Anchor
        Determines which point is attached to :attr:`pos_hint`.
    background_char : str | None
        Background character.
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
    update_geometry:
        Called when parent is resized. Applies size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point is within widget's bounding box.
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
        Yield all descendents (or ancestors if `reverse` is True).
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
        size_hint: SizeHint=SizeHint(None, None),
        min_width: int | None=None,
        max_width: int | None=None,
        min_height: int | None=None,
        max_height: int | None=None,
        pos_hint: PosHint=PosHint(None, None),
        anchor=Anchor.TOP_LEFT,
        is_transparent: bool=False,
        is_visible: bool=True,
        is_enabled: bool=True,
        background_char: str | None=None,
        background_color_pair: ColorPair | None=None,
    ):
        self.parent: Widget | None = None
        self.children: list[Widget] = [ ]

        h, w = size
        self._size = Size(clamp(h, 1, None), clamp(w, 1, None))
        self._pos = Point(*pos)

        self._size_hint = size_hint
        self._min_height = min_height
        self._max_height = max_height
        self._min_width = min_width
        self._max_width = max_width

        self._pos_hint = pos_hint
        self._anchor = anchor

        self.background_color_pair = background_color_pair
        self.background_char = background_char

        self.is_transparent = is_transparent
        self.is_visible = is_visible
        self.is_enabled = is_enabled

    @property
    def size(self) -> Size:
        """
        Size of widget.
        """
        return self._size

    @size.setter
    @emitter
    def size(self, size: Size):
        h, w = size
        self._size = Size(clamp(h, 1, None), clamp(w, 1, None))

        self.on_size()

        for child in self.children:
            child.update_geometry()

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
    @emitter
    def pos(self, point: Point):
        self._pos = Point(*point)

    @property
    def top(self) -> int:
        return self._pos[0]

    @top.setter
    def top(self, top: int):
        self.pos = top, self.left

    y = top

    @property
    def left(self) -> int:
        return self._pos[1]

    @left.setter
    def left(self, left: int):
        self.pos = self.top, left

    x = left

    @property
    def bottom(self) -> int:
        """
        Bottom of widget in parent's reference frame.
        """
        return self.top + self.height

    @bottom.setter
    def bottom(self, value: int):
        self.top = value - self.height

    @property
    def right(self) -> int:
        """
        Right side of widget in parent's reference frame.
        """
        return self.left + self.width

    @right.setter
    def right(self, value: int):
        self.left = value - self.width

    @property
    def absolute_pos(self) -> Point:
        """
        Absolute position on screen.
        """
        y, x = self.parent.absolute_pos
        return Point(self.top + y, self.left + x)

    @property
    def center(self) -> Point:
        """
        The center of the widget in local coordinates.
        """
        return Point(self.height // 2, self.width // 2)

    @property
    def size_hint(self) -> SizeHint:
        """
        Widget's size as a proportion of its parent's size.
        """
        return self._size_hint

    @size_hint.setter
    @emitter
    def size_hint(self, size_hint: SizeHint):
        """
        Set widget's size as a proportion of its parent's size.
        Negative size hints will be clamped to 0.
        """
        h, w = size_hint

        self._size_hint = SizeHint(
            h if h is None else max(float(h), 0.0),
            w if w is None else max(float(w), 0.0),
        )

        if self.parent:
            self.update_geometry()

    @property
    def height_hint(self) -> float | None:
        """
        Widget's height as proportion of its parent's height.
        """
        return self._size_hint[0]

    @height_hint.setter
    def height_hint(self, height_hint: float | None):
        self.size_hint = height_hint, self.width_hint

    @property
    def width_hint(self) -> float | None:
        """
        Widget's width as proportion of its parent's width.
        """
        return self._size_hint[1]

    @width_hint.setter
    def width_hint(self, width_hint: float | None):
        self.size_hint = self.height_hint, width_hint

    @property
    def min_height(self) -> int | None:
        """
        The minimum height of widget set due to :attr:`size_hint`.
        """
        return self._min_height

    @min_height.setter
    @emitter
    def min_height(self, min_height: int | None):
        self._min_height = min_height
        if self.parent:
            self.update_geometry()

    @property
    def max_height(self) -> int | None:
        """
        The maximum height of widget set due to :attr:`size_hint`.
        """
        return self._max_height

    @max_height.setter
    @emitter
    def max_height(self, max_height: int | None):
        self._max_height = max_height
        if self.parent:
            self.update_geometry()

    @property
    def min_width(self) -> int | None:
        """
        The minimum width of widget set due to :attr:`size_hint`.
        """
        return self._min_width

    @min_width.setter
    @emitter
    def min_width(self, min_width: int | None):
        self._min_width = min_width
        if self.parent:
            self.update_geometry()

    @property
    def max_width(self) -> int | None:
        """
        The maximum width of widget set due to :attr:`size_hint`.
        """
        return self._max_width

    @max_width.setter
    @emitter
    def max_width(self, max_width: int | None):
        self._max_width = max_width
        if self.parent:
            self.update_geometry()

    @property
    def pos_hint(self) -> PosHint:
        """
        Widget's position as a proportion of its parent's size.
        """
        return self._pos_hint

    @pos_hint.setter
    @emitter
    def pos_hint(self, pos_hint: PosHint):
        h, w = pos_hint
        self._pos_hint = PosHint(
            h if h is None else float(h),
            w if w is None else float(w),
        )

        if self.parent:
            self.update_geometry()

    @property
    def y_hint(self) -> float | None:
        """
        Vertical position of widget as a proportion of its parent's height.
        """
        return self._pos_hint[0]

    @y_hint.setter
    def y_hint(self, y_hint: float | None):
        self.pos_hint = y_hint, self.x_hint

    @property
    def x_hint(self) -> float | None:
        """
        Horizontal position of widget as proportion of its parent's width.
        """
        return self._pos_hint[1]

    @x_hint.setter
    def x_hint(self, x_hint: float | None):
        self.pos_hint = self.y_hint, x_hint

    @property
    def anchor(self) -> Anchor:
        return self._anchor

    @anchor.setter
    @emitter
    def anchor(self, anchor: Anchor):
        self._anchor = Anchor(anchor)
        self.update_geometry()

    @property
    def background_char(self) -> str | None:
        return self._background_char

    @background_char.setter
    @emitter
    def background_char(self, background_char: str | None):
        match background_char:
            case None:
                self._background_char = background_char
            case str():
                self._background_char = background_char[:1] or None
            case _:
                raise ValueError("invalid background character")

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

    def update_geometry(self):
        """
        Update geometry due to a change in parent's size.
        """
        if self.parent is None:
            return

        h, w = self.parent.size

        h_hint, w_hint = self.size_hint
        if h_hint is not None or w_hint is not None:
            if h_hint is None:
                height = self.height
            else:
                height = clamp(round(h_hint * h), self.min_height, self.max_height)

            if w_hint is None:
                width = self.width
            else:
                width = clamp(round(w_hint * w), self.min_width, self.max_width)

            if self.size != (height, width):  # Avoid unnecessary `on_size` calls.
                self.size = height, width

        y_hint, x_hint = self.pos_hint
        if y_hint is None and x_hint is None:
            return

        match self.anchor:
            case Anchor.TOP_LEFT:
                offset_top, offset_left = 0, 0
            case Anchor.TOP_RIGHT:
                offset_top, offset_left = 0, self.width
            case Anchor.BOTTOM_LEFT:
                offset_top, offset_left = self.height, 0
            case Anchor.BOTTOM_RIGHT:
                offset_top, offset_left = self.height, self.width
            case Anchor.CENTER:
                offset_top, offset_left = self.center
            case Anchor.TOP_CENTER:
                offset_top, offset_left = 0, self.center.x
            case Anchor.BOTTOM_CENTER:
                offset_top, offset_left = self.height, self.center.x
            case Anchor.LEFT_CENTER:
                offset_top, offset_left = self.center.y, 0
            case Anchor.RIGHT_CENTER:
                offset_top, offset_left = self.center.y, self.width

        if y_hint is not None:
            self.top = int(h * y_hint) - offset_top

        if x_hint is not None:
            self.left = int(w * x_hint) - offset_left

    def to_local(self, point: Point) -> Point:
        """
        Convert point in absolute coordinates to local coordinates.
        """
        y, x = self.parent.to_local(point)
        return Point(y - self.top, x - self.left)

    def collides_point(self, point: Point) -> bool:
        """
        Return True if point is within widget's bounding box.
        """
        # These conditions are separated as they both require
        # recursive calls up the widget tree and we'd like to
        # escape as early as possible.
        if not self.parent.collides_point(point):
            return False

        y, x = self.to_local(point)
        return 0 <= y < self.height and 0 <= x < self.width

    def collides_widget(self, other: "Widget") -> bool:
        """
        Return True if some part of `other` is within bounding box.
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

    def walk(self, reverse: bool=False):
        """
        Yield all descendents (or ancestors if `reverse` is True).
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
        Subscribe to a widget property. When property is modified, `action` will be called.

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
        to the event or `None` if subscription isn't found.
        """
        setter = getattr(type(source), attr).fset
        return setter.instances[source].pop(self, None)

    def dispatch_key(self, key_event: KeyEvent) -> bool | None:
        """
        Dispatch key press until handled. (A key press is handled if a handler returns True.)
        """
        return (
            any(
                widget.dispatch_key(key_event)
                for widget in reversed(self.children)
                if widget.is_enabled
            )
            or self.on_key(key_event)
        )

    def dispatch_mouse(self, mouse_event: MouseEvent) -> bool | None:
        """
        Dispatch mouse event until handled. (A mouse event is handled if a handler returns True.)
        """
        return (
            any(
                widget.dispatch_mouse(mouse_event)
                for widget in reversed(self.children)
                if widget.is_enabled
            )
            or self.on_mouse(mouse_event)
        )

    def dispatch_paste(self, paste_event: PasteEvent) -> bool | None:
        """
        Dispatch paste event until handled. (A paste event is handled if a handler returns True.)
        """
        return (
            any(
                widget.dispatch_paste(paste_event)
                for widget in reversed(self.children)
                if widget.is_enabled
            )
            or self.on_paste(paste_event)
        )

    def on_key(self, key_event: KeyEvent) -> bool | None:
        """
        Handle key press event. (Handled key presses should return True else False or None).
        """

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        """
        Handle mouse event. (Handled mouse events should return True else False or None).
        """

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        """
        Handle paste event. (Handled paste events should return True else False or None).
        """

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        """
        Paint region given by `source` into `canvas_view` and `colors_view`.
        """
        if not self.is_transparent:
            if self.background_char is not None:
                canvas_view[:] = self.background_char

            if self.background_color_pair is not None:
                colors_view[:] = self.background_color_pair

        self.render_children(source, canvas_view, colors_view)

    def render_children(self, destination: tuple[slice, slice], canvas_view, colors_view):
        vert_slice, hori_slice = destination
        dest = Rect(vert_slice.start, vert_slice.stop, hori_slice.start, hori_slice.stop)

        for child in self.children:
            if child.is_visible and child.is_enabled:
                source = Rect(child.top, child.bottom, child.left, child.right)
                if (slices := intersection(dest, source)) is not None:
                    dest_slice, source_slice = slices
                    child.render(canvas_view[dest_slice], colors_view[dest_slice], source_slice)

    async def tween(
        self,
        *,
        duration: float=1.0,
        easing: Easing=Easing.LINEAR,
        on_start: Callable | None=None,
        on_progress: Callable | None=None,
        on_complete: Callable | None=None,
        **properties: dict[str, int | float | Sequence[int] | Sequence[float | None]],
    ):
        """
        Coroutine that sequentially updates widget properties over a duration (in seconds).

        Parameters
        ----------
        duration : float, default: 1.0
            The duration of the tween in seconds.
        easing : Easing, default: Easing.LINEAR
            The easing used for tweening.
        on_start : Callable | None, default: None
            Called when tween starts.
        on_progress : Callable | None, default: None
            Called when tween updates.
        on_complete : Callable | None, default: None
            Called when tween completes.
        **properties : dict[str, int | float | Sequence[int] | Sequence[float | None]]
            Widget properties' target values. E.g., to smoothly tween a widget's position
            to (5, 10) over 2.5 seconds, specify the `pos` property as a keyword-argument:
            ``await widget.tween(pos=(5, 10), duration=2.5, easing=Easing.OUT_BOUNCE)``

        Warnings
        --------
        Running several tweens on the same properties concurrently will probably result in unexpected
        behavior. `tween` won't work for ndarray types. If tweening size or pos hints, make sure the
        relevant hints aren't `None` to start.
        """
        end_time = monotonic() + duration
        start_values = tuple(getattr(self, attr) for attr in properties)
        easing_function = getattr(easings, easing)

        if on_start:
            on_start()

        while (current_time := monotonic()) < end_time:
            p = easing_function(1 - (end_time - current_time) / duration)

            for start_value, (prop, target) in zip(start_values, properties.items()):
                match start_value:
                    case (int(), *_):  # Sequence[int]
                        value = tuple((
                            round(easings.lerp(i, j, p))
                            for i, j in zip(start_value, target)
                        ))
                    case int():
                        value = round(easings.lerp(start_value, target, p))
                    case (float() | None, *_):  # Sequence[float | None]
                        value = tuple((
                            None if i is None else easings.lerp(i, j, p)
                            for i, j in zip(start_value, target)
                        ))
                    case float():
                        value = easings.lerp(start_value, target, p)

                setattr(self, prop, value)

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
        self.update_geometry()
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
