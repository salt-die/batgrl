from abc import ABC, abstractmethod

from ..io import KeyPressEvent, MouseEvent, PasteEvent
from ..data_structures import *
from .widget_data_structures import *


class _WidgetBase(ABC):
    def __init__(
        self,
        *,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint=SizeHint(None, None),
        pos_hint: PosHint=PosHint(None, None),
        anchor=Anchor.TOP_LEFT,
        is_transparent: bool=False,
        is_visible: bool=True,
        is_enabled: bool=True,
    ):
        self.parent = None
        self.children = [ ]

        self._size = Size(*size)
        self.pos = pos

        self.size_hint = size_hint

        self.pos_hint = pos_hint
        self.anchor = anchor

        self.is_transparent = is_transparent
        self.is_visible = is_visible
        self.is_enabled = is_enabled

    @property
    def size(self):
        return self._size

    @property
    def pos(self):
        """
        Relative position to parent.
        """
        return Point(self.top, self.left)

    @property
    def size_hint(self):
        return self._size_hint

    @size_hint.setter
    def size_hint(self, value):
        h, w = value

        if h is not None and h <= 0:
            raise ValueError(f"invalid height hint ({h=})")

        if w is not None and w <= 0:
            raise ValueError(f"invalid width hint ({w=})")

        self._size_hint = SizeHint(h, w)

        if self.parent:
            self.update_geometry()

    @property
    def pos_hint(self):
        return self._pos_hint

    @pos_hint.setter
    def pos_hint(self, value):
        self._pos_hint = value
        if self.parent:
            self.update_geometry()

    @pos.setter
    def pos(self, point: Point):
        self.top, self.left = point

    @abstractmethod
    def resize(self, size: Size):
        """
        Resize widget.
        """

    def update_geometry(self):
        """
        Update geometry due to a change in parent's size.
        """
        h, w = self.parent.size
        h_hint, w_hint = self.size_hint

        height = self.height if h_hint is None else int(h_hint * h)
        width = self.width if w_hint is None else int(w_hint * w)

        self.resize(Size(height, width))

        if self.pos_hint == (None, None):
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

        h, w = self.parent.size
        top_hint, left_hint = self.pos_hint

        if top_hint is not None:
            self.top = round(h * top_hint) - offset_top

        if left_hint is not None:
            self.left = round(w * left_hint) - offset_left

    @property
    def absolute_pos(self):
        """
        Absolute position on screen.
        """
        y, x = self.parent.absolute_pos
        return Point(self.top + y, self.left + x)

    @property
    def height(self):
        return self._size[0]

    rows = height

    @property
    def width(self):
        return self._size[1]

    columns = width

    @property
    def y(self):
        return self.top

    @property
    def x(self):
        return self.left

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def right(self):
        return self.left + self.width

    @property
    def rect(self):
        """
        `Rect` of bounding box relative to parent.

        Notes
        -----
        `rect` of root widget is same as `absolute_rect`.
        """
        return Rect(
            self.top,
            self.left,
            self.bottom,
            self.right,
            self.height,
            self.width
        )

    @property
    def absolute_rect(self):
        """
        `Rect` of bounding box on screen.
        """
        top, left = self.absolute_pos
        height, width = self.size
        return Rect(
            top,
            left,
            top + height,
            left + width,
            height,
            width,
        )

    @property
    def center(self):
        return Point(self.height // 2, self.width // 2)

    @property
    def root(self):
        """
        The root widget.
        """
        return self.parent.root

    @property
    def app(self):
        """
        The running app.
        """
        return self.root.app

    def to_local(self, point: Point):
        """
        Convert point in absolute coordinates to local coordinates.
        """
        y, x = self.parent.to_local(point)
        return Point(y - self.top, x - self.left)

    def collides_point(self, point: Point):
        """
        Return True if point is within widget's bounding box.
        """
        y, x = self.to_local(point)
        return 0 <= y < self.height and 0 <= x < self.width

    def collides_widget(self, widget):
        """
        Return True if some part of widget is within bounding box.
        """
        self_top, self_left, self_bottom, self_right, _, _ = self.absolute_rect
        other_top, other_left, other_bottom, other_right, _ , _ = widget.absolute_rect

        return not (
            self_top >= other_bottom
            or other_top >= self_bottom
            or self_left >= other_right
            or other_left >= self_right
        )

    def add_widget(self, widget):
        """
        Add a child widget.
        """
        self.children.append(widget)
        widget.parent = self
        widget.update_geometry()

    def add_widgets(self, *widgets):
        """
        Add multiple child widgets.
        """
        if len(widgets) == 1 and not isinstance(widgets[0], _WidgetBase):
            # Assume item is an iterable of widgets.
            widgets = widgets[0]

        for widget in widgets:
            self.add_widget(widget)

    def remove_widget(self, widget):
        """
        Remove widget.
        """
        self.children.remove(widget)
        widget.parent = None

    def pull_to_front(self):
        """
        Move widget to end of widget stack so that it is drawn last.
        """
        parent = self.parent
        parent.remove_widget(self)
        parent.add_widget(self)

    def walk_from_root(self):
        """
        Yield all descendents of the root widget.
        """
        for child in self.root.children:
            yield child
            yield from child.walk()

    def walk(self):
        """
        Yield all descendents.
        """
        for child in self.children:
            yield child
            yield from child.walk()

    @abstractmethod
    def render(self, canvas_view, colors_view, rect: Rect):
        ...

    def dispatch_press(self, key_press_event: KeyPressEvent):
        """
        Dispatch key press until handled. (A key press is handled if a handler returns True.)
        """
        return (
            any(
                widget.dispatch_press(key_press_event)
                for widget in reversed(self.children)
                if widget.is_enabled
            )
            or self.on_press(key_press_event)
        )

    def dispatch_click(self, mouse_event: MouseEvent):
        """
        Dispatch mouse event until handled. (A mouse event is handled if a handler returns True.)
        """
        return (
            any(
                widget.dispatch_click(mouse_event)
                for widget in reversed(self.children)
                if widget.is_enabled
            )
            or self.on_click(mouse_event)
        )

    def dispatch_paste(self, paste_event: PasteEvent):
        """
        Dispatch paste event until handled.
        """
        return (
            any(
                widget.dispatch_paste(paste_event)
                for widget in reversed(self.children)
                if widget.is_enabled
            )
            or self.on_paste(paste_event)
        )

    def on_press(self, key_press_event: KeyPressEvent):
        """
        Handle key press event. (Handled key presses should return True else False or None).
        """

    def on_click(self, mouse_event: MouseEvent):
        """
        Handle mouse event. (Handled mouse events should return True else False or None).
        """

    def on_paste(self, paste_event: PasteEvent):
        """
        Handle paste event.
        """


def intersection(rect: Rect, widget: _WidgetBase):
    """
    Find the intersection of a rect with a widget.
    """
    t, l, _, _, h, w = rect  # top, left, height, width

    wt = widget.top - t
    wb = widget.bottom - t
    wl = widget.left - l
    wr = widget.right - l

    if (
        wt >= h
        or wb < 0
        or wl >= w
        or wr < 0
    ):
        # widget doesn't overlap.
        return False

    ####################################################################
    # Four cases for top / bottom of widget:                           #
    #     1) widget top is off-screen and widget bottom is off-screen. #
    #               +--------+                                         #
    #            +--| widget |------------+                            #
    #            |  |        |   dest     |                            #
    #            +--|        |------------+                            #
    #               +--------+                                         #
    #     2) widget top is off-screen and widget bottom is on-screen.  #
    #               +--------+                                         #
    #            +--| widget |------------+                            #
    #            |  +--------+   dest     |                            #
    #            +------------------------+                            #
    #                                                                  #
    #     3) widget top is on-screen and widget bottom is off-screen.  #
    #            +------------------------+                            #
    #            |  +--------+   dest     |                            #
    #            +--| widget |------------+                            #
    #               +--------+                                         #
    #                                                                  #
    #     4) widget top is on-screen and widget bottom is on-screen.   #
    #            +------------------------+                            #
    #            |  +--------+            |                            #
    #            |  | widget |   dest     |                            #
    #            |  +--------+            |                            #
    #            +------------------------+                            #
    #                                                                  #
    # Similarly, by symmetry, four cases for left / right of widget.   #
    ####################################################################

    # st, dt, sb, db, sl, dl, sr, dr stand for source_top, destination_top, source_bottom,
    # destination_bottom, source_left, destination_left, source_right, destination_right.
    if wt < 0:
        st = -wt
        dt = 0

        if wb >= h:
            sb = h + st
            db = h
        else:
            sb = widget.height
            db = wb
    else:
        st =  0
        dt = wt

        if wb >= h:
            sb = h - dt
            db = h
        else:
            sb = widget.height
            db = wb

    if wl < 0:
        sl = -wl
        dl = 0

        if wr >= w:
            sr = w + sl
            dr = w
        else:
            sr = widget.width
            dr = wr
    else:
        sl = 0
        dl = wl

        if wr >= w:
            sr = w - dl
            dr = w
        else:
            sr = widget.width
            dr = wr

    return (
        (slice(dt, db), slice(dl, dr)),
        Rect(st, sl, sb, sr, sb - st, sr - sl),
    )
