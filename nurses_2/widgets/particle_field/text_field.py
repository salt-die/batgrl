"""
A text particle field.

A particle field specializes in handling many single "pixel" children.
"""
import numpy as np

from ..widget import Widget

__all__ = "TextParticleField",


class TextParticleField(Widget):
    """
    A text particle field.

    Parameters
    ----------
    particle_positions : np.ndarray | None=None, default: None
        Positions of particles. Expect int array with shape `N, 2`.
    particle_chars : np.ndarray | None=None, default: None
        Characters of alphas. Expect object array with shape `N,`.
    particle_color_pairs : np.ndarray | None=None, default: None
        Color pairs of particles. Expect uint8 array with shape `N, 6`.
    particle_properties : dict[str, np.ndarray]=None, default: None
        Additional particle properties.
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint, default: SizeHint(None, None)
        Proportion of parent's height and width. Non-None values will have
        precedent over :attr:`size`.
    min_height : int | None, default: None
        Minimum height set due to size_hint. Ignored if corresponding size
        hint is None.
    max_height : int | None, default: None
        Maximum height set due to size_hint. Ignored if corresponding size
        hint is None.
    min_width : int | None, default: None
        Minimum width set due to size_hint. Ignored if corresponding size
        hint is None.
    max_width : int | None, default: None
        Maximum width set due to size_hint. Ignored if corresponding size
        hint is None.
    pos_hint : PosHint, default: PosHint(None, None)
        Position as a proportion of parent's height and width. Non-None values
        will have precedent over :attr:`pos`.
    anchor : Anchor, default: Anchor.TOP_LEFT
        The point of the widget attached to :attr:`pos_hint`.
    is_transparent : bool, default: False
        If true, background_char and background_color_pair won't be painted.
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    background_char : str | None, default: None
        The background character of the widget if not `None` and if the widget
        is not transparent.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if not `None` and if the
        widget is not transparent.

    Attributes
    ----------
    nparticles : int
        Number of particles in particle field.
    particle_positions : np.ndarray
        Positions of particles.
    particle_chars : np.ndarray
        Characters of alphas.
    particle_color_pairs : np.ndarray
        Color pairs of particles.
    particle_properties : dict[str, np.ndarray]
        Additional particle properties.
    size : Size
        Size of widget.
    height : int
        Height of widget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of widget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position relative to parent.
    top : int
        Y-coordinate of position.
    y : int
        Y-coordinate of position.
    left : int
        X-coordinate of position.
    x : int
        X-coordinate of position.
    bottom : int
        :attr:`top` + :attr:`height`.
    right : int
        :attr:`left` + :attr:`width`.
    absolute_pos : Point
        Absolute position on screen.
    center : Point
        Center of widget in local coordinates.
    size_hint : SizeHint
        Size as a proportion of parent's size.
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    min_height : int
        Minimum height allowed when using :attr:`size_hint`.
    max_height : int
        Maximum height allowed when using :attr:`size_hint`.
    min_width : int
        Minimum width allowed when using :attr:`size_hint`.
    max_width : int
        Maximum width allowed when using :attr:`size_hint`.
    pos_hint : PosHint
        Position as a proportion of parent's size.
    y_hint : float | None
        Vertical position as a proportion of parent's size.
    x_hint : float | None
        Horizontal position as a proportion of parent's size.
    anchor : Anchor
        Determines which point is attached to :attr:`pos_hint`.
    background_char : str | None
        Background character.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Widget | None
        Parent widget.
    children : list[Widget]
        Children widgets.
    is_transparent : bool
        True if widget is transparent.
    is_visible : bool
        True if widget is visible.
    is_enabled : bool
        True if widget is enabled.
    root : Widget | None
        If widget is in widget tree, return the root widget.
    app : App
        The running app.

    Methods
    -------
    on_size:
        Called when widget is resized.
    update_geometry:
        Called when parent is resized. Applies size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point is within widget's bounding box.
    collides_widget:
        True if other is within widget's bounding box.
    add_widget:
        Add a child widget.
    add_widgets:
        Add multiple child widgets.
    remove_widget:
        Remove a child widget.
    pull_to_front:
        Move to end of widget stack so widget is drawn last.
    walk_from_root:
        Yield all descendents of root widget.
    walk:
        Yield all descendents (or ancestors if `reverse` is True).
    subscribe:
        Subscribe to a widget property.
    unsubscribe:
        Unsubscribe to a widget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    on_add:
        Called after a widget is added to widget tree.
    on_remove:
        Called before widget is removed from widget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this widget and all descendents.
    """
    def __init__(
        self,
        particle_positions: np.ndarray | None=None,
        particle_chars: np.ndarray | None=None,
        particle_color_pairs: np.ndarray | None=None,
        particle_properties: dict[str, np.ndarray]=None,
        **kwargs
    ):
        super().__init__(**kwargs)

        if particle_positions is None:
            self.particle_positions = np.zeros((0, 2), dtype=int)
        else:
            self.particle_positions = particle_positions

        if particle_chars is None:
            self.particle_chars = np.full(len(self.particle_positions), " ", dtype=object)
        else:
            self.particle_chars = particle_chars

        if particle_color_pairs is None:
            self.particle_color_pairs = np.zeros((len(self.particle_positions), 6), dtype=np.uint8)
        else:
            self.particle_color_pairs = particle_color_pairs

        if particle_properties is None:
            self.particle_properties = {}
        else:
            self.particle_properties = particle_properties

    @property
    def nparticles(self) -> int:
        """
        Number of particles in particle field.
        """
        return len(self.particle_positions)

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        vert_slice, hori_slice = source
        t = vert_slice.start
        h = vert_slice.stop - t
        l = hori_slice.start
        w = hori_slice.stop - l

        pos = self.particle_positions - (t, l)
        where_inbounds = np.nonzero((((0, 0) <= pos) & (pos < (h, w))).all(axis=1))
        local_ys, local_xs = pos[where_inbounds].T

        canvas_view[local_ys, local_xs] = self.particle_chars[where_inbounds]
        colors_view[local_ys, local_xs] = self.particle_color_pairs[where_inbounds]

        self.render_children(source, canvas_view, colors_view)
