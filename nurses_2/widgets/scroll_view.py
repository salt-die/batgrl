from .widget import Widget, overlapping_region

def clamp(value, min=0.0, max=1.0):
    if value < min:
        return min
    if value > max:
        return max
    return value


class ScrollView(Widget):
    """
    A scrollable view widget.

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

    def __init__(
        self,
        *args,
        scroll_vertical=True,
        scroll_horizontal=True,
        draggable=True,
        vertical_scrollbar=True,
        horizontal_scrollbar=True,
        scrollwheel_enabled=True,
        vertical_proportion=0.0,
        horizontal_proportion=0.0,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.scroll_vertical = scroll_vertical
        self.scroll_horizontal = scroll_horizontal
        self.draggable = draggable
        self.vertical_scrollbar = vertical_scrollbar
        self.horizontal_scrollbar = horizontal_scrollbar
        self.scrollwheel_enabled = scrollwheel_enabled
        self.vertical_proportion = vertical_proportion
        self.horizontal_proportion = horizontal_proportion
        self._view = None

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
            return None

        return self._view.height - self.height

    @property
    def total_horizontal_distance(self):
        """
        Return difference between child width and scrollview width.
        """
        if self._view is None:
            return None

        return self._view.width - self.width

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
        if self.children:
            raise ValueError("ScrollView already has child.")

        self._view = widget

        super().add_widget(widget)

    def remove_widget(self, widget):
        super().remove_widget(widget)

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

        if view := self._view:
            view.top = self.view_top
            view.left = self.view_left

            if region := overlapping_region(rect, view):  # Can this condition can fail?
                dest_slice, view_rect = region
                view.render(canvas_view[dest_slice], colors_view[dest_slice], view_rect)

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
            return

        return True

    def _scroll_left(self, n=1):
        if self._view is not None and self.scroll_horizontal:
            self.horizontal_proportion = clamp((-self.view_left - n) / self.total_horizontal_distance)

    def _scroll_right(self, n=1):
        self._scroll_left(-n)

    def _scroll_up(self, n=1):
        if self._view is not None and self.scroll_vertical:
            self.vertical_proportion = clamp((-self.view_top - n) / self.total_vertical_distance)

    def _scroll_down(self, n=1):
        self._scroll_up(-n)
