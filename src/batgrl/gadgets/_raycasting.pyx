from libc.stdlib cimport free, malloc, qsort
from libc.math cimport cos, exp, fabs, floor, sin

cimport cython

from .._rendering cimport Cell

ctypedef unsigned char uint8


cdef struct Sprite:
    double y
    double x
    size_t texture_idx
    double distance


cdef int sprite_cmp(const void* a, const void* b) noexcept nogil:
    cdef:
        const Sprite *sa = <Sprite*>a
        const Sprite *sb = <Sprite*>b
    if sa.distance > sb.distance:
        return -1
    if sa.distance == sb.distance:
        return 0
    return 1


cdef inline void composite(uint8 *dst, uint8 *src):
    if src[3] == 0:
        return

    if src[3] == 255 or dst[3] == 0:
        # Fast path for masking.
        dst[0] = src[0]
        dst[1] = src[1]
        dst[2] = src[2]
        dst[3] = src[3]
        return

    cdef double b = <double>dst[0], alpha = <double>src[3] / 255.0
    dst[0] = <uint8>((<double>src[0] - b) * alpha + b)
    b = <double>dst[1]
    dst[1] = <uint8>((<double>src[1] - b) * alpha + b)
    b = <double>dst[2]
    dst[2] = <uint8>((<double>src[2] - b) * alpha + b)
    dst[3] = src[3] + <uint8>(<double>dst[3] * (1 - alpha))


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline void draw_floor_ceiling(
    uint8[:, :, ::1] texture,
    bint draw_ceil,
    uint8[:, :, ::1] ceiling_texture,
    bint draw_floor,
    uint8[:, :, ::1] floor_texture,
    double pos_y,
    double pos_x,
    double dir_y,
    double dir_x,
    double plane_y,
    double plane_x,
):
    cdef:
        size_t h = texture.shape[0], w = texture.shape[1]
        size_t y, x
        size_t ch, cw, fh, fw
        double ray_dir_y0, ray_dir_y1
        double ray_dir_x0, ray_dir_x1
        int p
        double pos_z, row_distance
        double floor_step_y, floor_step_x
        double floor_y, floor_x
        int cell_y, cell_x, tx, ty

    if draw_ceil:
        ch = ceiling_texture.shape[0]
        cw = ceiling_texture.shape[1]
    if draw_floor:
        fh = floor_texture.shape[0]
        fw = floor_texture.shape[1]

    for y in range(h//2, h):
        ray_dir_y0 = dir_y - plane_y
        ray_dir_y1 = dir_y + plane_y
        ray_dir_x0 = dir_x - plane_x
        ray_dir_x1 = dir_x + plane_x
        p = y - h // 2
        pos_z = 0.5 * h
        if p:
            row_distance = pos_z / p
        else:
            row_distance = pos_z
        floor_step_y = row_distance * (ray_dir_y1 - ray_dir_y0) / w
        floor_step_x = row_distance * (ray_dir_x1 - ray_dir_x0) / w
        floor_y = pos_y + row_distance * ray_dir_y0
        floor_x = pos_x + row_distance * ray_dir_x0
        for x in range(w):
            cell_y = <int>floor_y
            cell_x = <int>floor_x

            if draw_ceil:
                ty = <int>(ch * (floor_y - cell_y))
                tx = <int>(cw * (floor_x - cell_x))
                texture[h - y - 1, x, 0] = ceiling_texture[ty, tx, 0]
                texture[h - y - 1, x, 1] = ceiling_texture[ty, tx, 1]
                texture[h - y - 1, x, 2] = ceiling_texture[ty, tx, 2]
                texture[h - y - 1, x, 3] = ceiling_texture[ty, tx, 3]
            if draw_floor:
                ty = <int>(fh * (floor_y - cell_y))
                tx = <int>(fw * (floor_x - cell_x))
                texture[y, x, 0] = floor_texture[ty, tx, 0]
                texture[y, x, 1] = floor_texture[ty, tx, 1]
                texture[y, x, 2] = floor_texture[ty, tx, 2]
                texture[y, x, 3] = floor_texture[ty, tx, 3]

            floor_y += floor_step_y
            floor_x += floor_step_x


@cython.boundscheck(False)
@cython.wraparound(False)
def cast_rays(
    uint8[:, :, ::1] texture,
    uint8[:, ::1] map,
    tuple[double, double] camera_pos,
    double camera_theta,
    double camera_fov,
    list[uint8[:, :, ::1]] wall_textures,
    uint8[:, :, ::1] ceiling_texture,
    uint8[:, :, ::1] floor_texture,
    uint8[::1] sprite_indexes,
    double[:, ::1] sprite_positions,
    list[uint8[:, :, ::1]] sprite_textures,
) -> None:
    cdef size_t h = texture.shape[0], w = texture.shape[1]
    if not h or not w:
        return

    cdef:
        double pos_y = camera_pos[0], pos_x = camera_pos[1]
        double dir_y = cos(camera_theta), dir_x = sin(camera_theta)
        double plane_y = camera_fov * dir_x, plane_x = camera_fov * -dir_y
        bint draw_ceiling = ceiling_texture is not None
        bint draw_floor = floor_texture is not None

    if draw_ceiling or draw_floor:
        draw_floor_ceiling(
            texture,
            draw_ceiling,
            ceiling_texture,
            draw_floor,
            floor_texture,
            pos_y,
            pos_x,
            dir_y,
            dir_x,
            plane_y,
            plane_x,
        )

    cdef:
        size_t y, x
        size_t mh = map.shape[0], mw = map.shape[1]
        int map_y, map_x
        double camera_x, delta_dist_y, delta_dist_x
        int step_y, step_x
        int line_height
        int initial_y, draw_start_y, draw_end_y
        size_t tex_h, tex_w
        int tex_y, tex_x
        double wall_x, step, tex_pos
        bint side, skip
        double perp_wall_dist
        uint8[:, :, ::1] wall_texture
        double *zbuffer = <double*>malloc(w * sizeof(double))

    for x in range(w):
        camera_x = 2 * x / <double>w - 1
        ray_dir_y = dir_y + plane_y * camera_x
        ray_dir_x = dir_x + plane_x * camera_x
        map_y = <int>pos_y
        map_x = <int>pos_x
        delta_dist_y = (
            1e30
            if ray_dir_y == 0
            else fabs(1 / ray_dir_y)
        )
        delta_dist_x = (
            1e30
            if ray_dir_x == 0
            else fabs(1 / ray_dir_x)
        )

        if ray_dir_y < 0:
            step_y = -1
            side_dist_y = (pos_y - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - pos_y) * delta_dist_y

        if ray_dir_x < 0:
            step_x = -1
            side_dist_x = (pos_x - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - pos_x) * delta_dist_x

        # Cast rays.
        skip = 0
        while True:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            if map_y < 0 or map_y >= mh or map_x < 0 or map_x >= mw:
                skip = 1  # Outside map.
                break

            if map[map_y, map_x] > 0:
                wall_texture = wall_textures[map[map_y, map_x] - 1]
                tex_h = wall_texture.shape[0]
                tex_w = wall_texture.shape[1]
                if tex_h == 0 or tex_w == 0:
                    skip = 1  # Empty texture?
                break

        if side:
            perp_wall_dist = side_dist_y - delta_dist_y
        else:
            perp_wall_dist = side_dist_x - delta_dist_x
        zbuffer[x] = perp_wall_dist

        if skip or perp_wall_dist == 0:
            continue

        line_height = <int>(h / perp_wall_dist)
        if line_height == 0:
            continue

        initial_y = h // 2 - line_height // 2
        if initial_y < 0:
            draw_start_y = 0
        else:
            draw_start_y = initial_y
        draw_end_y = h // 2 + line_height // 2
        if draw_end_y > h:
            draw_end_y = h

        if side:
            wall_x = pos_x + perp_wall_dist * ray_dir_x
        else:
            wall_x = pos_y + perp_wall_dist * ray_dir_y
        wall_x -= floor(wall_x)

        tex_x = <int>(wall_x * <double>tex_w)
        if side == 0 and ray_dir_x > 0 or side == 1 and ray_dir_y < 0:
            tex_x = tex_w - tex_x - 1

        step = <double>tex_h / line_height
        tex_pos = (draw_start_y - initial_y) * step
        for y in range(draw_start_y, draw_end_y):
            tex_y = <int>tex_pos
            if tex_y < 0 or tex_y > tex_h:
                continue

            tex_pos += step
            if side:
                # Darken wall.
                texture[y, x, 0] = (wall_texture[tex_y, tex_x, 0] >> 1) & 127
                texture[y, x, 1] = (wall_texture[tex_y, tex_x, 1] >> 1) & 127
                texture[y, x, 2] = (wall_texture[tex_y, tex_x, 2] >> 1) & 127
            else:
                texture[y, x, 0] = wall_texture[tex_y, tex_x, 0]
                texture[y, x, 1] = wall_texture[tex_y, tex_x, 1]
                texture[y, x, 2] = wall_texture[tex_y, tex_x, 2]
            texture[y, x, 3] = wall_texture[tex_y, tex_x, 3]

    cdef:
        size_t nsprites, i
        Sprite *sprites
        Sprite *sprite

    nsprites = sprite_indexes.shape[0]
    sprites = <Sprite*>malloc(nsprites * sizeof(Sprite))
    for i in range(nsprites):
        sprite = &sprites[i]
        sprite.y = sprite_positions[i, 0]
        sprite.x = sprite_positions[i, 1]
        sprite.texture_idx = sprite_indexes[i]
        sprite.distance = (
            (pos_y - sprite.y) * (pos_y - sprite.y)
            + (pos_x - sprite.x) * (pos_x - sprite.x)
        )
    qsort(sprites, nsprites, sizeof(Sprite), &sprite_cmp)

    cdef:
        double inv_det = 1.0 / (plane_x * dir_y - plane_y * dir_x)
        double sprite_y, sprite_x
        double trans_y, trans_x, scale_h, scale_w
        int sprite_screen_x, sprite_h, sprite_w
        int initial_x, draw_start_x, draw_end_x
        uint8[:, :, ::1] sprite_texture

    for i in range(nsprites):
        sprite_y = sprites[i].y - pos_y
        sprite_x = sprites[i].x - pos_x
        trans_y = inv_det * (plane_x * sprite_y - plane_y * sprite_x)
        if trans_y <= 0:
            # Behind the camera.
            continue

        trans_x = inv_det * (dir_y * sprite_x - dir_x * sprite_y)
        sprite_screen_x = <int>((w / 2) * (1 + trans_x / trans_y))

        sprite_h = <int>(h / trans_y)
        if sprite_h == 0:
            continue
        sprite_w = <int>((w / 2) / trans_y)
        if sprite_w == 0:
            continue

        initial_y = h // 2 - sprite_h // 2
        if initial_y < 0:
            draw_start_y = 0
        else:
            draw_start_y = initial_y
        draw_end_y = h // 2 + sprite_h // 2
        if draw_end_y > h:
            draw_end_y = h

        initial_x = sprite_screen_x - sprite_w // 2
        if initial_x < 0:
            draw_start_x = 0
        else:
            draw_start_x = initial_x
        draw_end_x = sprite_screen_x + sprite_w // 2
        if draw_end_x > w:
            draw_end_x = w

        sprite_texture = sprite_textures[sprites[i].texture_idx]
        tex_h = sprite_texture.shape[0]
        tex_w = sprite_texture.shape[1]

        scale_h = tex_h / sprite_h
        scale_w = tex_w / sprite_w

        for x in range(draw_start_x, draw_end_x):
            if trans_y > zbuffer[x]:
                # Sprite behind a wall.
                continue

            tex_x = <int>((x - initial_x) * scale_w)
            if tex_x < 0 or tex_x >= tex_w:
                continue

            for y in range(draw_start_y, draw_end_y):
                tex_y = <int>((y - initial_y) * scale_h)
                if tex_y < 0 or tex_y >= tex_h:
                    continue
                composite(&texture[y, x, 0], &sprite_texture[tex_y, tex_x, 0])

    free(zbuffer)
    free(sprites)


cdef uint8 shade_wall(uint8 value, double distance):
    return <uint8>(value * exp(-0.15 * distance))


@cython.boundscheck(False)
@cython.wraparound(False)
def text_cast_rays(
    Cell[:, ::1] canvas,
    uint8[:, ::1] map,
    tuple[double, double] camera_pos,
    double camera_theta,
    double camera_fov,
    list[uint8[:, ::1]] wall_textures,
    uint8[::1] sprite_indexes,
    double[:, ::1] sprite_positions,
    list[Cell[:, ::1]] sprite_textures,
    unsigned int[::1] ascii_map,
) -> None:
    cdef size_t h = canvas.shape[0], w = canvas.shape[1]
    if not h or not w:
        return

    cdef:
        double pos_y = camera_pos[0], pos_x = camera_pos[1]
        double dir_y = cos(camera_theta), dir_x = sin(camera_theta)
        double plane_y = camera_fov * dir_x, plane_x = camera_fov * -dir_y
        size_t y, x
        size_t mh = map.shape[0], mw = map.shape[1]
        int map_y, map_x
        double camera_x, delta_dist_y, delta_dist_x
        int step_y, step_x
        int line_height
        int initial_y, draw_start_y, draw_end_y
        size_t tex_h, tex_w
        int tex_y, tex_x
        double wall_x, step, tex_pos
        bint side, skip
        double perp_wall_dist
        uint8[:, ::1] wall_texture
        double *zbuffer = <double*>malloc(w * sizeof(double))
        uint8 wall_value

    for x in range(w):
        camera_x = 2 * x / <double>w - 1
        ray_dir_y = dir_y + plane_y * camera_x
        ray_dir_x = dir_x + plane_x * camera_x
        map_y = <int>pos_y
        map_x = <int>pos_x
        delta_dist_y = (
            1e30
            if ray_dir_y == 0
            else fabs(1 / ray_dir_y)
        )
        delta_dist_x = (
            1e30
            if ray_dir_x == 0
            else fabs(1 / ray_dir_x)
        )

        if ray_dir_y < 0:
            step_y = -1
            side_dist_y = (pos_y - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - pos_y) * delta_dist_y

        if ray_dir_x < 0:
            step_x = -1
            side_dist_x = (pos_x - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - pos_x) * delta_dist_x

        # Cast rays.
        skip = 0
        while True:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            if map_y < 0 or map_y >= mh or map_x < 0 or map_x >= mw:
                skip = 1  # Outside map.
                break

            if map[map_y, map_x] > 0:
                wall_texture = wall_textures[map[map_y, map_x] - 1]
                tex_h = wall_texture.shape[0]
                tex_w = wall_texture.shape[1]
                if tex_h == 0 or tex_w == 0:
                    skip = 1  # Empty texture?
                break

        if side:
            perp_wall_dist = side_dist_y - delta_dist_y
        else:
            perp_wall_dist = side_dist_x - delta_dist_x
        zbuffer[x] = perp_wall_dist

        if skip or perp_wall_dist == 0:
            continue

        line_height = <int>(h / perp_wall_dist)
        if line_height == 0:
            continue

        initial_y = h // 2 - line_height // 2
        if initial_y < 0:
            draw_start_y = 0
        else:
            draw_start_y = initial_y
        draw_end_y = h // 2 + line_height // 2
        if draw_end_y > h:
            draw_end_y = h

        if side:
            wall_x = pos_x + perp_wall_dist * ray_dir_x
        else:
            wall_x = pos_y + perp_wall_dist * ray_dir_y
        wall_x -= floor(wall_x)

        tex_x = <int>(wall_x * <double>tex_w)
        if side == 0 and ray_dir_x > 0 or side == 1 and ray_dir_y < 0:
            tex_x = tex_w - tex_x - 1

        step = <double>tex_h / line_height
        tex_pos = (draw_start_y - initial_y) * step
        for y in range(draw_start_y, draw_end_y):
            tex_y = <int>tex_pos
            if tex_y < 0 or tex_y > tex_h:
                continue

            tex_pos += step
            wall_value = shade_wall(
                wall_texture[tex_y, tex_x], perp_wall_dist + 2.0 * side
            )
            canvas[y, x].char_ = ascii_map[wall_value]

    cdef:
        size_t nsprites, i
        Sprite *sprites
        Sprite *sprite

    nsprites = sprite_indexes.shape[0]
    sprites = <Sprite*>malloc(nsprites * sizeof(Sprite))
    for i in range(nsprites):
        sprite = &sprites[i]
        sprite.y = sprite_positions[i, 0]
        sprite.x = sprite_positions[i, 1]
        sprite.texture_idx = sprite_indexes[i]
        sprite.distance = (
            (pos_y - sprite.y) * (pos_y - sprite.y)
            + (pos_x - sprite.x) * (pos_x - sprite.x)
        )
    qsort(sprites, nsprites, sizeof(Sprite), &sprite_cmp)

    cdef:
        double inv_det = 1.0 / (plane_x * dir_y - plane_y * dir_x)
        double sprite_y, sprite_x
        double trans_y, trans_x, scale_h, scale_w
        int sprite_screen_x, sprite_h, sprite_w
        int initial_x, draw_start_x, draw_end_x
        Cell[:, ::1] sprite_texture

    for i in range(nsprites):
        sprite_y = sprites[i].y - pos_y
        sprite_x = sprites[i].x - pos_x
        trans_y = inv_det * (plane_x * sprite_y - plane_y * sprite_x)
        if trans_y <= 0:
            # Behind the camera.
            continue

        trans_x = inv_det * (dir_y * sprite_x - dir_x * sprite_y)
        sprite_screen_x = <int>((w / 2) * (1 + trans_x / trans_y))

        sprite_h = <int>(h / trans_y)
        if sprite_h == 0:
            continue
        sprite_w = <int>((w / 2) / trans_y)
        if sprite_w == 0:
            continue

        initial_y = h // 2 - sprite_h // 2
        if initial_y < 0:
            draw_start_y = 0
        else:
            draw_start_y = initial_y
        draw_end_y = h // 2 + sprite_h // 2
        if draw_end_y > h:
            draw_end_y = h

        initial_x = sprite_screen_x - sprite_w // 2
        if initial_x < 0:
            draw_start_x = 0
        else:
            draw_start_x = initial_x
        draw_end_x = sprite_screen_x + sprite_w // 2
        if draw_end_x > w:
            draw_end_x = w

        sprite_texture = sprite_textures[sprites[i].texture_idx]
        tex_h = sprite_texture.shape[0]
        tex_w = sprite_texture.shape[1]

        scale_h = tex_h / sprite_h
        scale_w = tex_w / sprite_w

        for x in range(draw_start_x, draw_end_x):
            if trans_y > zbuffer[x]:
                # Sprite behind a wall.
                continue

            tex_x = <int>((x - initial_x) * scale_w)
            if tex_x < 0 or tex_x >= tex_w:
                continue

            for y in range(draw_start_y, draw_end_y):
                tex_y = <int>((y - initial_y) * scale_h)
                if tex_y < 0 or tex_y >= tex_h:
                    continue
                if sprite_texture[tex_y, tex_x].char_ == u"0":
                    continue
                canvas[y, x] = sprite_texture[tex_y, tex_x]

    free(zbuffer)
    free(sprites)
