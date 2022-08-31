"""
Effects are behaviors that modify how a widget and its children are rendered.
"""
from abc import ABC, abstractmethod


class Effect(ABC):
    """
    Effects are behaviors that modify how a widget and its children are rendered.
    Effects should be inherited in the reverse order that they are applied, e.g.,

    .. code-block:: python

        class MyEffectWidget(Effect1, Effect2, TextWidget):
            ...

    applies Effect2 then Effect1.

    Methods
    -------
    apply_effect:
        Apply an effect to the rendered views of a widget.
    """
    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        """
        Render normally then apply canvas and color effects.
        """
        super().render(canvas_view, colors_view, source)

        self.apply_effect(canvas_view, colors_view, source)

    @abstractmethod
    def apply_effect(self, canvas_view, colors_view, source: tuple[slice, slice]):
        """
        Apply an effect to the rendered views of a widget.
        """
