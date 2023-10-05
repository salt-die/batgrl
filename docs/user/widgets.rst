#######
Widgets
#######

Widgets are the building blocks of your app.  All widgets have a size, position, and
:ref:`children <widget_tree>`. The base widget has a `background_color_pair` and a `background_char`
so you can fill the area of the screen the widget is located in with some character or color.

For more interesting displays, there are `Text` and `Graphics`. Underlying both
these classes are NumPy arrays that represent the content of the widget. The `Text` has
a `canvas` array of characters and a `colors` array of color pairs. The `Graphics` widget
has a rgba `texture` array that is twice the height of the widget. Painting any image on screen
is as simple as copying the image into the `texture` array.  Layered graphic widgets do proper
alpha compositing.

Size and Pos Hints
------------------
If a widget has a non-None size hint, it will have a size that is some proportion (given by the hint) of its
parent. If the parent is resized, the widget will update its size to follow the size hint. Similarly, for non-None
position hints, a widget will position itself at some proportion of its parent's size.  Position hints can be
further controlled with the `anchor` key or attribute. The `anchor` determines which point
in the widget is aligned with the position hint (the default is `"center"`).

Responding to Events
--------------------
Each widget has `on_key`, `on_mouse`, and `on_paste` methods to enable responding to
input events. Input events are dispatched to every widget until one of these methods return
True to signal that the event was handled.

In addition to input events, widgets may want to update when other widget properties change.
Widgets have a `subscribe` method that notifies them of property changes and allows you to
register any callback when said properties change.

Collisions
----------
To determine if a point is within a widget's bounds you can use `collides_point`.
Related, `to_local` converts a point to a widget's local coordinates (which can be used
to determine how close the point is to the widget). Use `collides_widget` to check if a
widget overlaps another.
