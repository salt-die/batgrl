"""
A recycle-view provides a view into a large data-set using as few gadgets as
possible.
"""

from __future__ import annotations

from abc import abstractmethod

from ..geometry.regions import Region
from ..terminal.events import MouseButton
from .gadget import Gadget, Point, PosHint, Size, SizeHint
from .scroll_view import ScrollView

__all__ = ["RecycleView", "Point", "Size"]


class RecycleView[T, G: Gadget](ScrollView):
    r"""
    A recycle-view provides a view into a large data-set using as few gadgets as
    possible.

    ``RecycleView`` is an abstract class. The following methods require an
    implementation:

    * ``get_layout(i)``: Return the size and position of the ith item in
      ``recycle_view_data``.
    * ``new_data_view()``: Initialize and return a new data-view gadget for the recycle
      view.
    * ``update_data_view(data_view, datum)``: Update ``data_view`` to display ``datum``.

    In addition, one may want to re-implement ``set_view_size()`` which sets the size of
    the view of all the data.

    Parameters
    ----------
    recycle_view_data: list[T] | None, default: None
        The recycle-view's data.
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
    recycle_view_data: list[T]
        The recycle-view's data.
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
    get_layout(i)
        Return the size and position of the ith item of the recycle-view's data.
    new_data_view()
        Initialize and return a new data-view gadget for the recycle-view.
    update_data_view(data_view, datum)
        Update ``data_view`` to display ``datum``.
    set_view_size()
        Set the size of the view.
    refresh_data()
        Refresh data of currently visible data-views.
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
        recycle_view_data: list[T] | None = None,
        allow_vertical_scroll: bool = True,
        allow_horizontal_scroll: bool = True,
        show_vertical_bar: bool = True,
        show_horizontal_bar: bool = True,
        dynamic_bars: bool = False,
        scrollwheel_enabled: bool = True,
        arrow_keys_enabled: bool = True,
        is_grabbable: bool = True,
        ptf_on_grab: bool = False,
        mouse_button: MouseButton = "left",
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            allow_vertical_scroll=allow_vertical_scroll,
            allow_horizontal_scroll=allow_horizontal_scroll,
            show_vertical_bar=show_vertical_bar,
            show_horizontal_bar=show_horizontal_bar,
            dynamic_bars=dynamic_bars,
            scrollwheel_enabled=scrollwheel_enabled,
            arrow_keys_enabled=arrow_keys_enabled,
            is_grabbable=is_grabbable,
            ptf_on_grab=ptf_on_grab,
            mouse_button=mouse_button,
            alpha=alpha,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self._unused_views: list[G] = []
        """Currently unused views."""
        self._index_to_view: dict[int, G] = {}
        """Index of datum to the view displaying it."""
        self._view_pos_bind: int | None = None
        """uid to unbind view's ``pos`` from ``_update_view``."""
        self._old_len_of_data: int = 0
        """
        Previous length of recycle-view data used to determine whether layout should be
        recalculated in ``refresh_data``.
        """

        self.recycle_view_data: list[T]
        """The recycle-view's data."""
        if recycle_view_data is None:
            self.recycle_view_data = []
        else:
            self.recycle_view_data = recycle_view_data

        self.view = Gadget()
        self.set_view_size()
        self.refresh_data()

    @abstractmethod
    def get_layout(self, i: int) -> tuple[Size, Point]:
        """
        Return the size and position of the ith item of the recycle-view's data.

        Parameters
        ----------
        i : int
            The index of an item in the recycle-view's data.

        Returns
        -------
        tuple[Size, Point]
            The size and position of the item.
        """

    @abstractmethod
    def new_data_view(self) -> G:
        """Initialize and return a new data-view gadget for the recycle-view."""

    @abstractmethod
    def update_data_view(self, data_view: G, datum: T) -> None:
        """Update ``data_view`` to display ``datum``."""

    def set_view_size(self) -> None:
        """
        Set the size of the view.

        The default implementation sets the view size to be the minimum size required to
        fully encompass the bottom-most, right-most rect returned by ``get_layout``.
        """
        if self.view is None:
            return

        bottom = right = 0
        for i in range(len(self.recycle_view_data)):
            size, pos = self.get_layout(i)
            current_bottom = size.height + pos.y
            if current_bottom > bottom:
                bottom = current_bottom

            current_right = size.width + pos.x
            if current_right > right:
                right = current_right

        self.view.size = Size(bottom, right)

    def refresh_data(self) -> None:
        """Refresh data of currently visible data-views."""
        if self._old_len_of_data == len(self.recycle_view_data):
            for i, data_view in self._index_to_view.items():
                self.update_data_view(data_view, self.recycle_view_data[i])
        else:
            self._old_len_of_data = len(self.recycle_view_data)
            for data_view in self._index_to_view.values():
                self.view.remove_gadget(data_view)
            self._unused_views.extend(self._index_to_view.values())
            self._index_to_view.clear()
            self.set_view_size()
            self._update_recycle_view()

    def on_add(self) -> None:
        """Bind the view's size and pos to update the items in the view."""
        super().on_add()
        self._view_pos_bind = self.view.bind("pos", self._update_recycle_view)

    def on_remove(self) -> None:
        """Unbind the view's size and pos from updating the items in the view."""
        if self.view is not None and self._view_pos_bind is not None:
            self.view.unbind(self._view_pos_bind)
        self._view_pos_bind = None
        super().on_remove()

    def on_size(self) -> None:
        """Update the recycle-view on resize."""
        super().on_size()
        if self.view is not None:
            self._update_recycle_view()

    def _update_recycle_view(self) -> None:
        scroll_view_reg = Region.from_rect(
            -self.view.pos, (self.port_height, self.port_width)
        )
        recycle_view_reg = Region.from_rect((0, 0), self.view.size)
        clipping_rect = scroll_view_reg & recycle_view_reg

        seen: list[int] = []
        for i in range(len(self.recycle_view_data)):
            size, pos = self.get_layout(i)
            datum_reg = Region.from_rect(pos, size)
            is_seen = bool(datum_reg & clipping_rect)
            has_gadget = i in self._index_to_view
            if has_gadget != is_seen:
                if has_gadget:
                    gadget = self._index_to_view[i]
                    self.view.remove_gadget(gadget)
                    self._unused_views.append(gadget)
                    del self._index_to_view[i]
                else:
                    seen.append(i)

        if len(seen) > len(self._unused_views):
            new_items = len(seen) - len(self._unused_views)
            self._unused_views.extend(self.new_data_view() for _ in range(new_items))

        for i in seen:
            gadget = self._unused_views.pop()
            self._index_to_view[i] = gadget
            gadget.size, gadget.pos = self.get_layout(i)
            self.update_data_view(gadget, self.recycle_view_data[i])
            self.view.add_gadget(gadget)
