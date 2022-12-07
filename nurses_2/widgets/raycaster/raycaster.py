"""
A raycaster widget.
"""
import numpy as np

from ...clamp import clamp
from ...colors import BLACK, Color
from ..graphic_widget import GraphicWidget
from .protocols import Map, Camera, Texture
from .sprite import Sprite


class Raycaster(GraphicWidget):
    """
    A raycaster widget.

    Parameters
    ----------
    map : Map
        An array-like with non-zero entries n indicating walls with texture `wall_textures[n - 1]`.
    camera : Camera
        A view in the map.
    wall_textures : List[Texture]
        Textures for walls.
    light_wall_textures : list[Texture] | None, default: None
        If provided, walls north/south face will use textures in :attr:`light_wall_textures`
        instead of :attr:`wall_textures`.
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
        If widget is transparent, the alpha channel of the underlying texture will be multiplied by this
        value. (0 <= alpha <= 1.0)
    interpolation : Interpolation, default: Interpolation.LINEAR
        Interpolation used when widget is resized.
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
    map : Map
        An array-like with non-zero entries n indicating walls with texture `wall_textures[n - 1]`.
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
    texture : numpy.ndarray
        uint8 RGBA color array.
    default_color : AColor
        Default texture color.
    alpha : float
        Transparency of widget if :attr:`is_transparent` is true.
    interpolation : Interpolation
        Interpolation used when widget is resized.
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
    to_png:
        Write :attr:`texture` to provided path as a `png` image.
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
    HOPS = 20  # How far rays are cast.

    def __init__(
        self,
        *,
        map: Map,
        camera: Camera,
        wall_textures: list[Texture] | None,
        light_wall_textures: list[Texture] | None=None,
        sprites: list[Sprite] | None=None,
        sprite_textures: list[Texture] | None=None,
        ceiling: Texture | None=None,
        ceiling_color: Color=BLACK,
        floor: Texture | None=None,
        floor_color: Color=BLACK,
        **kwargs,
    ):
        super().__init__(**kwargs)

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
        self._distances = distances = np.linspace(1e-10, h, num=h, endpoint=False, dtype=float)
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

        ###########
        # Casting #
        ###########

        for _ in range(self.HOPS):
            side = 0 if sides[0] < sides[1] else 1
            sides[side] += delta[side]
            ray_pos[side] += step[side]

            if texture_index := map[tuple(ray_pos)]:
                # Distance from wall to camera plane.
                # Note that distance of wall to camera is not used
                # as it would result in a "fish-eye" effect.
                distance = (
                    ray_pos[side]
                    - camera_pos[side]
                    + (0 if step[side] == 1 else 1)
                ) / ray_angle[side]
                break

        else:  # No walls in range.
            distance = 1000  # 1000 == infinity, roughly

        self._column_distances[column] = distance

        #############
        # Rendering #
        #############

        texture = self.texture[:, ::-1]
        height = texture.shape[0]

        column_height = int(height / distance) if distance else 1000  # 1000 == infinity, roughly

        # Start and end y-coordinates of column.
        ########################################
        half_height = height >> 1              #
        half_column = column_height >> 1       #
        if half_column > half_height:          #
            half_column = half_height          #
                                               #
        start = half_height - half_column      #
        end = half_height + half_column        #
        ########################################

        wall_texture = (self.wall_textures if side else self.light_wall_textures)[texture_index - 1]
        tex_h, tex_w, _ = wall_texture.shape

        # Exactly where wall was hit by ray as a percentage of its width.
        wall_x = (camera_pos[1 - side] + distance * ray_angle[1 - side]) % 1

        # Use above percentage to grab the column of the texture we need.
        tex_x = int(wall_x * tex_w)
        if (-1 if side == 1 else 1) * ray_angle[side] < 0:  # Sign correction.
            tex_x = tex_w - tex_x - 1

        # Interpolate texture onto column
        ############################################################
        drawn_height = end - start                                 #
        offset = (column_height - drawn_height) / 2                #
        ratio = tex_h / column_height                              #
        texture_start = offset * ratio                             #
        texture_end = (offset + drawn_height) * ratio              #
        tex_ys = np.linspace(                                      #
            texture_start,                                         #
            texture_end,                                           #
            num=drawn_height,                                      #
            endpoint=False,                                        #
            dtype=int                                              #
        )                                                          #
        texture_column = wall_texture[tex_ys, tex_x].astype(float) #
        ############################################################

        # Darken colors further away.
        texture_column *= np.e ** (-distance * .05)
        np.clip(texture_column, 0, 255, out=texture_column, casting="unsafe")

        # Paint column.
        texture[start: end, column] = texture_column

        # Render floor and ceiling.
        ###################################################################################
        ceiling = self.ceiling                                                            #
        floor = self.floor                                                                #
                                                                                          #
        if ceiling is None and floor is None:                                             #
            texture[:start, column] = self.ceiling_color                                  #
            texture[end:, column] = self.floor_color                                      #
            return                                                                        #
                                                                                          #
        # Buffer views                                                                    #
        floor_pos = self._floor_pos                                                       #
        weights = self._weights[half_column:]                                             #
        tex_frac = self._tex_frac[half_column:]                                           #
        tex_frac_2 = self._tex_frac_2[half_column:]                                       #
        tex_int = self._tex_int[half_column:]                                             #
                                                                                          #
        # Floor position                                                                  #
        if side == 0:                                                                     #
            facing = float(ray_angle[0] < 0), wall_x                                      #
        else:                                                                             #
            facing = wall_x, float(ray_angle[1] < 0)                                      #
        np.add(ray_pos, facing, out=floor_pos)                                            #
                                                                                          #
        # Horizontal distances of floor / ceiling                                         #
        np.divide(self._distances[half_column:], distance, out=weights[:, 0])             #
        weights[:, 1] = weights[:, 0]                                                     #
                                                                                          #
        # Texture coordinates                                                             #
        # (weights * floor_pos + (1 - weights) * camera_pos) % 1                          #
        np.multiply(weights, floor_pos, out=tex_frac)                                     #
        np.subtract(1.0, weights, out=weights)                                            #
        np.multiply(weights, camera_pos, out=tex_frac_2)                                  #
        np.add(tex_frac, tex_frac_2, out=tex_frac)                                        #
        np.mod(tex_frac, 1.0, out=tex_frac)                                               #
                                                                                          #
        # Paint ceiling                                                                   #
        if ceiling is not None:                                                           #
            # Note reversed order of texture coordinates from floor                       #
            np.multiply(ceiling.shape[:2], tex_frac[::-1], out=tex_int, casting="unsafe") #
            texture[:start, column] = ceiling[tex_int[:, 0], tex_int[:, 1]]               #
        else:                                                                             #
            texture[:start, column] = self.ceiling_color                                  #
                                                                                          #
        # Paint floor                                                                     #
        if floor is not None:                                                             #
            np.multiply(floor.shape[:2], tex_frac, out=tex_int, casting="unsafe")         #
            texture[end:, column] = floor[tex_int[:, 0], tex_int[:, 1]]                   #
        else:                                                                             #
            texture[end:, column] = self.floor_color                                      #
        ###################################################################################

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

        for sprite in sprites:  # Draw each sprite from furthest to closest.
            # Transformed position of sprites due to camera position
            y, x = sprite.relative @ cam_inv

            if y <= 0:  # Sprite is behind camera, don't draw it.
                continue

            # Sprite x-position on screen
            sprite_x = int(half_w * (1 + x / y))

            sprite_height = int(h / y)
            sprite_width = int(half_w / y)
            if sprite_height == 0 or sprite_width == 0:  # Sprite too small.
                continue

            start_x = clamp(sprite_x - sprite_width // 2, 0, w)
            end_x = clamp(sprite_x + sprite_width // 2, 0, w)
            columns = np.arange(start_x, end_x)

            # Remove columns that are behind walls or off-screen:
            # Buffered version of `(0 <= columns) & (columns <= w) & (y <= column_distances[columns])`
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

            sprite_rect = sprite_tex[rows.astype(int)][:, tex_xs.astype(int)].astype(float)
            sprite_rgb = sprite_rect[..., :3]
            tex_rect = texture[start_y: end_y, columns, :3]

            np.subtract(sprite_rgb, tex_rect, out=sprite_rgb)
            np.multiply(sprite_rgb, sprite_rect[..., 3, None], out=sprite_rgb)
            np.divide(sprite_rgb, 255, out=sprite_rgb)
            np.add(sprite_rgb, tex_rect, out=sprite_rgb)

            texture[start_y: end_y, columns, :3] = sprite_rgb

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        # Bring in to locals
        #######################################
        camera = self.camera                  #
        pos_frac = self._pos_frac             #
        rotated_angles = self._rotated_angles #
        deltas = self._deltas                 #
        steps = self._steps                   #
        sides = self._sides                   #
        multiply = np.multiply                #
        cast_ray = self.cast_ray              #
        #######################################

        # Early calculations on rays can be vectorized:
        ############################################################
        np.dot(self._ray_angles, camera.plane, out=rotated_angles) #
                                                                   #
        with np.errstate(divide="ignore"):                         #
            np.true_divide(1.0, rotated_angles, out=deltas)        #
        np.absolute(deltas, out=deltas)                            #
                                                                   #
        np.sign(rotated_angles, out=steps, casting="unsafe")       #
                                                                   #
        np.heaviside(steps, 1.0, out=sides)                        #
        np.mod(camera.pos, 1.0, out=pos_frac)                      #
        np.subtract(sides, pos_frac, out=sides)                    #
        multiply(sides, steps, out=sides)                          #
        multiply(sides, deltas, out=sides)                         #
        ############################################################

        for column in range(self.width):
            cast_ray(column)

        self.cast_sprites()

        super().render(canvas_view, colors_view, source)
