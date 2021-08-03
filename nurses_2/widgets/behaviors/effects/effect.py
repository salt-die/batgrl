from abc import ABC, abstractmethod

from ...widget_data_structures import Rect


class Effect(ABC):
    """
    Effects are behaviors that modify how a widget and its children are rendered.
    Effects should be inherited in the reverse order that they are applied, e.g.,
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

        self.apply_effect(canvas_view, colors_view, rect)

    @abstractmethod
    def apply_effect(self, canvas_view, colors_view, rect: Rect):
        """
        Apply an effect to the rendered views of a widget.
        """
