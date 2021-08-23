# nurses_2 - terminal graphics

This is a widget and async-centric library for creating graphical applications in the terminal. Support only for vt-100 enabled, truecolor terminals.

How it works
------------
A widget's visual state is stored in numpy arrays. Because numpy arrays follow the buffer protocol, views of these arrays can be passed to other widgets without copying any data. To render the current screen, the root widget, for each of its children, finds the rectangular region of the screen a child overlaps and passes a view of this region to that child. The child is then responsible for rendering into this view. It may continue the process, passing
overlapping region views of the view to *its* children as well.

Input dispatching is similar. Starting with the root widget all input is recursively dispatched to the entire widget tree until a input handler (`on_press` or `on_click` methods) returns `True`.  `True` indicates the input was handled and stops the dispatching.

Getting Started
---------------
To create a nurses_2 app, inherit the `App` class and implement the `on_start` asynchronous method. The root widget of the app is named `root` and widgets can be added to it with `root.add_widget` or `root.add_widgets`. One can find examples in the `/examples/` directory. Once implemented, the app can be run by instantiating it and calling the `run` method.

# /examples/exploding_logo.py

![Exploding logo example](preview_images/exploding_logo.gif)

# /examples/exploding_logo_redux.py

![Exploding logo example 2](preview_images/exploding_logo_redux.gif)

# /examples/sandbox

![Sandbox demonstration](preview_images/sandbox_demonstration.gif)

# /examples/raycaster

![Raycaster demonstration](preview_images/raycaster_demonstration.gif)

# /examples/tetris

![Tetris demonstration](preview_images/tetris_demonstration.gif)

# /examples/rubiks

![Rubik's Cube demonstration](preview_images/rubiks_demonstration.gif)
