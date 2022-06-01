"""
A restrictive precise angle shadowcaster widget.
"""
from .shadow_caster import AGRAY, ShadowCaster
from .shadow_caster_data_structures import (
    Camera,
    Coordinates,
    LightIntensity,
    LightSource,
    Point,
    Restrictiveness,
)

__all__ = (
    "AGRAY",
    "Camera",
    "Coordinates",
    "LightIntensity",
    "LightSource",
    "Point",
    "Restrictiveness",
    "ShadowCaster",
)