from pathlib import Path

import cv2
import numpy as np

from .widget import Widget
from ..colors import BLACK_ON_BLACK


class ReloadTextureProperty:
    def __set_name__(self, owner, name):
        self.name = '_' + name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return getattr(instance, self.name)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value
        instance._load_texture()


class Image(Widget):
    """
    An Image widget.

    Notes
    -----
    Changing the path to an Image (or updating `is_grayscale` or `alpha_threshold`)
    will immediately reload the image.

    Parameters
    ----------
    path : pathlib.Path
        Path to image.
    is_grayscale : bool, default: False
        If true, convert image to grayscale.
    """
    is_grayscale = ReloadTextureProperty()
    path = ReloadTextureProperty()

    def __init__(self, *args, path: Path, is_grayscale=False, **kwargs):
        kwargs.pop('default_char', None)
        kwargs.pop('default_color', None)

        super().__init__(*args, default_char="▀", default_color=BLACK_ON_BLACK, **kwargs)

        self._is_grayscale = is_grayscale
        self._path = path

        self._load_texture()

    def _load_texture(self):
        path = str(self.path)

        # Load unchanged to determine if there is an alpha channel.
        unchanged_texture = cv2.imread(path, cv2.IMREAD_UNCHANGED)

        if unchanged_texture.shape[-1] == 4:
            # `copy` because we want `unchanged_texture` to be garbage collected.
            self.texture_alpha = unchanged_texture[:, :, -1].copy()
        else:
            self.texture_alpha = None

        # Reload in BGR format.
        bgr_texture = cv2.imread(path, cv2.IMREAD_COLOR)
        if self.is_grayscale:
            grayscale = cv2.cvtColor(bgr_texture, cv2.COLOR_BGR2GRAY)
            self.texture = cv2.cvtColor(grayscale, cv2.COLOR_GRAY2RGB)
        else:
            self.texture = cv2.cvtColor(bgr_texture, cv2.COLOR_BGR2RGB)

        self.resize(self.dim)

    def resize(self, dim):
        """
        Resize image.
        """
        h, w = dim
        TEXTURE_DIM = w, 2 * h
        self.canvas = np.full(dim, self.default_char, dtype=object)
        self.colors = np.zeros((h, w, 6), dtype=np.uint8)

        if self.texture_alpha is not None and self.is_transparent:
            alpha = cv2.resize(self.texture_alpha, TEXTURE_DIM) / 255
            self.alpha = np.zeros((h, w, 2), dtype=np.float16)
            self.alpha[..., 0] = alpha[::2]
            self.alpha[..., 1] = alpha[1::2]
        else:
            self.alpha = None

        texture =  cv2.resize(self.texture, TEXTURE_DIM)
        self.colors[..., :3] = texture[::2]
        self.colors[..., 3:] = texture[1::2]

        for child in self.children:
            child.update_geometry()

    def render(self, canvas_view, colors_view, rect):
        """
        Paint region given by rect into canvas_view and colors_view.
        """
        t, l, b, r, h, w = rect

        index_rect = slice(t, b), slice(l, r)
        canvas_view[:] = self.canvas[index_rect]

        alpha = self.alpha
        if alpha is None:
            colors_view[:] = self.colors[index_rect]
        else:
            # RGBA on rgb == rgb + (RGB - rgb) * A1
            colors = self.colors[index_rect]
            buffer = np.zeros((h, w, 3), dtype=np.float16)

            fg = colors_view[..., :3]
            np.subtract(colors[..., :3], fg, out=buffer, dtype=np.float16)
            np.multiply(buffer, alpha[..., 0, None], out=buffer)
            np.add(buffer, fg, out=fg, casting="unsafe")

            bg = colors_view[..., 3:]
            np.subtract(colors[..., 3:], bg, out=buffer, dtype=np.float16)
            np.multiply(buffer, alpha[..., 1, None], out=buffer)
            np.add(buffer, bg, out=bg, casting="unsafe")

        overlap = self._overlapping_region

        for child in self.children:
            if region := overlap(rect, child):
                dest_slice, child_rect = region
                child.render(canvas_view[dest_slice], colors_view[dest_slice], child_rect)
