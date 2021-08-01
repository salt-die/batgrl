from ...colors import Color
from ...mouse.mouse_event import MouseEventType
from ...widgets.behaviors.grabbable_behavior import GrabbableBehavior
from ..widget import Widget, overlapping_region
from .scrollbars import _HorizontalBar, _VerticalBar
from .scrollbar_data_structures import ScrollBarSettings

def clamp(value, min=0.0, max=1.0):
    if value < min:
        return min
    if value > max:
        return max
    return value


class ScrollView(GrabbableBehavior, Widget):
    """
    A scrollable view widget.

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
    vertical_proportion : float, default: 0.0
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float, default: 0.0
        Horizontal scroll position as a proportion of total.
    vertical_scrollbar, horizontal_scrollbar : ScrollBarSettings, default: DEFAULT_SCROLLBAR_SETTINGS
        Settings for scrollbars.

    Notes
    -----
    ScrollView accepts only one child and applies a scrollable viewport to it.
    ScrollView's child's `top` and `left` is set from `vertical_proportion`
    and `horizontal_proportion`, respectively.

    Raises
    ------
    ValueError
        If `add_widget` is called while already containing a child.
    """
    DEFAULT_SCROLLBAR_SETTINGS = ScrollBarSettings(
        bar_color=Color.from_hex("#340744"),
        indicator_inactive_color=Color.from_hex("#debad6"),
        indicator_hover_color=Color.from_hex("#741aac"),
        indicator_active_color=Color.from_hex("#005437"),
        indicator_length=2,
    )

    def __init__(
        self,
        *args,
        allow_vertical_scroll=True,
        allow_horizontal_scroll=True,
        show_vertical_bar=True,
        show_horizontal_bar=True,
        is_grabbable=True,
        scrollwheel_enabled=True,
        vertical_proportion=0.0,
        horizontal_proportion=0.0,
        vertical_scrollbar: ScrollBarSettings=DEFAULT_SCROLLBAR_SETTINGS,
        horizontal_scrollbar: ScrollBarSettings=DEFAULT_SCROLLBAR_SETTINGS,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.allow_vertical_scroll = allow_vertical_scroll
        self.allow_horizontal_scroll = allow_horizontal_scroll
        self.is_grabbable = is_grabbable
        self.show_vertical_bar = show_vertical_bar
        self.show_horizontal_bar = show_horizontal_bar
        self.scrollwheel_enabled = scrollwheel_enabled
        self.vertical_proportion = vertical_proportion
        self.horizontal_proportion = horizontal_proportion
        self._view = None
        self._grabbed = False

        # Setup scrollbars:
        self.children = [
            _VerticalBar(settings=vertical_scrollbar),
            _HorizontalBar(settings=horizontal_scrollbar),
        ]

        for child in self.children:
            child.parent = self
            child.update_geometry()

    @property
    def vertical_proportion(self):
        return self._vertical_proportion

    @vertical_proportion.setter
    def vertical_proportion(self, value):
        self._vertical_proportion = clamp(value)

    @property
    def horizontal_proportion(self):
        return self._horizontal_proportion

    @horizontal_proportion.setter
    def horizontal_proportion(self, value):
        self._horizontal_proportion = clamp(value)

    @property
    def total_vertical_distance(self):
        """
        Return difference between child height and scrollview height.
        """
        if self._view is None:
            return 0

        return self._view.height - self.height + self.show_horizontal_bar

    @property
    def total_horizontal_distance(self):
        """
        Return difference between child width and scrollview width.
        """
        if self._view is None:
            return 0

        return self._view.width - self.width + self.show_vertical_bar * 2

    @property
    def view_top(self):
        """
        The current top-coordinate of child due to `vertical_proportion`.
        """
        total_vertical_distance = self.total_vertical_distance
        if total_vertical_distance <= 0:
            return 0

        return -round(self.vertical_proportion * total_vertical_distance)

    @property
    def view_left(self):
        """
        The current left-coordinate of child due to `horizontal_proportion`.
        """
        total_horizontal_distance = self.total_horizontal_distance
        if total_horizontal_distance <= 0:
            return 0

        return -round(self.horizontal_proportion * total_horizontal_distance)

    def add_widget(self, widget):
        if self._view is not None:
            raise ValueError("ScrollView already has child.")

        self._view = widget

    def remove_widget(self, widget):
        if widget is not self._view:
            raise ValueError(f"{widget} not in ScrollView")

        self._view = None

    def render(self, canvas_view, colors_view, rect):
        """
        Paint region given by rect into canvas_view and colors_view.
        """
        t, l, b, r, _, _ = rect

        index_rect = slice(t, b), slice(l, r)
        if self.is_transparent:
            source = self.canvas[index_rect]
            visible = source != " "  # " " isn't painted if transparent.

            canvas_view[visible] = source[visible]
            colors_view[visible] = self.colors[index_rect][visible]
        else:
            canvas_view[:] = self.canvas[index_rect]
            colors_view[:] = self.colors[index_rect]

        overlap = overlapping_region

        if view := self._view:
            view.top = self.view_top
            view.left = self.view_left

            if region := overlap(rect, view):  # Can this condition can fail?
                dest_slice, view_rect = region
                view.render(canvas_view[dest_slice], colors_view[dest_slice], view_rect)

        vertical_bar, horizontal_bar = self.children
        if self.show_vertical_bar and (region := overlap(rect, vertical_bar)):
            dest_slice, vertical_bar_rect = region
            vertical_bar.render(canvas_view[dest_slice], colors_view[dest_slice], vertical_bar_rect)

        if self.show_horizontal_bar and (region := overlap(rect, horizontal_bar)):
            dest_slice, horizontal_bar_rect = region
            horizontal_bar.render(canvas_view[dest_slice], colors_view[dest_slice], horizontal_bar_rect)

    def on_press(self, key_press):
        if key_press.key == 'up':
            self._scroll_up()
        elif key_press.key == 'down':
            self._scroll_down()
        elif key_press.key == 'left':
            self._scroll_left()
        elif key_press.key == 'right':
            self._scroll_right()
        else:
            return super().on_press(key_press)

        return True

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self._last_touch = mouse_event.position

    def grab_update(self, mouse_event):
        last_y, last_x = self._last_touch
        y, x = self._last_touch = mouse_event.position

        self._scroll_up(y - last_y)
        self._scroll_left(x - last_x)

    def _scroll_left(self, n=1):
        if self._view is not None and self.allow_horizontal_scroll:
            self.horizontal_proportion = hp = clamp((-self.view_left - n) / self.total_horizontal_distance)
            self.children[1].indicator.update_geometry()

    def _scroll_right(self, n=1):
        self._scroll_left(-n)

    def _scroll_up(self, n=1):
        if self._view is not None and self.allow_vertical_scroll:
            self.vertical_proportion = vp = clamp((-self.view_top - n) / self.total_vertical_distance)
            self.children[0].indicator.update_geometry()

    def _scroll_down(self, n=1):
        self._scroll_up(-n)

    def dispatch_press(self, key_press):
        if self._view and self._view.dispatch_press(key_press):
            return True

        return self.on_press(key_press)

    def dispatch_click(self, mouse_event):
        v_bar, h_bar = self.children

        if self.show_horizontal_bar and h_bar.dispatch_click(mouse_event):
            return True

        if self.show_vertical_bar and v_bar.dispatch_click(mouse_event):
            return True

        if self._view and self._view.dispatch_click(mouse_event):
            return True

        return self.on_click(mouse_event)

    def on_click(self, mouse_event):
        if mouse_event.event_type == MouseEventType.SCROLL_UP:
            self._scroll_up()
        elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            self._scroll_down()
        else:
            return super().on_click(mouse_event)

        return True