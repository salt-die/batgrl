from math import cos, sin, pi, tau

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
    return (1 - p) * a + p * b

def linear(p):
    return p

def in_quad(p):
    return p**2

def out_quad(p):
    return -p * (p - 2)

def in_out_quad(p):
    p *= 2
    if p < 1:
        return p**2 / 2

    p -= 1
    return (1 - p * (p - 2)) / 2

def in_cubic(p):
    return p**3

def out_cubic(p):
    p -= 1
    return p**3 + 1

def in_out_cubic(p):
    p *= 2
    if p < 1:
        return p**3 / 2

    p -= 2
    return (p**3 + 2) / 2

def in_quart(p):
    return p**4

def out_quart(p):
    p -= 1
    return 1 - p**4

def in_out_quart(p):
    p *= 2
    if p < 1:
        return p**4 / 2

    p -= 2
    return (2 - p**4) / 2

def in_quint(p):
    return p**5

def out_quint(p):
    p -= 1
    return p**5 + 1

def in_out_quint(p):
    p *= 2
    if p < 1:
        return p**5 / 2

    p -= 2
    return (p**5 + 2) / 2

def in_sine(p):
    return -cos(p * (pi / 2)) + 1

def out_sine(p):
    return sin(p * (pi / 2))

def in_out_sine(p):
    return (1 - cos(pi * p)) / 2

def in_exp(p):
    if p == 0:
        return 0

    return 2**(10 * (p - 1))

def out_exp(p):
    if p == 1:
        return 1

    return 1 - 2**(-10 * p)

def in_out_exp(p):
    if p == 0:
        return 0

    if p == 1:
        return 1

    p *= 2

    if p < 1:
        return 2**(10 * (p - 1)) / 2

    p -= 1
    return (2 - 2**(-10 * p)) / 2

def in_circ(p):
    return 1 - (1 - p**2)**.5

def out_circ(p):
    p -= 1
    return (1 - p**2)**.5

def in_out_circ(p):
    p *= 2
    if p < 1:
        return -((1 - p**2)**.5 - 1) / 2

    p -= 2
    return ((1 - p**2)**.5 + 1) / 2

def in_elastic(p):
    S = .3

    if p == 1:
        return p

    p -= 1
    return 2**(10 * p) * -sin((p - S / 4) * tau / S)

def out_elastic(p):
    S = .3

    if p == 1:
        return 1

    return 2**(-10 * p) * sin((p - S / 4) * tau / S) + 1

def in_out_elastic(p):
    T = .415

    if p == 1:
        return 1

    p *= 2
    p -= 1
    if p < 0:
        return 2**(10 * p) * -sin((q - T / 4) * tau / T) / 2

    return 2**(-10 * p) * sin((q - T / 4) * tau / T) / 2 + 1

def in_back(p):
    S = 1.70158
    return p**2 * ((S + 1) * p - S)

def out_back(p):
    S = 1.70158
    p -= 1
    return p**2 * ((S + 1) * p + S) + 1

def in_out_back(p):
    S = 2.5949095
    p *= 2
    if p < 1:
        return (p**2 * ((S + 1) * p - S)) / 2

    p -= 2
    return (p**2 * ((S + 1) * p + S) + 2) / 2

def out_bounce(p):
    S = 7.5625
    T = 2.75

    if p < 1 / T:
        return S * p**2

    if p < 2 / T:
        p -= 1.5 / T
        return S * p**2 + .75

    if p < 2.5 / T:
        p -= 2.25 / T
        return S * p**2 + .9375

    p -= 2.625 / T
    return S * p**2 + .984375

def in_bounce(p):
    return 1 - out_bounce(1 - p)

def in_out_bounce(p):
    p *= 2
    if p < 1:
        return in_bounce(p) / 2

    return (out_bounce(p - 1) + 1) / 2
