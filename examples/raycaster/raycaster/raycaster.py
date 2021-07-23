from typing import List, Optional

import numpy as np

from nurses_2.widgets import Widget
from nurses_2.widgets.image import Image
from nurses_2.colors import BLACK, Color

from .protocols import Map, Camera, Texture


# TODO: It may be more efficient to store textures in F-order,
# so that columns are closer together in memory. Consider updating
# Texture protocol to allow memory-order to be swapped.
class RayCaster(Widget):
    """
    A raycaster for nurses_2.

    Parameters
    ----------
    map : Map
        Map for raycaster
        Non-zero `p` in map correspond to walls with texture `textures[p - 1]`.
    camera : Camera
        View in map.
    textures : list[Texture]
        Textures for walls in `map`.
    light_textures : list[Texture] | None
        If provided, walls oriented in one direction will have a lighter color texture
        than walls oriented in another. This gives an illusion of depth.
    ceiling : Texture | None
        Ceiling texture.
    ceiling_color : Color, default: BLACK
        Color of ceiling if no ceiling texture.
    floor : Texture | None
        Floor texture.
    floor_color : Color, default: BLACK
        Color of floor if no floor texture.
    """
    HOPS = 20  # How far rays are cast.

    def __init__(
        self,
        *args,
        map: np.ndarray,
        camera: Camera,
        textures: List[Texture],
        light_textures: Optional[List[Texture]]=None,
        ceiling: Optional[Texture]=None,
        ceiling_color: Color=BLACK,
        floor: Optional[Texture]=None,
        floor_color: Color=BLACK,
        default_char="▀",
        **kwargs,
        ):
        kwargs.pop('transparent', None)

        super().__init__(*args, default_char=default_char, **kwargs)

        self.map = map
        self.camera = camera
        self.textures = textures
        self.light_textures = light_textures or textures
        self.ceiling = ceiling
        self.ceiling_color = ceiling_color
        self.floor = floor
        self.floor_color = floor_color

        # Buffers for camera and ray position
        self._pos_int = np.zeros((2,), dtype=np.int16)
        self._pos_frac = np.zeros((2,), dtype=np.float16)

        self.resize(self.dim)

    def resize(self, dim):
        super().resize(dim)
        width = self.width

        self._colors = np.full((2 * self.height, width, 3), 0, dtype=np.uint8)

        # Pre-calculate angle of rays cast.
        self._ray_angles = angles = np.ones((width, 2), dtype=np.float16)
        angles[:, 1] = np.linspace(-1, 1, width)

        # Buffers
        self._rotated_angles = np.zeros_like(angles)
        self._deltas = np.zeros_like(angles)
        self._sides = np.zeros_like(angles)
        self._steps = np.zeros_like(angles, dtype=np.int16)

    def render_backgroun(self):
        """
        Render floor and/or ceiling.
        """
        # camera = self.camera
        # height = self.height

        # ray_initial = camera.plane[0] - camera.plane[1]
        # ray_final = camera.plane.sum(axis=0)

        # ys = np.arange(-height, height)
        # mid = height * .5
        # row_distance = mid / ys

        # steps = row_distance * (ray_final - ray_initial) / self.width

        # floor_pos = camera.pos + row_distance * ray_initial

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
                break
        else:  # No walls in range.
            return

        # Perpendicular distance from wall to camera plane.
        # Note that euclidean distance of wall to camera is not used
        # as it would result in a "fish-eye" effect.
        distance = (
            ray_pos[side]
            - camera_pos[side]
            + (0 if step[side] == 1 else 1)
        ) / ray_angle[side]

        #############
        # Rendering #
        #############

        colors = self._colors
        height = colors.shape[0]

        column_height = int(height / distance) if distance else 1000  # 1000 == infinity, roughly
        if column_height == 0:
            return  # Draw nothing

        # Start and end y-coordinates of column.
        ########################################
        half_height = height >> 1              #
        half_column = column_height >> 1       #
                                               #
        start = half_height - half_column      #
        if start < 0:                          #
            start = 0                          #
                                               #
        end = half_height + half_column        #
        if end >= height:                      #
            end = height - 1                   #
        ########################################

        texture = (self.textures if side else self.light_textures)[texture_index - 1]
        tex_h, tex_w, _ = texture.shape

        # Exactly where wall was hit by ray as a percentage of its width.
        wall_x = (camera_pos[1 - side] + distance * ray_angle[1 - side]) % 1

        # Use above percentage to grab the column of the texture we need.
        tex_x = int(wall_x * tex_w)
        if (-1 if side == 1 else 1) * ray_angle[side] < 0:  # Sign correction.
            tex_x = tex_w - tex_x - 1

        # Interpolate texture onto column
        #######################################################
        drawn_height = end - start                            #
        offset = (column_height - drawn_height) / 2           #
        ratio = tex_h / column_height                         #
        texture_start = offset * ratio                        #
        texture_end = (offset + drawn_height) * ratio         #
        tex_ys = np.linspace(                                 #
            texture_start,                                    #
            texture_end,                                      #
            num=drawn_height,                                 #
            endpoint=False,                                   #
            dtype=int                                         #
        )                                                     #
        texture_column = texture[tex_ys, tex_x].astype(float) #
        #######################################################

        # Darken colors further away.
        texture_column *= np.e ** (-distance * .05)
        np.clip(texture_column, 0, 255, out=texture_column, casting="unsafe")

        # Paint column.
        colors[start: end, column] = texture_column

    def render(self, canvas_view, colors_view, rect):
        colors = self._colors
        height = self.height

        if self.ceiling is None and self.floor is None:
            colors[:height, :] = self.ceiling_color
            colors[height:, :] = self.floor_color
        else:
            if self.ceiling is None:
                colors[:height, :] = self.ceiling_color
            elif self.floor is None:
                colors[height:, :] = self.floor_color

            self.render_background()

        # Bring in to locals
        #######################################
        camera = self.camera                  #
        pos_frac = self._pos_frac             #
        rotated_angles = self._rotated_angles #
        deltas = self._deltas                 #
        steps = self._steps                   #
        sides = self._sides                   #
        multiply = np.multiply                #
        divide = np.true_divide               #
        errstate = np.errstate                #
        cast_ray = self.cast_ray              #
        #######################################

        # Early calculations on rays can be vectorized; fill buffers with these calculations.
        #####################################################################################
        np.dot(self._ray_angles, camera.plane, out=rotated_angles)                          #
                                                                                            #
        with errstate(divide="ignore"):                                                     #
            divide(1.0, rotated_angles, out=deltas)                                         #
        np.absolute(deltas, out=deltas)                                                     #
                                                                                            #
        np.sign(rotated_angles, out=steps, casting="unsafe")                                #
                                                                                            #
        np.heaviside(steps, 1.0, out=sides)                                                 #
        np.mod(camera.pos, 1.0, out=pos_frac)                                               #
        np.subtract(sides, pos_frac, out=sides)                                             #
        multiply(sides, steps, out=sides)                                                   #
        multiply(sides, deltas, out=sides)                                                  #
        #####################################################################################

        for column in range(self.width):
            cast_ray(column)

        np.concatenate((colors[::2], colors[1::2]), axis=-1, out=self.colors)

        super().render(canvas_view, colors_view, rect)
