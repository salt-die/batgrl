from ..widget_data_structures import Rect


class Effect:
    """
    Effects are behaviors that modify the rendering of a widget's canvas and colors. Inherit
    effects in the reverse order they should be applied, e.g.,
        ```
        class MyEffectWidget(Effect1, Effect2, Widget):
            ...
        ```
    applies Effect2 then Effect1.
    """
    def render(self, canvas_view, colors_view, rect: Rect):
        """
        Render normally then apply canvas and color effects.
        """
        super().render(canvas_view, colors_view, rect)

        self.apply_canvas_effect(canvas_view, rect)

        self.apply_colors_effect(colors_view, rect)

    def apply_canvas_effect(self, canvas_view, rect: Rect):
        """
        Apply an effect to the rendered canvas of a widget.
        """

    def apply_colors_effect(self, colors_view, rect: Rect):
        """
        Apply an effect to the rendered colors of a widget.
        """
