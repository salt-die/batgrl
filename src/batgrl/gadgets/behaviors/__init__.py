"""
Inheritable gadget behaviors.

A `Behavior` is an inheritable class that modifies a gadget.

It should be inherited *before* the base gadget, e.g.,::

    class MovableImage(Movable, Image): ...

Where `Movable` is a `Behavior` and `Image` is the base gadget. In this case,
`MovableImage` is now an `Image` that can be moved around the terminal by clicking and
dragging.
"""

from typing import cast

from ..gadget import Gadget

Behavior = cast(type[Gadget], object)
"""
A `Behavior` is an inheritable class that modifies a gadget.

It should be inherited *before* the base gadget, e.g.,::

    class MovableImage(Movable, Image): ...

Where `Movable` is a `Behavior` and `Image` is the base gadget. In this case,
`MovableImage` is now an `Image` that can be moved around the terminal by clicking and
dragging.
"""
