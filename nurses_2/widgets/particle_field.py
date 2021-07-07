from .widget import Widget
from ..colors import WHITE_ON_BLACK


class ParticleField(Widget):
    """
    A Widget that only has `Particle` children.

    ParticleField's `render` and `dispatch_*` methods are specifically for `Particle` children.

    Raises
    ------
    ValueError if `add_widget` is called with non-`Particle`.
    """
    def add_widget(self, widget):
        if not isinstance(widget, Particle):
            raise ValueError(f"expected Particle, got {type(widget).__name__}")

        super().add_widget(widget)

    def walk(self):
        yield self
        yield from self.children

    def _render_child(self, child):
        raise NotImplementedError

    def render(self, canvas_view, colors_view, rect):
        """
        Paint region given by rect into canvas_view and colors_view.
        """
        t, l, b, r, h, w = rect

        index_rect = slice(t, b), slice(l, r)
        if self.is_transparent:
            source = self.canvas[index_rect]
            visible = source != " "  # " " isn't painted if transparent.

            canvas_view[visible] = source[visible]
            colors_view[visible] = self.colors[index_rect][visible]
        else:
            canvas_view[:] = self.canvas[index_rect]
            colors_view[:] = self.colors[index_rect]

        for child in self.children:
            pos = top, left = child.top - t, child.left - l

            if (
                child.is_visible
                and not (child.is_transparent and child.char == " ")
                and 0 <= top < h
                and 0 <= left < w
            ):
                canvas_view[pos] = child.char
                colors_view[pos] = child.color

    def dispatch_press(self, key_press):
        """
        Try to handle key press; if not handled, dispatch event to particles until handled.
        """
        return (
            self.on_press(key_press)
            or any(particle.on_press(key_press) for particle in reversed(self.children))
        )

    def dispatch_click(self, mouse_event):
        return (
            self.on_click(mouse_event)
            or any(particle.on_click(mouse_event) for particle in reversed(self.children))
        )


class Particle:
    """
    A 1x1 TUI element that's Widget-like, except it has no render method.
    Particles require a `ParticleField` parent to be rendered.
    """
    def __init__(
        self,
        pos=(0, 0),
        *,
        char=" ",
        color=WHITE_ON_BLACK,
        is_transparent=False,
        is_visible=True,
    ):
        self.char = char
        self.color = color

        self.top, self.left = pos
        self.is_transparent = is_transparent
        self.is_visible = is_visible
        self.parent = None

    def update_geometry(self):
        """
        Update geometry due to a change in parent's size.
        """

    @property
    def dim(self):
        return 1, 1

    @property
    def pos(self):
        return self.top, self.left

    @property
    def height(self):
        return 1

    @property
    def width(self):
        return 1

    @property
    def bottom(self):
        return self.top + 1

    @property
    def right(self):
        return self.left + 1

    @property
    def middle(self):
        return 0, 0

    def absolute_to_relative_coords(self, coords):
        """
        Convert absolute coordinates to relative coordinates.
        """
        y, x = self.parent.absolute_to_relative_coords(coords)
        return y - self.top, x - self.left

    def on_press(self, key_press):
        """
        Handle key press. (Handled key presses should return True else False or None).

        Notes
        -----
        `key_press` is a `prompt_toolkit` `KeyPress`.
        """

    def on_click(self, mouse_event):
        """
        Handle mouse event. (Handled mouse events should return True else False or None).

        Notes
        -----
        `mouse_event` is a `prompt_toolkit` MouseEvent`.
        """
