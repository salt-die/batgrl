"""
Text effects are coroutines that create some effect on a text gadget.

This module is an approximate recreation of some effects from terminaltexteffects.

References
----------
https://github.com/ChrisBuilds/terminaltexteffects

Warnings
--------
Modifying the text size while effect is running will break the effect.
"""

from .beams import beams_effect
from .black_hole import black_hole_effect
from .ring import ring_effect
from .spotlights import spotlights_effect

__all__ = ["beams_effect", "black_hole_effect", "ring_effect", "spotlights_effect"]
