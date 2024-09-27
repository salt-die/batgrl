"""A raycaster gadget."""

import numpy as np
from numpy.typing import NDArray

from .raycaster import RaycasterCamera, Sprite
from .text import Cell, Point, PosHint, Size, SizeHint, Text, clamp

__all__ = ["TextRaycaster", "RaycasterCamera", "Sprite", "Point", "Size"]


class TextRaycaster(Text):
    r"""
    A raycaster gadget.

    Parameters
    ----------
    caster_map : NDArray[np.ushort]
        The raycaster map.
    camera : RaycasterCamera
        The raycaster camera.
    wall_textures : List[NDArray[np.uint]]
        Textures for walls.
    sprites : list[Sprite] | None, default: None
        A list of sprites.
    sprite_textures : list[NDArray[np.str\_]] | None, default: None
        Textures for sprites.
    max_hops : int, default: 20
        Determines how far rays are cast.
    ascii_map : str, default: " .,:;<+*LtCa4U80dQM@"
        Dark to bright ascii characters for shading.
    default_cell : NDArray[Cell] | str, default: " "
        Default cell of text canvas.
    alpha : float, default: 1.0
        Transparency of gadget.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
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
    caster_map : NDArray[np.ushort]
        The raycaster map.
    camera : RaycasterCamera
        The raycaster camera.
    wall_textures : List[NDArray[np.uint]]
        Textures for walls.
    sprites : list[Sprite]
        A list of sprites.
    sprite_textures : list[NDArray[np.str\_]]
        Textures for sprites.
    max_hops : int
        Determines how far rays are cast.
    ascii_map : str
        Dark to bright ascii characters for shading.
    canvas : NDArray[Cell]
        The array of characters for the gadget.
    default_cell : NDArray[Cell]
        Default cell of text canvas.
    default_fg_color : Color
        Foreground color of default cell.
    default_bg_color : Color
        Background color of default cell.
    alpha : float
        Transparency of gadget.
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
        y-coordinate of top of gadget.
    y : int
        y-coordinate of top of gadget.
    left : int
        x-coordinate of left side of gadget.
    x : int
        x-coordinate of left side of gadget.
    bottom : int
        y-coordinate of bottom of gadget.
    right : int
        x-coordinate of right side of gadget.
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
    cast_rays()
        Update canvas by casting all rays.
    add_border(style="light", ...)
        Add a border to the gadget.
    add_syntax_highlighting(lexer, style)
        Add syntax highlighting to current text in canvas.
    add_str(str, pos, ...)
        Add a single line of text to the canvas.
    set_text(text, ...)
        Resize gadget to fit text, erase canvas, then fill canvas with text.
    clear()
        Fill canvas with default cell.
    shift(n=1)
        Shift content in canvas up (or down in case of negative `n`).
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(\*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    tween(...)
        Sequentially update gadget properties over time.
    on_size()
        Update gadget after a resize.
    on_transparency()
        Update gadget after transparency is enabled/disabled.
    on_add()
        Update gadget after being added to the gadget tree.
    on_remove()
        Update gadget after being removed from the gadget tree.
    on_key(key_event)
        Handle a key press event.
    on_mouse(mouse_event)
        Handle a mouse event.
    on_paste(paste_event)
        Handle a paste event.
    on_terminal_focus(focus_event)
        Handle a focus event.
    """

    def __init__(
        self,
        *,
        caster_map: NDArray[np.ushort],
        camera: RaycasterCamera,
        wall_textures: list[NDArray[np.uint]] | None,
        sprites: list[Sprite] | None = None,
        sprite_textures: list[NDArray[np.str_]] | None = None,
        max_hops: int = 20,
        ascii_map: str = " .,:;<+*LtCa4U80dQM@",
        default_cell: NDArray[Cell] | str = " ",
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            default_cell=default_cell,
            alpha=alpha,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.caster_map = caster_map
        """The raycaster map."""
        self.camera = camera
        """The raycaster camera."""
        self.wall_textures = wall_textures
        """Textures for walls."""
        self.sprites = sprites
        """A list of sprites."""
        self.sprite_textures = sprite_textures
        """Textures for sprites."""
        self.max_hops = max_hops
        """Determines how far rays are cast."""
        self.ascii_map = np.array(list(ascii_map))
        """Dark to bright ascii characters for shading."""

        self._shades = len(self.ascii_map) - 1
        self._shade_values = np.linspace(-12, 24, self._shades, dtype=int)
        self._side_shade = 2
        self._shade_diff = self._shades - self._side_shade
        # Buffers
        self._pos_int = np.zeros((2,), dtype=int)
        self._pos_frac = np.zeros((2,), dtype=float)

        self.on_size()

    def on_size(self):
        """Resize canvas array and re-make caster buffers."""
        h, w = self._size

        self.canvas = np.full((h, w), self.default_cell)

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

    def cast_rays(self):
        """Update canvas by casting all rays."""
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

        self.canvas["char"] = " "
        self.canvas["char"][self.height // 2 :, ::2] = self.ascii_map[1]

        for column in range(self.width):
            self._cast_ray(column)

        self._cast_sprites()

    def _cast_ray(self, column):
        """Cast a ray for a given column of the screen."""
        camera = self.camera
        camera_pos = camera.pos
        caster_map = self.caster_map

        ray_pos = self._pos_int
        ray_pos[:] = camera_pos

        ray_angle = self._rotated_angles[column]
        delta = self._deltas[column]
        step = self._steps[column]
        sides = self._sides[column]

        # Cast a ray until we hit a wall or hit max_hops
        for _ in range(self.max_hops):
            side = 0 if sides[0] < sides[1] else 1
            sides[side] += delta[side]
            ray_pos[side] += step[side]

            if texture_index := caster_map[tuple(ray_pos)]:
                # Distance from wall to camera plane.
                # Note that distance of wall to camera is not used
                # as it would result in a "fish-eye" effect.
                distance = (
                    ray_pos[side] - camera_pos[side] + (0 if step[side] == 1 else 1)
                ) / ray_angle[side]
                break
        else:  # No walls in range.
            distance = 10000

        self._column_distances[column] = distance

        column_height = int(self.height / distance) if distance else 10000
        if column_height == 0:
            return

        # Start and end y-coordinates of column.
        half_height = self.height >> 1
        half_column = column_height >> 1
        if half_column > half_height:
            half_column = half_height

        start = half_height - half_column
        end = half_height + half_column
        drawn_height = end - start

        shade = min(drawn_height, self._shade_diff)
        if side:
            shade += self._side_shade

        shade_buffer = np.full(drawn_height, shade)
        wall_texture = self.wall_textures[texture_index - 1]
        tex_h, tex_w = wall_texture.shape

        # Exactly where wall was hit by ray as a percentage of its width.
        wall_x = (camera_pos[1 - side] + distance * ray_angle[1 - side]) % 1

        # Use above percentage to grab the column of the texture we need.
        tex_x = int(wall_x * tex_w)
        if (-1 if side == 1 else 1) * ray_angle[side] < 0:  # Sign correction.
            tex_x = tex_w - tex_x - 1

        # Interpolate texture onto column
        offset = (column_height - drawn_height) / 2
        ratio = tex_h / column_height
        texture_start = offset * ratio
        texture_end = (offset + drawn_height) * ratio
        tex_ys = np.linspace(
            texture_start, texture_end, num=drawn_height, endpoint=False, dtype=int
        )
        shade_buffer += self._shade_values[wall_texture[tex_ys, tex_x]]
        np.clip(shade_buffer, 1, self._shades, out=shade_buffer)

        # Paint column.
        self.canvas["char"][:, ::-1][start:end, column] = self.ascii_map[shade_buffer]

    def _cast_sprites(self):
        """Render all sprites."""
        h, w = self.size
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
            tex_height, tex_width = sprite_tex.shape

            clip_y = (sprite_height - h) / 2
            rows += clip_y
            rows *= tex_height / sprite_height
            np.clip(rows, 0, None, out=rows)

            clip_x = sprite_x - sprite_width / 2
            tex_xs = columns - clip_x
            tex_xs *= tex_width / sprite_width

            sprite_rect = sprite_tex[rows.astype(int)][:, tex_xs.astype(int)]
            chars = self.canvas["char"][:, ::-1]
            chars[start_y:end_y, columns] = np.where(
                sprite_rect != "0",
                sprite_rect,
                chars[start_y:end_y, columns],
            )
