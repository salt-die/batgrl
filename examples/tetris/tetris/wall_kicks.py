"""
Wall kick data for all tetrominos.

When a tetromino rotates, wall kicks will be attempted until the tetromino
no longer collides with the stack or grid boundaries. If all wall kicks fail,
the tetromino will not rotate.

Notes
-----
The dictionary keys are (current_orientation, target_orientation) where the
orientations are UP, RIGHT, DOWN, LEFT for 0, 1, 2, 3 respectively.

The values are tuples of positional offsets in (dy, dx) format with
positive dy moving down and positive dx moving right.

See Also
--------
https://tetris.wiki/Super_Rotation_System#Wall_Kicks
"""

JLSTZ_WALL_KICKS = {
    # Clockwise rotations
    (0, 1): (( 0,  0), ( 0, -1), (-1, -1), ( 2,  0), ( 2, -1)),
    (1, 2): (( 0,  0), ( 0,  1), ( 1,  1), (-2,  0), (-2,  1)),
    (2, 3): (( 0,  0), ( 0,  1), (-1,  1), ( 2,  0), ( 2,  1)),
    (3, 0): (( 0,  0), ( 0, -1), ( 1, -1), (-2,  0), (-2, -1)),

    # Counter-clockwise rotations
    (1, 0): (( 0,  0), ( 0,  1), ( 1,  1), (-2,  0), (-2,  1)),
    (2, 1): (( 0,  0), ( 0, -1), (-1, -1), ( 2,  0), ( 2, -1)),
    (3, 2): (( 0,  0), ( 0, -1), ( 1, -1), (-2,  0), (-2, -1)),
    (0, 3): (( 0,  0), ( 0,  1), (-1,  1), ( 2,  0), ( 2,  1)),
}

I_WALL_KICKS = {
    # Clockwise rotations
    (0, 1): (( 0,  0), ( 0, -2), ( 0,  1), ( 1, -2), (-2,  1)),
    (1, 2): (( 0,  0), ( 0, -1), ( 0,  2), (-2, -1), ( 1,  2)),
    (2, 3): (( 0,  0), ( 0,  2), ( 0, -1), (-1,  2), ( 2, -1)),
    (3, 0): (( 0,  0), ( 0,  1), ( 0, -2), ( 2,  1), (-1, -2)),

    # Counter-clockwise rotations
    (1, 0): (( 0,  0), ( 0,  2), ( 0, -1), (-1,  2), ( 2, -1)),
    (2, 1): (( 0,  0), ( 0,  1), ( 0, -2), ( 2,  1), (-1, -2)),
    (3, 2): (( 0,  0), ( 0, -2), ( 0,  1), ( 1, -2), (-2,  1)),
    (0, 3): (( 0,  0), ( 0, -1), ( 0,  2), (-2, -1), ( 1,  2)),
}

# Alternative wall kicks for I pieces used in ARIKA Tetris games
ARIKA_I_WALL_KICKS = {
    # Clockwise rotations
    (0, 1): (( 0,  0), ( 0, -2), ( 0,  1), (-2,  1), ( 1, -2)),
    (1, 2): (( 0,  0), ( 0, -1), ( 0,  2), (-2, -1), ( 1,  2)),
    (2, 3): (( 0,  0), ( 0,  2), ( 0, -1), (-1,  2), ( 1, -1)),
    (3, 0): (( 0,  0), ( 0, -2), ( 0,  1), (-1, -2), ( 2,  1)),

    # Counter-clockwise rotations
    (1, 0): (( 0,  0), ( 0,  2), ( 0, -1), (-1,  2), ( 2, -1)),
    (2, 1): (( 0,  0), ( 0,  2), ( 0,  1), (-1, -2), ( 1,  1)),
    (3, 2): (( 0,  0), ( 0,  1), ( 0, -2), (-2,  1), ( 1, -2)),
    (0, 3): (( 0,  0), ( 0,  2), ( 0, -1), (-2, -1), ( 1,  2)),
}

O_WALL_KICKS = {
    (0, 1): (( 0,  0), ),
    (1, 2): (( 0,  0), ),
    (2, 3): (( 0,  0), ),
    (3, 0): (( 0,  0), ),

    (1, 0): (( 0,  0), ),
    (2, 1): (( 0,  0), ),
    (3, 2): (( 0,  0), ),
    (0, 3): (( 0,  0), ),
}
