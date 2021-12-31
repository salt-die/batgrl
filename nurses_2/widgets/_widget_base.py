from abc import ABC, abstractmethod

import numpy as np

from ..io import KeyPressEvent, MouseEvent, PasteEvent
from ..data_structures import *
from .widget_data_structures import *


class _WidgetBase(ABC):
    """
    Base for TextWidget and GraphicWidget with abstract methods `resize` and `render`.
    """
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
    def size(self) -> Size:
        return self._size

    @property
    def height(self) -> int:
        return self._size[0]

    rows = height

    @property
    def width(self) -> int:
        return self._size[1]

    columns = width

    @property
    def pos(self) -> Point:
        """
        Position relative to parent.
        """
        return Point(self.top, self.left)

    @pos.setter
    def pos(self, point: Point):
        self.top, self.left = point

    @property
    def y(self) -> int:
        """
        Alias for top.
        """
        return self.top

    @y.setter
    def y(self, value: int):
        self.top = value

    @property
    def x(self) -> int:
        """
        Alias for left.
        """
        return self.left

    @x.setter
    def x(self, value: int):
        self.left = value

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @bottom.setter
    def bottom(self, value: int):
        self.top = value - self.height

    @property
    def right(self) -> int:
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
        return Point(self.height // 2, self.width // 2)

    @property
    def size_hint(self) -> SizeHint:
        return self._size_hint

    @size_hint.setter
    def size_hint(self, value: SizeHint):
        h, w = value

        if h is not None and h <= 0:
            raise ValueError(f"invalid height hint ({h=})")

        if w is not None and w <= 0:
            raise ValueError(f"invalid width hint ({w=})")

        self._size_hint = SizeHint(h, w)

        if self.parent:
            self.update_geometry()

    @property
    def pos_hint(self) -> PosHint:
        return self._pos_hint

    @pos_hint.setter
    def pos_hint(self, value: PosHint):
        self._pos_hint = PosHint(*value)

        if self.parent:
            self.update_geometry()

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

    def to_local(self, point: Point) -> Point:
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

    def collides_widget(self, widget) -> bool:
        """
        Return True if some part of widget is within bounding box.
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

    def dispatch_press(self, key_press_event: KeyPressEvent) -> bool | None:
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

    def dispatch_click(self, mouse_event: MouseEvent) -> bool | None:
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

    def dispatch_paste(self, paste_event: PasteEvent) -> bool | None:
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

    def on_press(self, key_press_event: KeyPressEvent) -> bool | None:
        """
        Handle key press event. (Handled key presses should return True else False or None).
        """

    def on_click(self, mouse_event: MouseEvent) -> bool | None:
        """
        Handle mouse event. (Handled mouse events should return True else False or None).
        """

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        """
        Handle paste event. (Handled paste events should return True else False or None).
        """

    @abstractmethod
    def render(self, canvas_view, colors_view, source_slice: tuple[slice, slice]):
        ...

    def render_children(self, destination: tuple[slice, slice], canvas_view, colors_view):
        for child in self.children:
            if child.is_visible and child.is_enabled:
                child.render_intersection(destination, canvas_view, colors_view)

    def render_intersection(
        self,
        destination: tuple[slice, slice],
        canvas_view,
        colors_view,
    ) -> tuple[tuple[slice, slice], tuple[slice, slice]]:
        """
        Render the intersection of destination with widget.
        """
        vert_slice, hori_slice = destination
        t = vert_slice.start
        h = vert_slice.stop - t
        l = hori_slice.start
        w = hori_slice.stop - l

        wt = self.top - t
        wb = self.bottom - t
        wl = self.left - l
        wr = self.right - l

        if (
            wt >= h
            or wb < 0
            or wl >= w
            or wr < 0
        ):
            # widget doesn't intersect.
            return

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
                sb = self.height
                db = wb
        else:
            st =  0
            dt = wt

            if wb >= h:
                sb = h - dt
                db = h
            else:
                sb = self.height
                db = wb

        if wl < 0:
            sl = -wl
            dl = 0

            if wr >= w:
                sr = w + sl
                dr = w
            else:
                sr = self.width
                dr = wr
        else:
            sl = 0
            dl = wl

            if wr >= w:
                sr = w - dl
                dr = w
            else:
                sr = self.width
                dr = wr

        dest_slice = np.s_[dt: db, dl : dr]
        self.render(canvas_view[dest_slice], colors_view[dest_slice], np.s_[st: sb, sl: sr])
