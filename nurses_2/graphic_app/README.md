GraphicApps paint only one character, the upper-half block. GraphicWidgets will be optimized to not
carry character data, only color information. Though it's not clear that any optimizations gained from this
are worth a separate module. Consider this module experimental for now.

GraphicWidgets' color arrays have a (h, w, 2, 3) shape instead of a (h, w, 6) shape of Widget color arrays.
This is so multiplication will be compatible with their `alpha_channel` array (of shape (h, w, 2, 1)).

The base GraphicWidget is very close to an Image widget from outside this module.
