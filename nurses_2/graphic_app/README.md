GraphicApps paint only one character, the upper-half block. GraphicWidgets don't carry character data,
only color information. It's not clear that any optimizations gained from this are worth a separate
module. Consider this module experimental for now.

GraphicWidgets' color arrays have a (h, w, 2, 3) shape instead of a (h, w, 6) shape of Widget color arrays.
This is so multiplication will be compatible with their `alpha_channels` array (of shape (h, w, 2, 1)).

The base GraphicWidget is very close to an Image widget from outside this module.
