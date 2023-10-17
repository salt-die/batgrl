#######
Gadgets
#######

Gadgets are the building blocks of your app.  All gadgets have a size, position,
and :ref:`children <gadget_tree>`. The `Gadget` class has a
`background_color_pair` and a `background_char` so you can fill the area of the
screen the gadget is located in with some character or color.

For more interesting displays, there are `Text` and `Graphics`. Underlying both
of these classes are NumPy arrays that represent the content of the gadget. The
`Text` has a `canvas` array of characters and a `colors` array of color pairs.
The `Graphics` gadget has a RGBA `texture` array that is twice the height of the
gadget. Painting any image on screen is as simple as copying the image into the
`texture` array.  Layered graphic gadgets do proper alpha compositing.

Size and Pos Hints
------------------
If a gadget has a non-None size hint, it will have a size that is some
proportion (given by the hint) of its parent. If the parent is resized, the
gadget will update its size to follow the size hint. Similarly, for non-None
position hints, a gadget will position itself at some proportion of its parent's
size.  Position hints can be further controlled with the `anchor` key or
attribute. The `anchor` determines which point in the gadget is aligned with the
position hint (the default is `"center"`).

Responding to Events
--------------------
Each gadget has `on_key`, `on_mouse`, and `on_paste` methods to enable
responding to input events. Input events are dispatched to every gadget until
one of these methods return True to signal that the event was handled.

In addition to input events, gadgets may want to update when other gadget
properties change. Gadgets have a `subscribe` method that allows you to register
a callback when some property changes.

Collisions
----------
To determine if a point is within a gadget's bounds you can use
`collides_point`. Related, `to_local` converts a point to a gadget's local
coordinates (which can be used to determine how close the point is to the
gadget). Use `collides_gadget` to check if a gadget overlaps another.
