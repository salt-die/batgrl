#######
Gadgets
#######

Gadgets are the building blocks of your app.  All gadgets have a size, position,
and :ref:`children <gadget_tree>`. Additionally, gadgets have attributes `is_transparent`,
`is_visible` and `is_enabled` that determine whether the gadget is transparent (whether gadgets
beneath are rendered), whether the gadget is rendered, or whether input events are dispatched,
respectively.

The base gadget is little more than a container for other gadgets. Some other more interesting
gadgets include:
* `Pane`, a gadget with a background color. An `alpha` attribute can modify its transparency.
* `Graphics`, a gadget for arbitrary RGBA textures.
* `Text`, the most general gadget. Its state is an array of cells where each cell carries
attributes a terminal character can have such as its character, whether it's bold, or the
color of its foreground.

Size and Pos Hints
------------------
If a gadget has a non-None size hint, it will have a size that is some proportion
(given by the hint) of its parent. If the parent is resized, the gadget will update its
size to follow the size hint. Similarly, for non-None position hints, a gadget will position
itself at some proportion of its parent's size.  Position hints can be further controlled
with the `anchor` which determines which point in the gadget is aligned with the position hint
(the default is `"center"`).

Responding to Events
--------------------
Each gadget has `on_key()`, `on_mouse()`, and `on_paste()` methods to enable responding to input
events. Input events are dispatched to every gadget until one of these methods return True to
signal that the event was handled.


Collisions
----------
`collides_point()` will determina if a point is within a gadget's visible region. `to_local()`
converts a point from absolute coordinates to the gadget's local coordinates. `collides_gadget()`
can determine if one gadget overlaps another.
