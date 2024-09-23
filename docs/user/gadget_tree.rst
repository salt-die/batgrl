.. _gadget_tree:

###############
The Gadget Tree
###############

Gadgets in your app are organized in a tree.  The root of the tree is a special gadget that always
matches your terminal's size. The root has child gadgets and these gadget can have children
of their own. Gadgets that are part of the gadget tree can access the root gadget with the `root`
property.

A gadget has the following methods that modify the gadget tree:

* `add_gadget()`: Add a gadget as a child.
* `add_gadgets()`: Add an iterable of gadgets or add multiple gadgets as children.
* `remove_gadget()`: Remove a child gadget.
* `prolicide()`: Recursively remove all child gadgets.
* `destroy()`: Remove a gadget from its parent and recursively remove all its children.

When a gadget is added to the gadget tree (there must be a path from the gadget to the root), the
`on_add()` method is called. Similarly, when a gadget is removed from the gadget tree, `on_remove()` is called.

You can iterate over all descendents of a gadget with `walk()` (preorder traversal) or `walk_reverse()` (reverse 
postorder traversal) or iterate over all ancestors of a gadget with `ancestors()`.

Rendering
---------
The gadgets are drawn based on their position in the gadget tree. Children are drawn on top of their parents and
in the order of `children`.  The `pull_to_front()` method will move a gadget to the end of `children` making sure
it is drawn after all its siblings.

Dispatching
-----------
Input is dispatched across the entire gadget tree. If a gadget has children, events will first
be dispatched to its children in reversed order. For the following tree::

                             Root
                             /  \
                            A    B
                           / \   |
                          a   b  c

dispatching would visit *c B b a A Root*. If any gadget returns True from its event handler,
the dispatching will stop. The event handlers are `on_key()`, `on_mouse()`, `on_paste()`, and `on_terminal_focus()`.
They handle key events, mouse events, paste events, and focus events respectively. The structure of the different
input events can be found `here <https://github.com/salt-die/batgrl/blob/main/batgrl/terminal/events.py>`_.
