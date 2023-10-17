"""
A raycaster gadget.
"""
from dataclasses import dataclass, field
from typing import Literal, Protocol

import numpy as np
from numpy.typing import NDArray

from ..colors import BLACK, TRANSPARENT, AColor, Color
from .graphics import (
    Char,
    Graphics,
    Interpolation,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    clamp,
)

__all__ = [
    "Camera",
    "Interpolation",
    "Map",
    "Point",
    "PosHint",
    "PosHintDict",
    "Raycaster",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "Sprite",
    "Texture",
]


@dataclass(slots=True)
class Sprite:
    """
    A sprite for a raycaster.
    """

    pos: tuple[float, float]
    """Position of sprite on map."""

    texture_idx: int
    """Index of sprite texture."""

    _relative: NDArray[np.float64] = field(
        init=False, default_factory=lambda: np.zeros(2)
    )

    distance: np.float64 = field(init=False)
    """Distance from camera, set when :attr:`relative` is set."""

    @property
    def relative(self):
        """Vector from camera to sprite, set by the caster."""
        return self._relative

    @relative.setter
    def relative(self, value):
        self._relative = value
        self.distance = value @ value

    def __lt__(self, other):
        """
        Sprites are ordered by their distance to camera.
        """
        return self.distance > other.distance


class Map(Protocol):
    """
    Map with non-zero entries indicating walls.

    Notes
    -----
    Wall value `n` will have nth texture in raycaster's texture array, e.g.,
    `wall_textures[n - 1]`.
    """

    ndim: Literal[2]

    def __getitem__(self, y, x):
        """
        Supports numpy indexing. Returns a non-negative integer.
        """


class Camera(Protocol):
    """
    A camera view.

    Notes
    -----
    The renderer expects both `pos` and `plane` be numpy arrays with dtype
    `float` and shapes (2,) and (2, 2) respectively.
    """

    pos: NDArray[np.float64]
    """Position of camera. Array should have shape `(2,)`."""
    plane: NDArray[np.float64]
    """Rotation of camera. Array should have shape `(2, 2)`."""


class Texture(Protocol):
    """
    A texture. Typically a numpy array.

    Notes
    -----
    This protocol is provided to allow for, say, animated textures. The raycaster
    will function as long as `shape` and `__getitem__` work as expected.
    """

    shape: tuple[int, int, Literal[4]]  # (height, width, RGBA)

    def __getitem__(self, key):
        """
        Supports numpy indexing. Return arrays or views with dtype `np.uint8`.
        """


