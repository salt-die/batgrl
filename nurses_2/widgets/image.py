from pathlib import Path

import cv2
import numpy as np

from .widget import Widget, overlapping_region
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
    alpha : float, default: 1.0
        If image has an alpha channel, it will be multiplied by `alpha`.
        Otherwise, `alpha` is default value for this will be the default alpha.
    """
    is_grayscale = ReloadTextureProperty()
    path = ReloadTextureProperty()
    alpha = ReloadTextureProperty()

    def __init__(self,
        *args,
        path: Path,
        is_grayscale=False,
        alpha=1.0,
        default_char="▀",
        is_transparent=True,
        **kwargs
    ):
        kwargs.pop('default_color', None)

        super().__init__(
            *args,
            default_char=default_char,
            default_color=BLACK_ON_BLACK,
            is_transparent=is_transparent,
            **kwargs,
        )

        self._path = path
        self._is_grayscale = is_grayscale
        self._alpha = alpha

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

        if self.texture_alpha is not None:
            texture_alpha = cv2.resize(self.texture_alpha, TEXTURE_DIM) / 255 * self.alpha
            self.alpha_channels = np.dstack((texture_alpha[::2], texture_alpha[1::2]))[..., None]
        else:
            self.alpha_channels = np.full((h, w, 2, 1), self.alpha, dtype=np.float16)

        texture =  cv2.resize(self.texture, TEXTURE_DIM)
        self.colors = np.dstack((texture[::2], texture[1::2]))

        for child in self.children:
            child.update_geometry()

    def render(self, canvas_view, colors_view, rect):
        """
        Paint region given by rect into canvas_view and colors_view.
        """
        t, l, b, r, h, w = rect

        index_rect = slice(t, b), slice(l, r)
        canvas_view[:] = self.canvas[index_rect]

        if not self.is_transparent:
            colors_view[:] = self.colors[index_rect]
        else:
            buffer = np.zeros((h, w, 6), dtype=np.float16)
            alpha_buffer = buffer.reshape((h, w, 2, 3))

            # RGBA on rgb == rgb + (RGB - rgb) * A1
            np.subtract(self.colors[index_rect], colors_view, out=buffer, dtype=np.float16)
            np.multiply(alpha_buffer, self.alpha_channels, out=alpha_buffer)
            np.add(buffer, colors_view, out=colors_view, casting="unsafe")

        overlap = overlapping_region

        for child in self.children:
            if region := overlap(rect, child):
                dest_slice, child_rect = region
                child.render(canvas_view[dest_slice], colors_view[dest_slice], child_rect)
