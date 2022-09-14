.. _widget_tree:

###############
The Widget Tree
###############

Widgets your app are organized in a tree.  The root of the tree is a special widget that always
matches your terminal's size. The root has `children` widgets and these widget can have `children`
of their own. Widgets that are part of the widget tree can access the root widget with the `root`
property.

The widget tree can be modified with the following methods:

* `add_widget`: Add a widget as a child.
* `add_widgets`: Add an iterable of widgets or add multiple widgets as children.
* `remove_widget`: Remove a widget from `children`.
* `prolicide`: Recursively remove all child widgets.
* `destroy`: Remove a widget from its parent and recursively remove all its children.

When a widget is added to the widget tree (there must be a path from the widget to the root), the
`on_add` method is called. Similarly, when a widget is removed from the widget tree, `on_remove` is called.

You can visit all widgets in the widget tree with the `walk_from_root` method. Or visit all descendents of a
widget with `walk`.

Rendering
---------
The widgets are drawn based on their position in the widget tree. Children are drawn on top of their parents and
in the order of `children`.  The `pull_to_front` method will move a widget to the end of `children` making sure
it is drawn after all its siblings.

Dispatching
-----------
Input is dispatched across the entire widget tree. If a widget has children, events will first
be dispatched to its children in reversed order. For the following tree::

                             Root
                             /  \
                            A    B
                           / \   |
                          a   b  c

dispatching would visit *c B b a A Root*. If any widget returns True from its event handler,
the dispatching will stop. The event handlers are `on_key`, `on_mouse`, and `on_paste`.
They handle key presses, mouse events, and paste events respectively. The structure of the different
input events can be found `here <https://github.com/salt-die/nurses_2/blob/main/nurses_2/io/input/events.py>`_.
