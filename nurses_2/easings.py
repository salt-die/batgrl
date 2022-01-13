"""
Easing functions.
"""
from math import cos, sin, pi

__all__ = (
    "lerp",
    "linear",
    "in_quad",
    "out_quad",
    "in_out_quad",
    "in_cubic",
    "out_cubic",
    "in_out_cubic",
    "in_quart",
    "out_quart",
    "in_out_quart",
    "in_quint",
    "out_quint",
    "in_out_quint",
    "in_sine",
    "out_sine",
    "in_out_sine",
    "in_exp",
    "out_exp",
    "in_out_exp",
    "in_circ",
    "out_circ",
    "in_out_circ",
    "in_elastic",
    "out_elastic",
    "in_out_elastic",
    "in_back",
    "out_back",
    "in_out_back",
    "in_bounce",
    "out_bounce",
    "in_out_bounce",
)

def lerp(a, b, p):
    return (1.0 - p) * a + p * b

def linear(p):
    return p

def in_quad(p):
    return p**2.0

def out_quad(p):
    return -p * (p - 2.0)

def in_out_quad(p):
    if p < .5:
        return 2.0 * p**2.0

    return -2.0 * p**2.0 + 4.0 * p - 1.0

def in_cubic(p):
    return p**3.0

def out_cubic(p):
    return (p - 1.0)**3.0 + 1.0

def in_out_cubic(p):
    if p < .5:
        return 4.0 * p**3.0

    return .5 * (2.0 * p - 2.0)**3.0 + 1.0

def in_quart(p):
    return p**4.0

def out_quart(p):
    return 1.0 - (p - 1.0)**4.0

def in_out_quart(p):
    if p < .5:
        return 8.0 * p**4.0

    return -8.0 * (p - 1.0)**4.0 + 1.0

def in_quint(p):
    return p**5.0

def out_quint(p):
    return (p - 1.0)**5.0 + 1.0

def in_out_quint(p):
    if p < .5:
        return 16.0 * p**5.0

    return .5 * (2.0 * p - 2.0)**5.0 + 1.0

def in_sine(p):
    return sin((p - 1.0) * pi * .5) + 1.0

def out_sine(p):
    return sin(p * pi * .5)

def in_out_sine(p):
    return .5 * (1.0 - cos(p * pi))

def in_exp(p):
    if p == 0.0:
        return 0.0

    return 2.0**(10.0 * (p - 1.0))

def out_exp(p):
    if p == 1.0:
        return 1.0

    return 1.0 - 2.0**(-10.0 * p)

def in_out_exp(p):
    if p == 0.0:
        return 0.0

    if p == 1.0:
        return 1.0

    if p < .5:
        return .5 * 2.0**(20.0 * p - 10.0)

    return -.5 * 2.0**(-20.0 * p + 10.0) + 1.0

def in_circ(p):
    return 1.0 - (1.0 - p**2.0)**.5

def out_circ(p):
    p -= 1.0
    return (1.0 - p**2.0)**.5

def in_out_circ(p):
    p *= 2.0
    if p < 1.0:
        return -.5 * (1.0 - p**2.0)**.5 + .5

    p -= 2.0
    return .5 * (1.0 - p**2.0)**.5 + .5

def in_elastic(p):
    return sin(6.5 * pi * p) * 2.0**(10.0 * (p - 1.0))

def out_elastic(p):
    return sin(-6.5 * pi * (p + 1.0)) * 2.0**(-10.0 * p) + 1.0

def in_out_elastic(p):
    if p < .5:
        return .5 * sin(13.0 * pi * p) * 2.0**(20.0 * p - 10.0)

    return .5 * (sin(-13.0 * pi * p) * 2.0**(-20.0 * p + 10.0) + 2.0)

def in_back(p):
    return p**2.0 * (2.70158 * p - 1.70158)

def out_back(p):
    p -= 1.0
    return p**2.0 * (2.70158 * p + 1.70158) + 1.0

def in_out_back(p):
    p *= 2.0
    if p < 1.0:
        return .5 * (p**2.0 * (3.5949095 * p - 2.5949095))

    p -= 2.0
    return .5 * (p**2.0 * (3.5949095 * p + 2.5949095) + 2.0)

def out_bounce(p):
    if p < 4.0 / 11.0:
        return 121.0 * p**2.0 / 16.0

    if p < 8.0 / 11.0:
        return 363.0 / 40.0 * p**2.0 - 99.0 / 10.0 * p + 17.0 / 5.0

    if p < 9.0 / 10.0:
        return 4356.0 / 361.0 * p**2.0 - 35442.0 / 1805.0 * p + 16061.0 / 1805.0

    return 54.0 / 5.0 * p**2.0 - 513.0 / 25.0 * p + 268.0 / 25.0

def in_bounce(p):
    return 1.0 - out_bounce(1.0 - p)

def in_out_bounce(p):
    if p < .5:
        return .5 * in_bounce(2.0 * p)

    return .5 * out_bounce(2.0 * p - 1.0) + .5
