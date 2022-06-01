"""
A scrollable view widget.
"""
from ...clamp import clamp
from ...io import KeyPressEvent, MouseEventType, MouseEvent
from ..behaviors.grabbable_behavior import GrabbableBehavior
from ..widget import Widget
from .scrollbars import _HorizontalBar, _VerticalBar


class ScrollView(GrabbableBehavior, Widget):
    """
    A scrollable view widget. A scroll view accepts only one child and
    places it in a scrollable viewport.

    Parameters
    ----------
    allow_vertical_scroll : bool, default: True
        Allow vertical scrolling.
    allow_horizontal_scroll : bool, default: True
        Allow horizontal scrolling.
    show_vertical_bar : bool, default: True
        Show the vertical scrollbar.
    show_horizontal_bar : bool, default: True
        Show the horizontal scrollbar.
    is_grabbable : bool, default: True
        Allow moving scroll view by dragging mouse.
    scrollwheel_enabled : bool, default: True
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool, default: True
        Allow scrolling with arrow keys.
    vertical_proportion : float, default: 0.0
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float, default: 0.0
        Horizontal scroll position as a proportion of total.

    Attributes
    ----------
    allow_vertical_scroll : bool
        Allow vertical scrolling.
    allow_horizontal_scroll : bool
        Allow horizontal scrolling.
    show_vertical_bar : bool
        Show the vertical scrollbar.
    show_horizontal_bar : bool
        Show the horizontal scrollbar.
    is_grabbable : bool
        Allow moving scroll view by dragging mouse.
    scrollwheel_enabled : bool
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool
        Allow scrolling with arrow keys.
    vertical_proportion : float
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float
        Horizontal scroll position as a proportion of total.
    view : Widget | None
        The scroll view's child.

    Raises
    ------
    ValueError
        If `add_widget` is called while already containing a child.
    """
    def __init__(
        self,
        allow_vertical_scroll=True,
        allow_horizontal_scroll=True,
        show_vertical_bar=True,
        show_horizontal_bar=True,
        is_grabbable=True,
        scrollwheel_enabled=True,
        arrow_keys_enabled=True,
        vertical_proportion=0.0,
        horizontal_proportion=0.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.allow_vertical_scroll = allow_vertical_scroll
        self.allow_horizontal_scroll = allow_horizontal_scroll
        self.show_vertical_bar = show_vertical_bar
        self.show_horizontal_bar = show_horizontal_bar
        self.is_grabbable = is_grabbable
        self.scrollwheel_enabled = scrollwheel_enabled
        self.arrow_keys_enabled = arrow_keys_enabled
        self._vertical_proportion = clamp(vertical_proportion, 0, 1)
        self._horizontal_proportion = clamp(horizontal_proportion, 0, 1)
        self._view = None

        self.children = [
            _VerticalBar(self),
            _HorizontalBar(self),
        ]

    @property
    def view(self) -> Widget | None:
        return self._view

    @property
    def vertical_proportion(self):
        return self._vertical_proportion

    @vertical_proportion.setter
    def vertical_proportion(self, value):
        if self.allow_vertical_scroll:
            if self._view is None or self._view.height <= self.height:
                self._vertical_proportion = 0
            else:
                self._vertical_proportion = clamp(value, 0, 1)
                self._set_view_top()

            vertical_bar = self.children[0]
            vertical_bar.indicator.update_geometry()

    @property
    def horizontal_proportion(self):
        return self._horizontal_proportion

    @horizontal_proportion.setter
    def horizontal_proportion(self, value):
        if self.allow_horizontal_scroll:
            if self._view is None or self._view.width <= self.width:
                self._horizontal_proportion = 0
            else:
                self._horizontal_proportion = clamp(value, 0, 1)
                self._set_view_left()

            horizontal_bar = self.children[1]
            horizontal_bar.indicator.update_geometry()

    @property
    def total_vertical_distance(self) -> int:
        """
        Return difference between child height and scrollview height.
        """
        if self._view is None:
            return 0

        return self._view.height - self.height + self.show_horizontal_bar

    @property
    def total_horizontal_distance(self) -> int:
        """
        Return difference between child width and scrollview width.
        """
        if self._view is None:
            return 0

        return self._view.width - self.width + self.show_vertical_bar * 2

    def _set_view_top(self):
        """
        Set the top-coordinate of the view.
        """
        if self.total_vertical_distance <= 0:
            self._view.top = 0
        else:
            self._view.top = -round(self.vertical_proportion * self.total_vertical_distance)

    def _set_view_left(self):
        """
        Set the left-coordinate of the view.
        """
        if self.total_horizontal_distance <= 0:
            self._view.left = 0
        else:
            self._view.left = -round(self.horizontal_proportion * self.total_horizontal_distance)

    def add_widget(self, widget):
        if self._view is not None:
            raise ValueError("ScrollView already has child.")

        self._view = widget
        widget.parent = self
        self._set_view_top()
        self._set_view_left()

    def remove_widget(self, widget):
        if widget is not self._view:
            raise ValueError(f"{widget} not in ScrollView")

        self._view = None
        widget.parent = None

    def on_size(self):
        if self._view is not None:
            self._set_view_left()
            self._set_view_top()

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        """
        Paint region given by source into canvas_view and colors_view.
        """
        if not self.is_transparent:
            if self.background_char is not None:
                canvas_view[:] = self.background_char

            if self.background_color_pair is not None:
                colors_view[:] = self.background_color_pair

        view = self._view
        if view is not None and view.is_enabled:
            view.render_intersection(source, canvas_view, colors_view)

        vertical_bar, horizontal_bar = self.children
        if self.show_vertical_bar:
            vertical_bar.render_intersection(source, canvas_view, colors_view)

        if self.show_horizontal_bar:
            horizontal_bar.render_intersection(source, canvas_view, colors_view)

    def on_press(self, key_press_event: KeyPressEvent):
        if not self.arrow_keys_enabled:
            return False

        match key_press_event.key:
            case "up":
                self._scroll_up()
            case "down":
                self._scroll_down()
            case "left":
                self._scroll_left()
            case "right":
                self._scroll_right()
            case _:
                return super().on_press(key_press_event)

        return True

    def grab_update(self, mouse_event: MouseEvent):
        self._scroll_up(self.mouse_dy)
        self._scroll_left(self.mouse_dx)

    def _scroll_left(self, n=1):
        if self._view is not None:
            if self.total_horizontal_distance > 0:
                self.horizontal_proportion = clamp((-self.view.left - n) / self.total_horizontal_distance, 0, 1)
            else:
                self.horizontal_proportion = 0

    def _scroll_right(self, n=1):
        self._scroll_left(-n)

    def _scroll_up(self, n=1):
        if self._view is not None:
            if self.total_vertical_distance > 0:
                self.vertical_proportion = clamp((-self.view.top - n) / self.total_vertical_distance, 0, 1)
            else:
                self.vertical_proportion = 0

    def _scroll_down(self, n=1):
        self._scroll_up(-n)

    def dispatch_press(self, key_press_event: KeyPressEvent):
        if (
            self._view is not None
            and self._view.is_enabled
            and self._view.dispatch_press(key_press_event)
        ):
            return True

        return self.on_press(key_press_event)

    def dispatch_click(self, mouse_event: MouseEvent):
        v_bar, h_bar = self.children

        if self.show_horizontal_bar and h_bar.dispatch_click(mouse_event):
            return True

        if self.show_vertical_bar and v_bar.dispatch_click(mouse_event):
            return True

        if (
            self._view is not None
            and self._view.is_enabled
            and self._view.dispatch_click(mouse_event)
        ):
            return True

        return self.on_click(mouse_event)

    def dispatch_double_click(self, mouse_event: MouseEvent):
        v_bar, h_bar = self.children

        if self.show_horizontal_bar and h_bar.dispatch_double_click(mouse_event):
            return True

        if self.show_vertical_bar and v_bar.dispatch_double_click(mouse_event):
            return True

        if (
            self._view is not None
            and self._view.is_enabled
            and self._view.dispatch_double_click(mouse_event)
        ):
            return True

        return self.on_double_click(mouse_event)

    def dispatch_triple_click(self, mouse_event: MouseEvent):
        v_bar, h_bar = self.children

        if self.show_horizontal_bar and h_bar.dispatch_triple_click(mouse_event):
            return True

        if self.show_vertical_bar and v_bar.dispatch_triple_click(mouse_event):
            return True

        if (
            self._view is not None
            and self._view.is_enabled
            and self._view.dispatch_triple_click(mouse_event)
        ):
            return True

        return self.on_triple_click(mouse_event)

    def on_click(self, mouse_event: MouseEvent):
        if (
            self.scrollwheel_enabled
            and self.collides_point(mouse_event.position)
        ):
            match mouse_event.event_type:
                case MouseEventType.SCROLL_UP:
                    self._scroll_up()
                    return True
                case MouseEventType.SCROLL_DOWN:
                    self._scroll_down()
                    return True

        return super().on_click(mouse_event)