class Raycaster(Graphics):
    """
    A raycaster gadget.

    Parameters
    ----------
    map : Map
        An array-like with non-zero entries n indicating walls with texture
        `wall_textures[n - 1]`.
    camera : Camera
        A view in the map.
    wall_textures : List[Texture]
        Textures for walls.
    light_wall_textures : list[Texture] | None, default: None
        If provided, walls north/south face will use textures in
        :attr:`light_wall_textures` instead of :attr:`wall_textures`.
    sprites : list[Sprite] | None, default: None
        List of sprites.
    sprite_textures : list[Texture] | None, default: None
        Textures for sprites.
    ceiling : Texture | None, default: None
        Ceiling texture.
    ceiling_color : Color, default: BLACK
        Color of ceiling if no ceiling texture.
    floor : Texture | None, default: None
        Floor texture.
    floor_color : Color, default: BLACK
        Color of floor if no floor texture.
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        If gadget is transparent, the alpha channel of the underlying texture will be
        multiplied by this value. (0 <= alpha <= 1.0)
    interpolation : Interpolation, default: "linear"
        Interpolation used when gadget is resized.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: True
        A transparent gadget allows regions beneath it to be painted. Additionally,
        non-transparent graphic gadgets are not alpha composited.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    map : Map
        An array-like with non-zero entries n indicating walls with texture
        `wall_textures[n - 1]`.
    camera : Camera
        A view in the map.
    wall_textures : List[Texture]
        East/west-faced walls' textures.
    light_wall_textures : list[Texture]
        North/south-faced walls' textures.
    sprites : list[Sprite]
        List of sprites.
    sprite_textures : list[Texture]
        Textures for sprites.
    ceiling : Texture | None
        Ceiling texture.
    ceiling_color : Color
        Color of ceiling if no ceiling texture.
    floor : Texture
        Floor texture.
    floor_color : Color
        Color of floor if no floor texture.
    texture : NDArray[np.uint8]
        uint8 RGBA color array.
    default_color : AColor
        Default texture color.
    alpha : float
        Transparency of gadget if :attr:`is_transparent` is true.
    interpolation : Interpolation
        Interpolation used when gadget is resized.
    size : Size
        Size of gadget.
    height : int
        Height of gadget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of gadget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of gadget.
    y : int
        Y-coordinate of top of gadget.
    left : int
        X-coordinate of left side of gadget.
    x : int
        X-coordinate of left side of gadget.
    bottom : int
        Y-coordinate of bottom of gadget.
    right : int
        X-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    parent: GadgetBase | None
        Parent gadget.
    children : list[GadgetBase]
        Children gadgets.
    is_transparent : bool
        True if gadget is transparent.
    is_visible : bool
        True if gadget is visible.
    is_enabled : bool
        True if gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    to_png(path):
        Write :attr:`texture` to provided path as a `png` image.
    on_size():
        Called when gadget is resized.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        True if point collides with an uncovered portion of gadget.
    collides_gadget(other):
        True if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\\*gadgets):
        Add multiple child gadgets.
    remove_gadget(gadget):
        Remove a child gadget.
    pull_to_front():
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root():
        Yield all descendents of the root gadget (preorder traversal).
    walk():
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse():
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors():
        Yield all ancestors of this gadget.
    subscribe(source, attr, action):
        Subscribe to a gadget property.
    unsubscribe(source, attr):
        Unsubscribe to a gadget property.
    on_key(key_event):
        Handle key press event.
    on_mouse(mouse_event):
        Handle mouse event.
    on_paste(paste_event):
        Handle paste event.
    tween(...):
        Sequentially update gadget properties over time.
    on_add():
        Called after a gadget is added to gadget tree.
    on_remove():
        Called before gadget is removed from gadget tree.
    prolicide():
        Recursively remove all children.
    destroy():
        Destroy this gadget and all descendents.
    """

    HOPS = 20  # How far rays are cast.

    def __init__(
        self,
        *,
        map: Map,
        camera: Camera,
        wall_textures: list[Texture] | None,
        light_wall_textures: list[Texture] | None = None,
        sprites: list[Sprite] | None = None,
        sprite_textures: list[Texture] | None = None,
        ceiling: Texture | None = None,
        ceiling_color: Color = BLACK,
        floor: Texture | None = None,
        floor_color: Color = BLACK,
        is_transparent: bool = True,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            is_transparent=is_transparent,
            default_color=default_color,
            alpha=alpha,
            interpolation=interpolation,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self.map = map
        self.camera = camera
        self.wall_textures = wall_textures
        self.light_wall_textures = light_wall_textures or wall_textures
        self.sprites = sprites
        self.sprite_textures = sprite_textures
        self.ceiling = ceiling
        self.ceiling_color = ceiling_color
        self.floor = floor
        self.floor_color = floor_color

        # Buffers
        self._pos_int = np.zeros((2,), dtype=int)
        self._pos_frac = np.zeros((2,), dtype=float)
        self._floor_pos = np.zeros((2,), dtype=float)

        self.on_size()

    def on_size(self):
        h, w = self._size

        self.texture = np.zeros((2 * h, w, 4), dtype=np.uint8)

        # Precalculate angle of rays cast.
        self._ray_angles = angles = np.ones((w, 2), dtype=float)
        angles[:, 1] = np.linspace(-1, 1, w)

        # Precalculate distances for ceiling and floor textures
        self._distances = distances = np.linspace(
            1e-10, h, num=h, endpoint=False, dtype=float
        )
        np.divide(h, distances, out=distances, dtype=float)

        # Buffers
        self._rotated_angles = np.zeros_like(angles)
        self._deltas = np.zeros_like(angles)
        self._sides = np.zeros_like(angles)
        self._steps = np.zeros_like(angles, dtype=int)
        self._weights = weights = np.zeros((h, 2), dtype=float)
        self._tex_frac = np.zeros_like(weights)
        self._tex_frac_2 = np.zeros_like(weights)
        self._tex_int = np.zeros_like(weights, dtype=int)
        self._column_distances = np.zeros((w,), dtype=float)

    def cast_ray(self, column):
        """
        Cast a ray for a given column of the screen.
        """
        camera = self.camera
        camera_pos = camera.pos
        map = self.map

        ray_pos = self._pos_int
        ray_pos[:] = camera_pos

        ray_angle = self._rotated_angles[column]
        delta = self._deltas[column]
        step = self._steps[column]
        sides = self._sides[column]

        # Casting #
        for _ in range(self.HOPS):
            side = 0 if sides[0] < sides[1] else 1
            sides[side] += delta[side]
            ray_pos[side] += step[side]

            if texture_index := map[tuple(ray_pos)]:
                # Distance from wall to camera plane.
                # Note that distance of wall to camera is not used
                # as it would result in a "fish-eye" effect.
                distance = (
                    ray_pos[side] - camera_pos[side] + (0 if step[side] == 1 else 1)
                ) / ray_angle[side]
                break

        else:  # No walls in range.
            distance = 1000  # 1000 == infinity, roughly

        self._column_distances[column] = distance

        # Rendering #
        texture = self.texture[:, ::-1]
        height = texture.shape[0]

        column_height = (
            int(height / distance) if distance else 1000
        )  # 1000 == infinity, roughly

        # Start and end y-coordinates of column.
        half_height = height >> 1
        half_column = column_height >> 1
        if half_column > half_height:
            half_column = half_height

        start = half_height - half_column
        end = half_height + half_column

        wall_texture = (self.wall_textures if side else self.light_wall_textures)[
            texture_index - 1
        ]
        tex_h, tex_w, _ = wall_texture.shape

        # Exactly where wall was hit by ray as a percentage of its width.
        wall_x = (camera_pos[1 - side] + distance * ray_angle[1 - side]) % 1

        # Use above percentage to grab the column of the texture we need.
        tex_x = int(wall_x * tex_w)
        if (-1 if side == 1 else 1) * ray_angle[side] < 0:  # Sign correction.
            tex_x = tex_w - tex_x - 1

        # Interpolate texture onto column
        drawn_height = end - start
        offset = (column_height - drawn_height) / 2
        ratio = tex_h / column_height
        texture_start = offset * ratio
        texture_end = (offset + drawn_height) * ratio
        tex_ys = np.linspace(
            texture_start, texture_end, num=drawn_height, endpoint=False, dtype=int
        )
        texture_column = wall_texture[tex_ys, tex_x].astype(float)

        # Darken colors further away.
        texture_column *= np.e ** (-distance * 0.05)
        np.clip(texture_column, 0, 255, out=texture_column, casting="unsafe")

        # Paint column.
        texture[start:end, column] = texture_column

        # Render floor and ceiling.
        ceiling = self.ceiling
        floor = self.floor

        if ceiling is None and floor is None:
            texture[:start, column] = self.ceiling_color
            texture[end:, column] = self.floor_color
            return

        # Buffer views
        floor_pos = self._floor_pos
        weights = self._weights[half_column:]
        tex_frac = self._tex_frac[half_column:]
        tex_frac_2 = self._tex_frac_2[half_column:]
        tex_int = self._tex_int[half_column:]

        # Floor position
        if side == 0:
            facing = float(ray_angle[0] < 0), wall_x
        else:
            facing = wall_x, float(ray_angle[1] < 0)
        np.add(ray_pos, facing, out=floor_pos)

        # Horizontal distances of floor / ceiling
        np.divide(self._distances[half_column:], distance, out=weights[:, 0])
        weights[:, 1] = weights[:, 0]

        # Texture coordinates
        # (weights * floor_pos + (1 - weights) * camera_pos) % 1
        np.multiply(weights, floor_pos, out=tex_frac)
        np.subtract(1.0, weights, out=weights)
        np.multiply(weights, camera_pos, out=tex_frac_2)
        np.add(tex_frac, tex_frac_2, out=tex_frac)
        np.mod(tex_frac, 1.0, out=tex_frac)

        # Paint ceiling
        if ceiling is None:
            texture[:start, column] = self.ceiling_color
        else:
            # Note reversed order of texture coordinates from floor
            np.multiply(
                ceiling.shape[:2], tex_frac[::-1], out=tex_int, casting="unsafe"
            )
            texture[:start, column] = ceiling[tex_int[:, 0], tex_int[:, 1]]

        # Paint floor
        if floor is None:
            texture[end:, column] = self.floor_color
        else:
            np.multiply(floor.shape[:2], tex_frac, out=tex_int, casting="unsafe")
            texture[end:, column] = floor[tex_int[:, 0], tex_int[:, 1]]

    def cast_sprites(self):
        """
        Render all sprites.
        """
        texture = self.texture[:, ::-1]
        h, w, _ = texture.shape
        half_w = w / 2

        camera = self.camera
        camera_pos = camera.pos
        sprites = self.sprites
        sprite_textures = self.sprite_textures
        column_distances = self._column_distances

        for sprite in sprites:
            sprite.relative = camera_pos - sprite.pos

        sprites.sort()

        # Camera Inverse used to calculate transformed position of sprites.
        cam_inv = np.linalg.inv(-camera.plane)

        # Draw each sprite from furthest to closest.
        for sprite in sprites:
            # Transformed position of sprites due to camera position
            y, x = sprite.relative @ cam_inv

            if y <= 0:
                # Sprite is behind camera, don't draw it.
                continue

            # Sprite x-position on screen
            sprite_x = int(half_w * (1 + x / y))

            sprite_height = int(h / y)
            sprite_width = int(half_w / y)
            if sprite_height == 0 or sprite_width == 0:
                # Sprite too small.
                continue

            start_x = clamp(sprite_x - sprite_width // 2, 0, w)
            end_x = clamp(sprite_x + sprite_width // 2, 0, w)
            columns = np.arange(start_x, end_x)

            # Remove columns that are behind walls or off-screen; buffered version of:
            #     (0 <= columns) & (columns <= w) & (y <= column_distances[columns])
            _where_buffer_1 = 0 <= columns
            _where_buffer_2 = columns <= w
            np.logical_and(_where_buffer_1, _where_buffer_2, out=_where_buffer_1)
            np.less_equal(y, column_distances[columns], out=_where_buffer_2)
            np.logical_and(_where_buffer_1, _where_buffer_2, out=_where_buffer_1)
            columns = columns[_where_buffer_1]

            start_y = clamp(int((h - sprite_height) / 2), 0, h)
            end_y = clamp(int((h + sprite_height) / 2), 0, h)
            rows = np.arange(start_y, end_y, dtype=float)

            sprite_tex = sprite_textures[sprite.texture_idx]
            tex_height, tex_width, _ = sprite_tex.shape

            clip_y = (sprite_height - h) / 2
            np.add(rows, clip_y, out=rows)
            np.multiply(rows, tex_height / sprite_height, out=rows)
            np.clip(rows, 0, None, out=rows)

            clip_x = sprite_x - sprite_width / 2
            tex_xs = columns - clip_x
            np.multiply(tex_xs, tex_width, out=tex_xs)
            np.divide(tex_xs, sprite_width, out=tex_xs)

            sprite_rect = sprite_tex[rows.astype(int)][:, tex_xs.astype(int)].astype(
                float
            )
            sprite_rgb = sprite_rect[..., :3]
            tex_rect = texture[start_y:end_y, columns, :3]

            np.subtract(sprite_rgb, tex_rect, out=sprite_rgb)
            np.multiply(sprite_rgb, sprite_rect[..., 3, None], out=sprite_rgb)
            np.divide(sprite_rgb, 255, out=sprite_rgb)
            np.add(sprite_rgb, tex_rect, out=sprite_rgb)

            texture[start_y:end_y, columns, :3] = sprite_rgb

    def render(self, canvas_view: NDArray[Char], colors_view: NDArray[np.uint8]):
        camera = self.camera
        pos_frac = self._pos_frac
        rotated_angles = self._rotated_angles
        deltas = self._deltas
        steps = self._steps
        sides = self._sides
        multiply = np.multiply
        cast_ray = self.cast_ray

        # Early calculations on rays can be vectorized:
        np.dot(self._ray_angles, camera.plane, out=rotated_angles)

        with np.errstate(divide="ignore"):
            np.true_divide(1.0, rotated_angles, out=deltas)
        np.absolute(deltas, out=deltas)

        np.sign(rotated_angles, out=steps, casting="unsafe")

        np.heaviside(steps, 1.0, out=sides)
        np.mod(camera.pos, 1.0, out=pos_frac)
        np.subtract(sides, pos_frac, out=sides)
        multiply(sides, steps, out=sides)
        multiply(sides, deltas, out=sides)

        for column in range(self.width):
            cast_ray(column)

        self.cast_sprites()

        super().render(canvas_view, colors_view)
