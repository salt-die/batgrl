"""
A movable, resizable window widget.
"""
from wcwidth import wcswidth

from ..clamp import clamp
from ..colors import ColorPair, AColor
from .behaviors.focus_behavior import FocusBehavior
from .behaviors.grabbable_behavior import GrabbableBehavior
from .behaviors.grab_resize_behavior import GrabResizeBehavior
from .behaviors.themable import Themable
from .graphic_widget import GraphicWidget
from .text_widget import TextWidget
from .widget import Widget, Size, Anchor

__all__ = "Window",


class _TitleBar(GrabbableBehavior, TextWidget):
    def __init__(self, **kwargs):
        super().__init__(disable_ptf=True, **kwargs)

        self._label = TextWidget(pos_hint=(None, .5), anchor=Anchor.TOP_CENTER)
        self.add_widget(self._label)

    def grab_update(self, mouse_event):
        self.parent.top += self.mouse_dy
        self.parent.left += self.mouse_dx

    def update_geometry(self):
        bh, bw = self.parent.border_size
        self.size = bh, self.parent.width - 2 * bw


class _View(GraphicWidget):
    def update_geometry(self):
        h, w = self.parent.size
        bh, bw = self.parent.border_size
        self.size = h - 1 - 2 * bh, w - 2 * bw
        self.is_visible = h > bh * 3 and w > bw * 2


class Window(Themable, FocusBehavior, GrabResizeBehavior, Widget):
    """
    A movable, resizable window widget.

    Parameters
    ----------
    title : str, default: ""
        Title of window.
    alpha : float, default: 1.0
        Transparency of window background and border.

    Notes
    -----
    If not given or too small, `min_height` and `min_width` will be
    set large enough so that the border is visible and the titlebar's
    label is visible.
    """
    def __init__(self, title="", alpha=1.0, **kwargs):
        self._view = None

        super().__init__(**kwargs)

        if self.min_height is None:
            self.min_height = 1

        if self.min_width is None:
            self.min_width = 1

        self.add_widgets(_View(), _TitleBar())
        self.pull_border_to_front()
        self._view = self.children[0]
        self._titlebar = self.children[1]

        self.alpha = alpha
        self.title = title

        self.update_theme()

        self.border_size = self.border_size  # Reposition titlebar and view

    @property
    def border_size(self) -> Size:
        return self._border_size

    @border_size.setter
    def border_size(self, size: Size):
        h, w = size
        self._border_size = Size(clamp(h, 1, None), clamp(w, 1, None))

        for border in self._borders:
            border.update_geometry()

        if self._view is None:  # Still being initialized.
            return

        self._titlebar.pos = h, w
        self._view.pos = h * 2, w

        self.min_height = max(h * 3, self.min_height)
        self.min_width = max(wcswidth(self._title) + self.border_size.width * 2 + 2, self.min_width)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title
        self._titlebar._label.size = 1, wcswidth(title)
        self._titlebar._label.add_text(title)
        self.min_width = max(wcswidth(title) + self.border_size.width * 2 + 2, self.min_width)

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._alpha = clamp(alpha, 0.0, 1.0)
        self.border_alpha = self._view.alpha = self._alpha

    def update_theme(self):
        ct = self.color_theme

        view_background = AColor(*ct.primary_bg_light, 255)
        self._view.default_color = view_background
        self._view.texture[:] = view_background

        if self.is_focused:
            self.border_color = AColor(*ct.secondary_bg, 255)
        else:
            self.border_color = AColor(*ct.primary_bg, 255)

        title_bar_color_pair = ColorPair.from_colors(ct.secondary_bg, ct.primary_bg_dark)
        self._titlebar.default_color_pair = title_bar_color_pair
        self._titlebar.colors[:] = title_bar_color_pair
        self._titlebar._label.default_color_pair = title_bar_color_pair
        self._titlebar._label.colors[:] = title_bar_color_pair

    def on_focus(self):
        self.update_theme()

    def on_blur(self):
        self.update_theme()

    def add_widget(self, widget):
        if self._view is None:  # Still being initialized.
            super().add_widget(widget)
        else:
            self._view.add_widget(widget)

    def remove_widget(self, widget):
        if self._view is None:  # Still being initialized.
            super().remove_widget(widget)
        else:
            self._view.remove_widget(widget)

    def dispatch_click(self, mouse_event):
        return super().dispatch_click(mouse_event) or self.collides_point(mouse_event.position)

    def dispatch_double_click(self, mouse_event):
        return super().dispatch_double_click(mouse_event) or self.collides_point(mouse_event.position)

    def dispatch_triple_click(self, mouse_event):
        return super().dispatch_triple_click(mouse_event) or self.collides_point(mouse_event.position)
