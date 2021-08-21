from typing import List, Optional

import numpy as np

from ...widgets import Widget
from ...colors import BLACK, Color
from .protocols import Map, Camera, Texture


class RayCaster(Widget):
    """
    A raycaster for nurses_2.

    Parameters
    ----------
    map : Map
        An array-like with non-zero entries n indicating walls with texture `wall_textures[n - 1]`.
    camera : Camera
        A view in the map.
    wall_textures : List[Texture]
        Textures for walls.
    light_wall_textures : Optional[list[Texture]], default: None
        If provided, walls north/south face will use textures in `light_wall_textures` instead
        of `wall_textures`.
    ceiling : Optional[Texture], default: None
        Ceiling texture.
    ceiling_color : Color, default: BLACK
        Color of ceiling if no ceiling texture.
    floor : Optional[Texture], default: None
        Floor texture.
    floor_color : Color, default: BLACK
        Color of floor if no floor texture.
    """
    HOPS = 20  # How far rays are cast.

    def __init__(
        self,
        *args,
        map: Map,
        camera: Camera,
        wall_textures: List[Texture],
        light_wall_textures: Optional[List[Texture]]=None,
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
        self.wall_textures = wall_textures
        self.light_wall_textures = light_wall_textures or wall_textures
        self.ceiling = ceiling
        self.ceiling_color = ceiling_color
        self.floor = floor
        self.floor_color = floor_color

        # Buffers
        self._pos_int = np.zeros((2,), dtype=np.int16)
        self._pos_frac = np.zeros((2,), dtype=np.float16)
        self._floor_pos = np.zeros((2,), dtype=np.float16)

        self.resize(self.size)

    def resize(self, size):
        super().resize(size)
        height = self.height
        width = self.width

        # Note double resolution due to half-block characters.
        self._colors = np.full((height << 1, width, 3), 0, dtype=np.uint8)

        # Precalculate angle of rays cast.
        self._ray_angles = angles = np.ones((width, 2), dtype=np.float16)
        angles[:, 1] = np.linspace(-1, 1, width)

        # Precalculate distances for ceiling and floor textures
        self._distances = distances = np.linspace(.001, height, num=height, endpoint=False, dtype=np.float16)
        np.divide(height, distances, out=distances, dtype=np.float16)

        # Buffers
        self._rotated_angles = np.zeros_like(angles)
        self._deltas = np.zeros_like(angles)
        self._sides = np.zeros_like(angles)
        self._steps = np.zeros_like(angles, dtype=np.int16)
        self._weights = weights = np.zeros((height, 2), dtype=np.float16)
        self._tex_frac = np.zeros_like(weights)
        self._tex_frac_2 = np.zeros_like(weights)
        self._tex_int = np.zeros_like(weights, dtype=np.int16)

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

        #############
        # Rendering #
        #############

        colors = self._colors
        height = colors.shape[0]

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

        texture = (self.wall_textures if side else self.light_wall_textures)[texture_index - 1]
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

        # Render floor and ceiling.
        ###################################################################################
        ceiling = self.ceiling                                                            #
        floor = self.floor                                                                #
                                                                                          #
        if ceiling is None and floor is None:                                             #
            colors[:start, column] = self.ceiling_color                                   #
            colors[end:, column] = self.floor_color                                       #
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
            colors[:start, column] = ceiling[tex_int[:, 0], tex_int[:, 1]]                #
        else:                                                                             #
            colors[:start, column] = self.ceiling_color                                   #
                                                                                          #
        # Paint floor                                                                     #
        if floor is not None:                                                             #
            np.multiply(floor.shape[:2], tex_frac, out=tex_int, casting="unsafe")         #
            colors[end:, column] = floor[tex_int[:, 0], tex_int[:, 1]]                    #
        else:                                                                             #
            colors[end:, column] = self.floor_color                                       #
        ###################################################################################

    def render(self, canvas_view, colors_view, rect):
        colors = self._colors[:, ::-1]  # `::-1` -- Not sure why rendering is flipped, but this is an easy fix.
        height = self.height

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

        # Early calculations on rays can be vectorized:
        ############################################################
        np.dot(self._ray_angles, camera.plane, out=rotated_angles) #
                                                                   #
        with errstate(divide="ignore"):                            #
            divide(1.0, rotated_angles, out=deltas)                #
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

        np.concatenate((colors[::2], colors[1::2]), axis=-1, out=self.colors)

        super().render(canvas_view, colors_view, rect)
