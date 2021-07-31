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
        self.vertical_proportion = clamp(vertical_proportion)
        self.horizontal_proportion = clamp(horizontal_proportion)

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

        overlap = overlapping_region

        if view := self._view:
            view.top = -round(self.vertical_proportion * (view.height - self.height))
            view.left = -round(self.horizontal_proportion * (view.width - self.width))

            if region := overlap(rect, view):
                dest_slice, child_rect = region
                view.render(canvas_view[dest_slice], colors_view[dest_slice], child_rect)

    def on_press(self, key_press):
        if not (view := self._view):
            return

        total_scroll_distance = view.height - self.height

        if key_press.key == 'up':
            if self.scroll_vertical:
                self.vertical_proportion = clamp(
                    (round(self.vertical_proportion * total_scroll_distance) - 1)
                    / total_scroll_distance
                )
        elif key_press.key == 'down':
            if self.scroll_vertical:
                self.vertical_proportion = clamp(
                    (round(self.vertical_proportion * total_scroll_distance) + 1)
                    / total_scroll_distance
                )
        elif key_press.key == 'left':
            if self.scroll_horizontal:
                self.horizontal_proportion = clamp(
                    (round(self.horizontal_proportion * total_scroll_distance) - 1)
                    / total_scroll_distance
                )
        elif key_press.key == 'right':
            if self.scroll_horizontal:
                self.horizontal_proportion = clamp(
                    (round(self.horizontal_proportion * total_scroll_distance) + 1)
                    / total_scroll_distance
                )
