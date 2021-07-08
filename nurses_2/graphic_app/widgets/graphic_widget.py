import cv2
import numpy as np

from ...widgets._widget_data_structures import Rect
from ...widgets.widget import Widget, overlapping_region
from ...colors import BLACK


class GraphicWidget:
    """
    A generic graphic element.

    Parameters
    ----------
    dim : tuple[int, int], default: (10, 10)
        Dimensions of widget.
    pos : tuple[int, int], default: (0, 0)
        Position of upper-left corner in parent.
    alpha: float (0 <= alpha <= 1), default: 1.0
        Multiplier against alpha channel.
    is_transparent : bool, default: True
        Render transparency if true.
    is_visible : bool, default: True
        If false, widget won't be painted.
    default_color : ColorPair, default: BLACK
        Default color of widget.
    """
    registry = { }

    def __init_subclass__(cls):
        GraphicWidget.registry[cls.__name__] = cls

    def __init__(
        self,
        dim=(10, 10),
        pos=(0, 0),
        *,
        alpha=1.0,
        is_transparent=True,
        is_visible=True,
        default_color=BLACK,
        texture=None,
        source=None,
    ):
        self._dim = dim
        self.top, self.left = pos
        self._alpha = alpha
        self.is_transparent = is_transparent
        self.is_visible = is_visible

        self.parent = None
        self.children = [ ]

        self.default_color = default_color

        if source:
            self.source = source
        else:
            self._source = None
            self.texture = texture

    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, new_texture):
        if new_texture is None:
            self._texture = np.full((1, 1, 3), self.default_color, np.uint8)
        else:
            assert new_texture.dtype == np.dtype(np.uint8), "texture dtype should be 'uint8'"
            assert len(new_texture.shape) == 3 and new_texture.shape[-1] in (3, 4), f"texture has bad shape, {new_texture.shape}"

            self._texture = new_texture

        self.resize(self.dim)

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, new_alpha):
        self._alpha = new_alpha
        self.resize(self.dim)  # Reload alpha channels

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, path):
        path = str(path)

        # Load unchanged to determine if there is an alpha channel.
        unchanged_texture = cv2.imread(path, cv2.IMREAD_UNCHANGED)

        if unchanged_texture.shape[-1] == 4:
            alpha = unchanged_texture[..., -1].copy()

            # Uncertain if this is necessary.
            if alpha.dtype == np.dtype(np.uint16):
                alpha = (alpha // 257).astype(np.uint8)  #  Note 65535 // 255 == 257
            elif alpha.dtype == np.dtype(np.float32):
                alpha = (alpha * 255).astype(np.uint8)

        else:
            alpha = None

        # Reload in BGR format.
        bgr_texture = cv2.imread(path, cv2.IMREAD_COLOR)
        texture = cv2.cvtColor(bgr_texture, cv2.COLOR_BGR2RGB)

        self.texture = np.dstack((texture, alpha)) if alpha is not None else texture

    def resize(self, dim):
        """
        Resize widget.
        """
        self._dim = h, w = dim
        TEXTURE_DIM = w, 2 * h

        texture =  cv2.resize(self._texture[..., :3], TEXTURE_DIM)
        self.colors = np.dstack((texture[::2], texture[1::2])).reshape((h, w, 2, 3))

        if self._texture.shape[-1] == 4:
            texture_alpha = cv2.resize(self._texture[..., -1], TEXTURE_DIM) / 255 * self.alpha
            self.alpha_channels = np.dstack((texture_alpha[::2], texture_alpha[1::2]))[..., None]
        else:
            self.alpha_channels = self.alpha

        for child in self.children:
            child.update_geometry()

    def update_geometry(self):
        """
        Update geometry due to a change in parent's size.
        """

    @property
    def dim(self):
        return self._dim

    @property
    def height(self):
        return self._dim[0]

    @property
    def width(self):
        return self._dim[1]

    @property
    def pos(self):
        return self.top, self.left

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def right(self):
        return self.left + self.width

    @property
    def rect(self):
        return Rect(
            self.top,
            self.left,
            self.bottom,
            self.right,
            self.height,
            self.width
        )

    @property
    def middle(self):
        return self.height // 2, self.width // 2

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

    def absolute_to_relative_coords(self, coords):
        """
        Convert absolute coordinates to relative coordinates.
        """
        y, x = self.parent.absolute_to_relative_coords(coords)
        return y - self.top, x - self.left

    def collides_coords(self, coords):
        """
        Return True if screen-coordinates are within this widget's bounding box.
        """
        y, x = self.absolute_to_relative_coords(coords)
        return 0 <= y < self.height and 0 <= x < self.width

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
        if len(widgets) == 1 and not isinstance(widgets[0], Widget):
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

    def pull_to_front(self, widget):
        """
        Move widget to end of widget stack so that it is drawn last.
        """
        self.children.remove(widget)
        self.children.append(widget)

    def walk_from_root(self):
        """
        Yield all descendents of the root widget.
        """
        for child in self.root.children:
            yield from child.walk()

    def walk(self):
        """
        Yield self and all descendents.
        """
        yield self

        for child in widget.children:
            yield from child.walk()

    def render(self, colors_view, rect):
        """
        Paint region given by rect into colors_view.
        """
        t, l, b, r, h, w = rect

        index_rect = slice(t, b), slice(l, r)
        if not self.is_transparent:
            colors_view[:] = self.colors[index_rect]

        else:
            buffer = np.zeros((h, w, 2, 3), dtype=np.float16)

            # RGBA on rgb == rgb + (RGB - rgb) * A1
            np.subtract(self.colors[index_rect], colors_view, out=buffer, dtype=np.float16)
            np.multiply(buffer, self.alpha_channels, out=buffer)
            np.add(buffer, colors_view, out=colors_view, casting="unsafe")

        overlap = overlapping_region

        for child in self.children:
            if region := overlap(rect, child):
                dest_slice, child_rect = region
                child.render(colors_view[dest_slice], child_rect)

    def dispatch_press(self, key_press):
        """
        Try to handle key press; if not handled, dispatch to descendents until handled.
        (A key press is handled if a handler returns True.)
        """
        return (
            self.on_press(key_press)
            or any(widget.dispatch_press(key_press) for widget in reversed(self.children))
        )

    def dispatch_click(self, mouse_event):
        """
        Try to handle mouse event; if not handled, dispatch to descendents until handled.
        (A mouse event is handled if a handler returns True.)
        """
        return (
            self.on_click(mouse_event)
            or any(widget.dispatch_click(mouse_event) for widget in reversed(self.children))
        )

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
