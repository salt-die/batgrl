"""A raycaster gadget."""

from dataclasses import dataclass
from typing import Literal, Protocol

import numpy as np
from numpy.typing import NDArray

from ..colors import BLACK, TRANSPARENT, AColor, Color
from .graphics import (
    Cell,
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
from .texture_tools import _composite

__all__ = ["Raycaster", "Sprite", "Camera", "Texture", "Point", "Size"]


@dataclass
class Sprite:
    """A sprite for a raycaster."""

    pos: tuple[float, float]
    """Position of sprite on map."""
    texture_idx: int
    """Index of sprite texture."""

    def __post_init__(self):
        self.relative: NDArray[np.float64] = np.zeros(2)

    @property
    def relative(self) -> NDArray[np.float64]:
        """Vector from camera to sprite."""
        return self._relative

    @relative.setter
    def relative(self, relative):
        self._relative = relative
        self.distance = relative @ relative

    def __lt__(self, other):
        """Sprites are ordered by their distance to camera."""
        return self.distance > other.distance


class Camera:
    """
    A raycaster camera.

    Parameters
    ----------
    pos : tuple[float, float], default: (0.0, 0.0)
        Position of camera on the map.
    theta : float, default: 0.0
        Direction of camera in radians.
    fov : float, default: 0.66
        Field of view of camera.

    Attributes
    ----------
    pos : tuple[float, float]
        Position of camera on the map.
    theta : float
        Direction of camera in radians.
    fov : float
        Field of view of camera.

    Methods
    -------
    rotation_matrix(theta)
        Return a 2-D rotation matrix from a given angle.
    rotate(theta)
        Rotate camera `theta` radians in-place.
    """

    def __init__(
        self,
        pos: tuple[float, float] = (0.0, 0.0),
        theta: float = 0.0,
        fov: float = 0.66,
    ):
        self.pos = np.array(pos, float)
        self._build_plane(theta, fov)

    @staticmethod
    def rotation_matrix(theta: float) -> NDArray[np.float32]:
        """Return a 2-D rotation matrix from a given angle."""
        x = np.cos(theta)
        y = np.sin(theta)
        return np.array([[x, y], [-y, x]], float)

    def _build_plane(self, theta: float, fov: float) -> NDArray[np.float64]:
        initial_plane = np.array([[1.001, 0.001], [0.0, fov]], float)
        self._plane = initial_plane @ self.rotation_matrix(theta)

    @property
    def theta(self) -> float:
        """Direction of camera in radians."""
        x2, x1 = self._plane[0]
        return np.arctan2(x1, x2)

    @theta.setter
    def theta(self, theta: float):
        self._build_plane(theta, self.fov)

    @property
    def fov(self) -> float:
        """Field of view of camera."""
        return (self._plane[1] ** 2).sum() ** 0.5

    @fov.setter
    def fov(self, fov: float):
        self._build_plane(self.theta, fov)

    def rotate(self, theta: float):
        """Rotate camera `theta` radians."""
        self._plane = self._plane @ self.rotation_matrix(theta)


class Texture(Protocol):
    """
    A texture. Typically a numpy array.

    Notes
    -----
    This protocol is provided to allow for, say, animated textures. The raycaster
    will function as long as `shape` and `__getitem__` work as expected.
    """

    shape: tuple[int, int, Literal[4]]  # (height, width, RGBA)

    def __getitem__(self, key) -> NDArray[np.uint8] | np.uint8:
        """Supports numpy indexing."""


class Raycaster(Graphics):
    r"""
    A raycaster gadget.

    Parameters
    ----------
    map : NDArray[np.ushort]
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
        Transparency of gadget.
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
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    map : NDArray[np.ushort]
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
        Transparency of gadget.
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
    parent: Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        Whether gadget is transparent.
    is_visible : bool
        Whether gadget is visible.
    is_enabled : bool
        Whether gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    to_png(path)
        Write :attr:`texture` to provided path as a `png` image.
    clear()
        Fill texture with default color.
    on_size()
        Update gadget after a resize.
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(\*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root()
        Yield all descendents of the root gadget (preorder traversal).
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    on_key(key_event)
        Handle key press event.
    on_mouse(mouse_event)
        Handle mouse event.
    on_paste(paste_event)
        Handle paste event.
    tween(...)
        Sequentially update gadget properties over time.
    on_add()
        Apply size hints and call children's `on_add`.
    on_remove()
        Call children's `on_remove`.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    """

    HOPS = 20  # How far rays are cast.

    def __init__(
        self,
        *,
        map: NDArray[np.ushort],
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
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
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
        """Resize texture array and re-make caster buffers."""
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
        """Cast a ray for a given column of the screen."""
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
        if ceiling is not None:
            # Note reversed order of texture coordinates from floor
            np.multiply(
                ceiling.shape[:2], tex_frac[::-1], out=tex_int, casting="unsafe"
            )
            texture[:start, column] = ceiling[tex_int[:, 0], tex_int[:, 1]]

        # Paint floor
        if floor is not None:
            np.multiply(floor.shape[:2], tex_frac, out=tex_int, casting="unsafe")
            texture[end:, column] = floor[tex_int[:, 0], tex_int[:, 1]]

    def cast_sprites(self):
        """Render all sprites."""
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
        cam_inv = np.linalg.inv(-camera._plane)

        # Draw each sprite from furthest to closest.
        for sprite in sprites:
            # Transformed position of sprites due to camera position.
            y, x = sprite.relative @ cam_inv

            if y <= 0:
                # Sprite is behind camera, don't draw it.
                continue

            # Sprite x-position on screen
            sprite_x = int(half_w * (1 + x / y))
            sprite_height = int(h / y)
            sprite_width = int(half_w / y)
            # Is sprite too small?
            if sprite_height == 0 or sprite_width == 0:
                continue

            start_x = clamp(sprite_x - sprite_width // 2, 0, w)
            end_x = clamp(sprite_x + sprite_width // 2, 0, w)
            columns = np.arange(start_x, end_x)
            columns = columns[y <= column_distances[columns]]

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

            sprite_rect = sprite_tex[rows.astype(int)][:, tex_xs.astype(int)]
            dst = texture[start_y:end_y, columns, :3]
            _composite(dst, sprite_rect[..., :3], sprite_rect[..., 3, None])
            texture[start_y:end_y, columns, :3] = dst

    def _render(self, canvas_view: NDArray[Cell]):
        """Render visible region of gadget."""
        h, w = self.size
        if h == 0 or w == 0:
            return

        # Early calculations on rays can be vectorized:
        np.dot(self._ray_angles, self.camera._plane, out=self._rotated_angles)
        with np.errstate(divide="ignore"):
            np.true_divide(1.0, self._rotated_angles, out=self._deltas)
        np.absolute(self._deltas, out=self._deltas)
        np.sign(self._rotated_angles, out=self._steps, casting="unsafe")
        np.heaviside(self._steps, 1.0, out=self._sides)
        np.mod(self.camera.pos, 1.0, out=self._pos_frac)
        np.subtract(self._sides, self._pos_frac, out=self._sides)
        np.multiply(self._sides, self._steps, out=self._sides)
        np.multiply(self._sides, self._deltas, out=self._sides)

        self.texture[:h, :, :3] = self.ceiling_color
        self.texture[h:, :, :3] = self.floor_color
        self.texture[..., 3] = 255

        for column in range(self.width):
            self.cast_ray(column)

        self.cast_sprites()

        super()._render(canvas_view)
